#![warn(clippy::perf, clippy::pedantic)]

mod assign;

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyInt, PySequence, PyString, PyTuple};

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
    use super::*;

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

#[pyfunction]
#[pyo3(text_signature = "(target, spec, *, default=None)")]
fn gloom(
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
    m.add_function(wrap_pyfunction!(gloom, m)?)?;
    m.add_function(wrap_pyfunction!(assign::assign, m)?)?;
    Ok(())
}
