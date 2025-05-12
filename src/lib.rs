#![warn(clippy::perf, clippy::pedantic)]

use std::io::Read;
use std::str::from_utf8_unchecked;

use pyo3::types::{PyAny, PyDict, PyInt, PyMapping, PySequence, PyString, PyTuple};
use pyo3::{BoundObject, prelude::*};

mod bytesplit;
use bytesplit::ByteSplit;

#[pyfunction]
#[pyo3(text_signature = "(obj, path, val)")]
fn assign<'py>(
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

fn get_single_digit_index(s: &str) -> Option<usize> {
    if s.len() != 1 {
        return None;
    }

    let b = s.as_bytes()[0];

    if !b.is_ascii_digit() {
        return None;
    }

    Some(b as usize - b'0' as usize)
}

mod tests {
    use std::any::Any;

    use super::*;
    use pyo3::types::PyModule;

    #[test]
    fn test_get_single_digit_index() {
        for i in '0'..='9' {
            let s = i.to_string();
            assert_eq!(get_single_digit_index(&s), Some(i as usize - '0' as usize));
        }
        assert_eq!(get_single_digit_index("a"), None);
    }

    #[test]
    fn test_python_digit_same_ptr() {
        for i in 0..100 {
            let mut a: Option<Py<PyInt>> = None;
            let mut b: Option<Py<PyInt>> = None;

            Python::with_gil(|py| {
                a = Some(PyInt::new(py, i).unbind());
            });

            Python::with_gil(|py| {
                b = Some(PyInt::new(py, i).unbind());
            });

            assert_eq!(a.unwrap().as_ptr(), b.unwrap().as_ptr());
        }
    }
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

        part.eq(0);

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

#[pyfunction]
#[pyo3(text_signature = "(target, spec, *, default=None)")]
fn gloom_compat(
    target: Bound<'_, PyAny>,
    spec: Bound<'_, PyAny>,
    default: PyObject,
) -> PyResult<PyObject> {
    if target.is_none() {
        return Ok(default);
    }

    if let Ok(spec_tuple) = spec.downcast::<PyTuple>() {
        return gloom_tuple(target, spec_tuple, default);
    } else if let Ok(spec_str) = spec.downcast::<PyString>() {
        return gloom_str(target, spec_str.to_str()?, default);
    }

    return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
        "spec must be a string or a tuple",
    ));
}

fn gloom_str(target: Bound<'_, PyAny>, spec: &str, default: PyObject) -> PyResult<PyObject> {
    let mut location = target;

    // for part in spec.byte_split(b'.') {
    // for part in spec.split(|b| b == &b'.') {
    // let part = from_utf8_unchecked(part);
    for part in spec.split('.') {
        if let Some(index) = get_single_digit_index(part) {
            if let Ok(item) = location.get_item(index) {
                location = item;
                continue;
            }
        }

        let part_isdigit = part.chars().all(|c| c.is_ascii_digit());
        let part_pystr = PyString::new(location.py(), part);

        if let Some(index) = get_single_digit_index(part) {
            if let Ok(item) = location.get_item(index) {
                location = item;
                continue;
            }
        }

        if let Ok(mapping) = location.downcast::<PyDict>() {
            if let Ok(Some(item)) = mapping.get_item(&part_pystr) {
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

fn gloom_tuple(
    target: Bound<'_, PyAny>,
    spec: &Bound<'_, PyTuple>,
    default: PyObject,
) -> PyResult<PyObject> {
    let mut location = target;

    for part in spec {
        if let Ok(mapping) = location.downcast::<PyDict>() {
            if let Ok(Some(item)) = mapping.get_item(&part) {
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

#[pymodule]
fn gloomy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // m.add_function(wrap_pyfunction!(gloom, m)?)?;
    // m.add_function(wrap_pyfunction!(gloom_path, m)?)?;
    // m.add_function(wrap_pyfunction!(gloom_assign, m)?)?;
    // m.add_function(wrap_pyfunction!(gloom_assign_path, m)?)?;
    m.add_function(wrap_pyfunction!(gloom_compat, m)?)?;
    m.add_function(wrap_pyfunction!(assign, m)?)?;
    Ok(())
}
