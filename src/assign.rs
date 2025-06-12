#![warn(clippy::perf, clippy::pedantic)]

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyInt, PySequence, PyString, PyTuple};

#[pyfunction]
#[pyo3(text_signature = "(obj, path, val)")]
pub fn assign<'py>(
    obj: Bound<'py, PyAny>,
    path: &Bound<'py, PyAny>,
    val: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    if let Ok(path_tuple) = path.downcast::<PyTuple>() {
        return assign_path_tuple(obj, path_tuple, val);
    } else if let Ok(path_str) = path.downcast::<PyString>() {
        return assign_path_str(obj, path_str.to_str()?, val);
    }

    return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
        "path must be a string or a tuple",
    ));
}

fn assign_path_str<'py>(
    obj: Bound<'py, PyAny>,
    path: &str,
    val: &Bound<'_, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
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

        if let Ok(mapping) = location.downcast::<PyDict>() {
            if i == path_len - 1 {
                mapping.set_item(&part_pystr, val)?;
                return Ok(obj);
            }

            if let Ok(Some(item)) = mapping.get_item(&part_pystr) {
                location = item;
                continue;
            }
        } else if part_isdigit {
            if i == path_len - 1 {
                location.set_item(part, val)?;
                return Ok(obj);
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
                return Ok(obj);
            }

            if let Ok(Some(attr)) = location.getattr_opt(&part_pystr) {
                location = attr;
                continue;
            }
        }
    }

    Ok(obj)
}

fn assign_path_tuple<'py>(
    obj: Bound<'py, PyAny>,
    path: &Bound<'py, PyTuple>,
    val: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    if obj.is_none() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Cannot assign to None",
        ));
    }

    let mut location = obj.clone();
    let path = path.iter();
    let path_len = path.len();

    for (i, part) in path.enumerate() {
        let is_last = i == path_len - 1;

        if let Ok(mapping) = location.downcast::<PyDict>() {
            if is_last {
                mapping.set_item(part, val)?;
                return Ok(obj);
            }

            if let Ok(Some(item)) = mapping.get_item(&part) {
                location = item;
                continue;
            }
        } else if let Ok(part_pystr) = part.downcast::<PyString>() {
            if is_last {
                location.setattr(&part_pystr, val)?;
                return Ok(obj);
            }

            if let Ok(attr) = location.getattr(&part_pystr) {
                location = attr;
                continue;
            }
        } else if let Ok(part_int) = part.downcast::<PyInt>() {
            if is_last {
                location.set_item(&part_int, val)?;
                return Ok(obj);
            }

            if let Ok(item) = location.get_item(&part_int) {
                location = item;
                continue;
            }
        }
    }

    Ok(obj)
}
