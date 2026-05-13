from __future__ import annotations

import base64
import hashlib
import io
from typing import Any, Dict, List, Union

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms
from transformers import AutoModel, AutoTokenizer

from src.runtime import get_settings


class ParameterExtractor(nn.Module):
    """
    Multi-modal parameter extractor with strict offline fallbacks.
    If bundled local models are absent, it falls back to deterministic hashing
    and lightweight visual statistics so the desktop app can still learn.
    """

    def __init__(self, output_dim: int = 256):
        super().__init__()
        self.output_dim = output_dim
        self.settings = get_settings()
        self.vision_transforms = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        self.vision_extractor = None
        self.vision_proj = None
        self.tokenizer = None
        self.text_model = None
        self.text_proj = None
        self.fusion = nn.Linear(output_dim * 2, output_dim)
        self._init_vision_stack()
        self._init_text_stack()

    def _init_vision_stack(self) -> None:
        try:
            weights = models.ResNet18_Weights.DEFAULT if self.settings.enable_model_downloads and not self.settings.offline_strict else None
            resnet = models.resnet18(weights=weights)
            self.vision_extractor = nn.Sequential(*list(resnet.children())[:-1])
            self.vision_proj = nn.Linear(512, self.output_dim)
        except Exception as exc:
            print(f"Vision extractor offline fallback enabled: {exc}")

    def _init_text_stack(self) -> None:
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        local_model_dir = self.settings.model_dir / "minilm"
        model_source = str(local_model_dir) if local_model_dir.exists() else None
        if model_source is None and not (self.settings.offline_strict or not self.settings.enable_model_downloads):
            model_source = model_name
        if model_source is None:
            print("Text extractor offline fallback enabled: no bundled embedding model found.")
            return
        kwargs = {}
        if self.settings.offline_strict or not self.settings.enable_model_downloads:
            kwargs["local_files_only"] = True
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_source, **kwargs)
            self.text_model = AutoModel.from_pretrained(model_source, **kwargs)
            self.text_proj = nn.Linear(384, self.output_dim)
        except Exception as exc:
            print(f"Text extractor offline fallback enabled: {exc}")

    def _normalize(self, tensor: torch.Tensor) -> np.ndarray:
        tensor = nn.functional.normalize(tensor, p=2, dim=0)
        return tensor.detach().cpu().numpy()

    def _fallback_text_embedding(self, text: str) -> torch.Tensor:
        vector = np.zeros(self.output_dim, dtype=np.float32)
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.output_dim
            vector[index] += 1.0
        if not vector.any():
            vector[0] = 1.0
        return torch.from_numpy(vector)

    def _fallback_visual_embedding(self, image: Image.Image) -> torch.Tensor:
        image = image.resize((32, 32)).convert("RGB")
        arr = np.asarray(image, dtype=np.float32) / 255.0
        hist = []
        for channel in range(3):
            counts, _ = np.histogram(arr[:, :, channel], bins=self.output_dim // 3, range=(0.0, 1.0))
            hist.extend(counts.tolist())
        vector = np.array(hist[: self.output_dim], dtype=np.float32)
        if len(vector) < self.output_dim:
            vector = np.pad(vector, (0, self.output_dim - len(vector)))
        return torch.from_numpy(vector)

    def extract_visual(self, image_data: Union[bytes, str]) -> torch.Tensor:
        if isinstance(image_data, str):
            try:
                if "," in image_data:
                    image_data = image_data.split(",", 1)[1]
                image_bytes = base64.b64decode(image_data)
            except Exception:
                image_bytes = image_data.encode("utf-8")
        else:
            image_bytes = image_data

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224))

        if self.vision_extractor is None or self.vision_proj is None:
            return self._fallback_visual_embedding(image)

        tensor = self.vision_transforms(image).unsqueeze(0)
        with torch.no_grad():
            features = self.vision_extractor(tensor)
            features = features.view(features.size(0), -1)
            parameters = self.vision_proj(features)
        return parameters.squeeze(0)

    def extract_text(self, text: str) -> torch.Tensor:
        if self.tokenizer is None or self.text_model is None or self.text_proj is None:
            return self._fallback_text_embedding(text)

        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.text_model(**inputs)
            attention_mask = inputs["attention_mask"]
            token_embeddings = outputs.last_hidden_state
            expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * expanded, 1)
            sum_mask = torch.clamp(expanded.sum(1), min=1e-9)
            embeddings = sum_embeddings / sum_mask
            parameters = self.text_proj(embeddings)
        return parameters.squeeze(0)

    def extract(self, data_type: str, raw_data: Any) -> np.ndarray:
        if data_type == "text":
            params = self.extract_text(str(raw_data))
        elif data_type in {"visual", "visual_frame"}:
            params = self.extract_visual(raw_data)
        else:
            params = self._fallback_text_embedding(str(raw_data))
        return self._normalize(params)


class ContinualRegressionEngine:
    """
    Continuous regression engine with novelty-weighted updates.
    """

    def __init__(self, learning_rate: float = 0.05, memory_preservation: float = 0.8):
        self.learning_rate = learning_rate
        self.memory_preservation = memory_preservation

    def calculate_surprise(self, new_tensor: torch.Tensor, existing_tensor: torch.Tensor) -> float:
        cosine_sim = nn.functional.cosine_similarity(new_tensor.unsqueeze(0), existing_tensor.unsqueeze(0))
        return 1.0 - cosine_sim.item()

    def regress(
        self,
        new_parameters: np.ndarray,
        existing_parameters: np.ndarray,
        confidence: float = 1.0,
        state_modifier: float = 1.0,
        entanglement_modifier: np.ndarray = None,
    ) -> tuple[np.ndarray, float]:
        new_tensor = torch.from_numpy(new_parameters)
        existing_tensor = torch.from_numpy(existing_parameters)
        surprise_score = self.calculate_surprise(new_tensor, existing_tensor)
        deviation = new_tensor - existing_tensor
        attention_multiplier = 1.0 + surprise_score
        adaptive_lr = (
            self.learning_rate
            * confidence
            * attention_multiplier
            * state_modifier
            * (1.0 - self.memory_preservation)
        )
        updated_tensor = existing_tensor + (adaptive_lr * deviation)
        if entanglement_modifier is not None:
            updated_tensor = updated_tensor + torch.from_numpy(entanglement_modifier)
        updated_tensor = nn.functional.normalize(updated_tensor, p=2, dim=0)
        return updated_tensor.numpy(), surprise_score
