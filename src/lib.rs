use pyo3::create_exception;
use pyo3::exceptions::{PyException, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::path::PathBuf;

create_exception!(oxipng, PngError, PyException);

fn parse_options(kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<oxi::Options> {
    let mut level = 2_u8;

    if let Some(dict) = kwargs {
        for (key, value) in dict.iter() {
            let key: String = key.extract()?;

            match key.as_str() {
                "level" => {
                    let parsed: i64 = value.extract().map_err(|_| {
                        PyValueError::new_err("level must be an integer from 0 to 6")
                    })?;

                    if !(0..=6).contains(&parsed) {
                        return Err(PyValueError::new_err(
                            "level must be between 0 and 6 inclusive",
                        ));
                    }

                    level = parsed as u8;
                }
                _ => {
                    return Err(PyTypeError::new_err(format!("unsupported option: {key}")));
                }
            }
        }
    }

    Ok(oxi::Options::from_preset(level))
}

fn map_png_error(error: oxi::PngError) -> PyErr {
    PngError::new_err(error.to_string())
}

#[pyfunction]
#[pyo3(signature = (input, output=None, **kwargs))]
#[pyo3(text_signature = "(input, output=None, *, level=2)")]
fn optimize(
    input: PathBuf,
    output: Option<PathBuf>,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<()> {
    let input_file = oxi::InFile::Path(input);
    let output_file = match output {
        Some(path) => oxi::OutFile::from_path(path),
        None => oxi::OutFile::Path {
            path: None,
            preserve_attrs: false,
        },
    };

    oxi::optimize(&input_file, &output_file, &parse_options(kwargs)?).map_err(map_png_error)?;
    Ok(())
}

#[pymodule]
fn _oxipng(py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("PngError", py.get_type::<PngError>())?;
    module.add_function(wrap_pyfunction!(optimize, module)?)?;
    Ok(())
}
