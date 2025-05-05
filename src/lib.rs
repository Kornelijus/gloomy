#![warn(clippy::perf, clippy::pedantic)]

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyMapping, PySequence, PyString};

#[pyfunction]
#[pyo3(text_signature = "(target, spec, *, default=None)")]
fn gloom_rusty(target: Bound<'_, PyAny>, spec: &str, default: PyObject) -> PyResult<PyObject> {
    if target.is_none() {
        return Ok(default);
    }

    let mut location = target;

    for part in spec.split('.') {
        let part_isdigit = part.chars().all(|c| c.is_ascii_digit());
        let part_pystr = PyString::new(location.py(), part);

        if let Ok(mapping) = location.downcast::<PyMapping>() {
            if let Ok(item) = mapping.get_item(&part_pystr) {
                location = item;
                continue;
            }
        } else if part_isdigit {
            if let Ok(sequence) = location.downcast::<PySequence>() {
                if let Ok(item) = sequence.get_item(part.parse()?) {
                    location = item;
                    continue;
                }
            }
        } else {
            if let Ok(Some(attr)) = location.getattr_opt(&part_pystr) {
                location = attr;
                continue;
            }
        }

        return Ok(default);
    }

    Ok(location.into())
}

#[pymodule]
fn gloomyrs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    println!("AAA");
    m.add_function(wrap_pyfunction!(gloom_rusty, m)?)?;

    Ok(())
}
