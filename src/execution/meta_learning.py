import os
import importlib.util
from typing import Callable, Dict, Any
from src.learning.reasoning import CognitiveReasoningEngine

class MetaLearningEngine:
    """
    The Evolution Layer: "AI by AI".
    Allows the twin to generate its own Python execution plugins at runtime,
    save them to disk, dynamically import them, and add them to its own 
    execution router when it realizes it lacks a specific capability.
    """
    def __init__(self, reasoning: CognitiveReasoningEngine):
        self.reasoning = reasoning
        self.plugin_dir = "src/execution/plugins"
        os.makedirs(self.plugin_dir, exist_ok=True)
        self.dynamic_tools: Dict[str, Callable] = {}
        self._load_existing_plugins()

    def _load_existing_plugins(self):
        """Loads previously generated meta-tools from disk."""
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                tool_name = filename[:-3]
                self._import_and_register(tool_name, os.path.join(self.plugin_dir, filename))

    def _import_and_register(self, tool_name: str, filepath: str):
        try:
            spec = importlib.util.spec_from_file_location(tool_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'execute'):
                self.dynamic_tools[f"dynamic:{tool_name}"] = module.execute
                print(f"Meta-Learning: Successfully loaded evolved tool -> '{tool_name}'")
        except Exception as e:
            print(f"Meta-Learning: Failed to load plugin {tool_name}: {e}")

    def evolve_new_tool(self, capability_request: str) -> bool:
        """
        Generates Python code for a new tool based on a capability gap, 
        saves it, and loads it.
        """
        if not self.reasoning.client:
            print("Meta-Learning offline. Cannot evolve.")
            return False

        print(f"Evolution triggered. Attempting to code new tool for: '{capability_request}'")

        prompt = (
            f"You are the meta-learning core of a digital twin. You need a new capability: '{capability_request}'.\n"
            "Write a Python script that implements this. It MUST contain a single function named `execute(args: str) -> str`.\n"
            "Do not include markdown blocks, just the pure Python code. Make it safe (no arbitrary OS destruction)."
        )

        try:
            code = self.reasoning._generate_generic(
                system_prompt="You are a meta-learning code generator.",
                user_prompt=prompt,
                max_tokens=300,
                temperature=0.1
            )
            
            if not code: return False
            
            # Very basic markdown strip if the model disobeys
            if code.startswith("```python"):
                code = code.split("```python")[1].split("```")[0].strip()

            tool_name = f"evolved_{int(os.times()[4])}"
            filepath = os.path.join(self.plugin_dir, f"{tool_name}.py")
            
            with open(filepath, "w") as f:
                f.write(code)
                
            self._import_and_register(tool_name, filepath)
            return True

        except Exception as e:
            print(f"Meta-Learning evolution failed: {e}")
            return False

    def get_dynamic_tools(self) -> Dict[str, Callable]:
        return self.dynamic_tools
