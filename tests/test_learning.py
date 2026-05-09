import pytest
import numpy as np
from src.learning.engine import ContinualRegressionEngine

def test_regression_engine():
    engine = ContinualRegressionEngine(learning_rate=0.1, memory_preservation=0.5)
    
    # 256-dim vectors
    existing_mem = np.ones(256, dtype=np.float32)
    # Normalize existing_mem
    existing_mem = existing_mem / np.linalg.norm(existing_mem)
    
    new_knowledge = np.zeros(256, dtype=np.float32)
    new_knowledge[0] = 1.0 # One-hot
    
    # Regress now returns a tuple (updated_mem, surprise_score)
    updated_mem, surprise = engine.regress(new_knowledge, existing_mem)
    
    assert updated_mem.shape == (256,)
    assert isinstance(surprise, float)
    
    # Verify the vector shifted towards new_knowledge
    assert updated_mem[0] > updated_mem[1]
    
    # Verify it remains normalized
    norm = np.linalg.norm(updated_mem)
    assert np.isclose(norm, 1.0, atol=1e-5)
