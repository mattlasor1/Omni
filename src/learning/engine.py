import torch
import torch.nn as nn
import numpy as np
from torchvision import models, transforms
from transformers import AutoTokenizer, AutoModel
from typing import Any, List, Dict, Union
from PIL import Image
import io
import base64

class ParameterExtractor(nn.Module):
    """
    Advanced multi-modal parameter extractor.
    Uses pre-trained vision models (ResNet) for visual frames
    and transformer models (MiniLM) for textual data.
    Outputs a consistent high-dimensional mathematical parameter vector.
    """
    def __init__(self, output_dim: int = 256):
        super(ParameterExtractor, self).__init__()
        self.output_dim = output_dim
        
        # Vision Model: ResNet18 as a feature extractor
        # Use a lightweight pre-trained model for the framework baseline
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.vision_extractor = nn.Sequential(*list(resnet.children())[:-1]) # Remove classification head
        self.vision_proj = nn.Linear(512, output_dim) # Project resnet 512-dim out to output_dim
        
        self.vision_transforms = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Text Model: HuggingFace all-MiniLM for sentence embeddings
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.text_model = AutoModel.from_pretrained(model_name)
        self.text_proj = nn.Linear(384, output_dim) # MiniLM output is 384-dim
        
        # Optional fusion layer if dealing with multi-modal inputs at once
        self.fusion = nn.Linear(output_dim * 2, output_dim)

    def extract_visual(self, image_data: Union[bytes, str]) -> torch.Tensor:
        """
        Extracts parameters from a visual frame (base64 or bytes).
        """
        if isinstance(image_data, str):
            # Try base64 decoding
            try:
                if "," in image_data: # Handle data URIs
                    image_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(image_data)
            except:
                image_bytes = image_data.encode('utf-8')
        else:
            image_bytes = image_data
            
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception:
            # Fallback to random tensor if parsing fails in prototype
            image = Image.new('RGB', (224, 224))
            
        tensor = self.vision_transforms(image).unsqueeze(0) # Add batch dimension
        
        with torch.no_grad():
            features = self.vision_extractor(tensor)
            features = features.view(features.size(0), -1) # Flatten
            parameters = self.vision_proj(features)
            
        return parameters.squeeze(0)

    def extract_text(self, text: str) -> torch.Tensor:
        """
        Extracts parameters from text.
        """
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.text_model(**inputs)
            # Mean pooling
            attention_mask = inputs['attention_mask']
            token_embeddings = outputs.last_hidden_state
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            embeddings = sum_embeddings / sum_mask
            
            parameters = self.text_proj(embeddings)
            
        return parameters.squeeze(0)

    def extract(self, data_type: str, raw_data: Any) -> np.ndarray:
        """
        Main extraction router.
        """
        if data_type == "text":
            tensor_params = self.extract_text(raw_data)
        elif data_type in ["visual", "visual_frame"]:
            tensor_params = self.extract_visual(raw_data)
        else:
            # Fallback
            tensor_params = torch.rand(self.output_dim)
            
        # L2 Normalize for better cosine similarity in vector DB
        tensor_params = nn.functional.normalize(tensor_params, p=2, dim=0)
        return tensor_params.numpy()


class ContinualRegressionEngine:
    """
    Advanced Continuous Regression engine with Attention/Surprise mapping.
    Implements a simplified Elastic Weight Consolidation (EWC) style merging, 
    ensuring catastrophic forgetting is minimized, while calculating an 'attention' 
    score based on the novelty of the incoming signal.
    """
    def __init__(self, learning_rate: float = 0.05, memory_preservation: float = 0.8):
        self.learning_rate = learning_rate
        self.memory_preservation = memory_preservation

    def calculate_surprise(self, new_tensor: torch.Tensor, existing_tensor: torch.Tensor) -> float:
        """
        Calculates how 'surprising' or novel the new information is by
        measuring the cosine distance between the parameter vectors.
        High distance = High Surprise = Higher Attention weighting.
        """
        cosine_sim = nn.functional.cosine_similarity(new_tensor.unsqueeze(0), existing_tensor.unsqueeze(0))
        distance = 1.0 - cosine_sim.item()
        return distance

    def regress(self, new_parameters: np.ndarray, existing_parameters: np.ndarray, 
                confidence: float = 1.0) -> tuple[np.ndarray, float]:
        """
        Regresses the new knowledge against existing knowledge.
        Uses confidence scores and memory preservation penalties to simulate
        EWC parameter updates.
        
        Args:
            new_parameters: The newly extracted vector.
            existing_parameters: The closest existing memory vector.
            confidence: How strongly the new parameter should overwrite (e.g., source reliability).
        """
        # Convert to tensors for math
        new_tensor = torch.from_numpy(new_parameters)
        existing_tensor = torch.from_numpy(existing_parameters)
        
        # 1. Calculate Attention / Surprise
        surprise_score = self.calculate_surprise(new_tensor, existing_tensor)
        
        # 2. Calculate deviation (loss gradient proxy)
        deviation = new_tensor - existing_tensor
        
        # 3. EWC-style penalty + Attention boost: 
        # We boost the learning rate if the information is highly surprising (novelty focus),
        # while restricting the base update based on memory_preservation to protect old knowledge.
        attention_multiplier = 1.0 + surprise_score 
        adaptive_lr = self.learning_rate * confidence * attention_multiplier * (1.0 - self.memory_preservation)
        
        # Update parameters
        updated_tensor = existing_tensor + (adaptive_lr * deviation)
        
        # Re-normalize
        updated_tensor = nn.functional.normalize(updated_tensor, p=2, dim=0)
        
        return updated_tensor.numpy(), surprise_score
