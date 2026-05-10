use pyo3::prelude::*;
use std::collections::HashSet;

/// Rust implementation of the Thalamic Gate heuristic.
/// Bypasses the Python GIL to provide zero-latency microsecond sensory filtering.
#[pyfunction]
fn fast_thalamic_filter(content: String, internal_arousal: f64, salience_threshold: f64) -> PyResult<bool> {
    // Arousal lowers the barrier to entry
    let dynamic_threshold = salience_threshold * (1.0 - (internal_arousal * 0.5));
    
    // Very fast string entropy calculation in Rust
    let len = content.chars().count();
    if len == 0 {
        return Ok(false);
    }
    
    let mut char_set = HashSet::new();
    for c in content.chars() {
        char_set.insert(c);
    }
    
    let entropy = char_set.len() as f64 / len as f64;
    
    // If string is highly diverse/salient, let it through
    if entropy > dynamic_threshold {
        Ok(true)
    } else {
        Ok(false)
    }
}

/// The PyO3 Module definition
#[pymodule]
fn omnicore(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_thalamic_filter, m)?)?;
    Ok(())
}
