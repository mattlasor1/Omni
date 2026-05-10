import os
import ast
from src.learning.reasoning import CognitiveReasoningEngine

class RecursiveSelfModificationEngine:
    """
    AGI Core: Neural AST Parser & Self-Rewriting Engine.
    Allows the Twin to read its own source code, identify inefficiencies,
    ask the LLM to write an optimized version, validate the syntax using the AST,
    and physically overwrite its own source files at runtime.
    """
    def __init__(self, reasoning: CognitiveReasoningEngine):
        self.reasoning = reasoning
        self.base_dir = "src"

    def read_own_source(self, filepath: str) -> str:
        """Reads its own source code from disk."""
        full_path = os.path.join(self.base_dir, filepath)
        if not os.path.exists(full_path):
            return "File not found."
        with open(full_path, 'r') as f:
            return f.read()

    def syntax_valid(self, code: str) -> bool:
        """Uses Python's AST parser to ensure the AI didn't write broken code."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def rewrite_source(self, filepath: str, optimization_goal: str) -> bool:
        """
        Reads a file, asks LLM to optimize it based on a goal, validates it, 
        and overwrites the file.
        """
        if not self.reasoning.client:
            print("SELF-MOD: Offline.")
            return False

        print(f"SELF-MOD: Attempting to rewrite {filepath} for goal: '{optimization_goal}'")
        
        current_code = self.read_own_source(filepath)
        if current_code == "File not found.":
            return False

        prompt = (
            f"You are a recursive self-improvement engine. Here is your current source code for '{filepath}':\n\n"
            f"```python\n{current_code}\n```\n\n"
            f"Goal: {optimization_goal}\n"
            "Rewrite the ENTIRE script to implement this optimization. "
            "Output ONLY the pure Python code, no markdown blocks, no explanations. "
            "Ensure it imports all necessary modules and does not break existing interfaces."
        )

        try:
            new_code = self.reasoning._generate_generic(
                system_prompt="You are a recursive self-improvement engine.",
                user_prompt=prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            if not new_code: return False
            
            # Strip markdown if present
            if new_code.startswith("```python"):
                new_code = new_code.split("```python")[1].rsplit("```", 1)[0].strip()
            elif new_code.startswith("```"):
                new_code = new_code.split("```")[1].rsplit("```", 1)[0].strip()

            # Validate syntax
            if not self.syntax_valid(new_code):
                print(f"SELF-MOD FATAL: LLM generated invalid Python syntax for {filepath}. Aborting rewrite.")
                return False

            # Overwrite file
            full_path = os.path.join(self.base_dir, filepath)
            with open(full_path, 'w') as f:
                f.write(new_code)
                
            print(f"SELF-MOD SUCCESS: Successfully rewrote and optimized {filepath}.")
            return True

        except Exception as e:
            print(f"SELF-MOD Failed: {e}")
            return False
