#![warn(clippy::perf, clippy::pedantic)]

mod assign;
mod get;

use pyo3::prelude::*;

#[pymodule]
fn gloomy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get::gloom, m)?)?;
    m.add_function(wrap_pyfunction!(assign::assign, m)?)?;
    Ok(())
}
