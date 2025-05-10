#![warn(clippy::perf, clippy::pedantic)]

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyInt, PyMapping, PySequence, PyString, PyTuple};

#[pyfunction]
#[pyo3(text_signature = "(target, spec, *, default=None)")]
fn gloom_path(
    target: Bound<'_, PyAny>,
    spec: Bound<'_, PyTuple>,
    default: PyObject,
) -> PyResult<PyObject> {
    if target.is_none() {
        return Ok(default);
    }

    let mut location = target;

    for part in spec {
        if let Ok(mapping) = location.downcast::<PyMapping>() {
            if let Ok(item) = mapping.get_item(&part) {
                location = item;
                continue;
            }
        } else if let Ok(part_pystr) = part.downcast::<PyString>() {
            if let Ok(attr) = location.getattr(&part_pystr) {
                location = attr;
                continue;
            }
        } else if let Ok(part_int) = part.downcast::<PyInt>() {
            if let Ok(item) = location.get_item(&part_int) {
                location = item;
                continue;
            }
        }

        return Ok(default);
    }

    Ok(location.into())
}

#[pyfunction]
#[pyo3(text_signature = "(obj, path, val)")]
fn gloom_assign<'py>(obj: Bound<'py, PyAny>, path: &str, val: Bound<'_, PyAny>) -> PyResult<()> {
    // ) -> PyResult<Bound<'py, PyAny>> {
    if obj.is_none() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Cannot assign to None",
        ));
    }

    let mut location = obj.clone();
    let path = path.split('.');
    let path_len = path.clone().count();

    for (i, part) in path.enumerate() {
        let part_isdigit = part.chars().all(|c| c.is_ascii_digit());
        let part_pystr = PyString::new(location.py(), part);

        if let Ok(mapping) = location.downcast::<PyMapping>() {
            if i == path_len - 1 {
                mapping.set_item(&part_pystr, val)?;
                // return Ok(obj);
                return Ok(());
            }

            if let Ok(item) = mapping.get_item(&part_pystr) {
                location = item;
                continue;
            }
        } else if part_isdigit {
            if i == path_len - 1 {
                location.set_item(part, val)?;
                // return Ok(obj);
                return Ok(());
            }

            if let Ok(sequence) = location.downcast::<PySequence>() {
                if let Ok(item) = sequence.get_item(part.parse()?) {
                    location = item;
                    continue;
                }
            }
        } else {
            if i == path_len - 1 {
                location.setattr(&part_pystr, val)?;
                // return Ok(obj);
                return Ok(());
            }

            if let Ok(Some(attr)) = location.getattr_opt(&part_pystr) {
                location = attr;
                continue;
            }
        }
    }

    Ok(())
    // Ok(obj)
}

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
fn gloomy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(gloom_rusty, m)?)?;
    m.add_function(wrap_pyfunction!(gloom_path, m)?)?;
    m.add_function(wrap_pyfunction!(gloom_assign, m)?)?;
    Ok(())
}
