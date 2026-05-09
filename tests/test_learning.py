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
    
    updated_mem = engine.regress(new_knowledge, existing_mem)
    
    assert updated_mem.shape == (256,)
    
    # Verify the vector shifted towards new_knowledge
    # Since existing_mem was uniform, and new_knowledge is heavily weighted on index 0,
    # the updated memory should have a higher value at index 0 than index 1.
    assert updated_mem[0] > updated_mem[1]
    
    # Verify it remains normalized
    norm = np.linalg.norm(updated_mem)
    assert np.isclose(norm, 1.0, atol=1e-5)
