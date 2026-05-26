use indexmap::IndexSet;
use pyo3::create_exception;
use pyo3::exceptions::{PyException, PyFileExistsError, PyOSError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyByteArray, PyBytes, PyDict, PyList, PyString, PyTuple};
use std::fs;
use std::path::PathBuf;

create_exception!(oxipng, PngError, PyException);

#[derive(Clone, Copy)]
enum ParseMode {
    File,
    Memory,
}

struct ParsedOptions {
    options: oxi::Options,
    backup: bool,
    preserve_attrs: bool,
}

fn value_as_string(value: &Bound<'_, PyAny>, option: &str) -> PyResult<String> {
    if let Ok(text) = value.downcast::<PyString>() {
        return Ok(text.to_str()?.to_owned());
    }

    if let Ok(enum_value) = value.getattr("value") {
        if let Ok(text) = enum_value.downcast::<PyString>() {
            return Ok(text.to_str()?.to_owned());
        }
    }

    Err(PyValueError::new_err(format!(
        "{option} must be a string or enum value"
    )))
}

fn parse_bool(value: &Bound<'_, PyAny>, option: &str) -> PyResult<bool> {
    if !value.is_instance_of::<PyBool>() {
        return Err(PyTypeError::new_err(format!("{option} must be a bool")));
    }
    value.extract()
}

fn parse_level(value: &Bound<'_, PyAny>) -> PyResult<u8> {
    let parsed: i64 = value
        .extract()
        .map_err(|_| PyValueError::new_err("level must be an integer from 0 to 6"))?;

    if !(0..=6).contains(&parsed) {
        return Err(PyValueError::new_err(
            "level must be between 0 and 6 inclusive",
        ));
    }

    Ok(parsed as u8)
}

fn parse_interlace(value: &Bound<'_, PyAny>) -> PyResult<Option<bool>> {
    match value_as_string(value, "interlace")?.as_str() {
        "keep" => Ok(None),
        "off" | "0" => Ok(Some(false)),
        "on" | "1" => Ok(Some(true)),
        _ => Err(PyValueError::new_err(
            "interlace must be one of: keep, off, on, 0, 1",
        )),
    }
}

fn parse_strip(value: &Bound<'_, PyAny>) -> PyResult<oxi::StripChunks> {
    match value_as_string(value, "strip")?.as_str() {
        "none" => Ok(oxi::StripChunks::None),
        "safe" => Ok(oxi::StripChunks::Safe),
        "all" => Ok(oxi::StripChunks::All),
        _ => Err(PyValueError::new_err(
            "strip must be one of: none, safe, all",
        )),
    }
}

fn parse_deflater(
    value: &Bound<'_, PyAny>,
    preset_deflater: oxi::Deflater,
) -> PyResult<oxi::Deflater> {
    match value_as_string(value, "deflate")?.as_str() {
        "libdeflater" => Ok(preset_deflater),
        "zopfli" => Ok(oxi::Deflater::Zopfli(Default::default())),
        _ => Err(PyValueError::new_err(
            "deflate must be one of: libdeflater, zopfli",
        )),
    }
}

fn parse_filter_strategy(value: &Bound<'_, PyAny>) -> PyResult<oxi::FilterStrategy> {
    match value_as_string(value, "filter")?.as_str() {
        "none" | "0" => Ok(oxi::FilterStrategy::NONE),
        "sub" | "1" => Ok(oxi::FilterStrategy::SUB),
        "up" | "2" => Ok(oxi::FilterStrategy::UP),
        "average" | "3" => Ok(oxi::FilterStrategy::AVERAGE),
        "paeth" | "4" => Ok(oxi::FilterStrategy::PAETH),
        "minsum" | "5" => Ok(oxi::FilterStrategy::MinSum),
        "entropy" | "6" => Ok(oxi::FilterStrategy::Entropy),
        "bigrams" | "7" => Ok(oxi::FilterStrategy::Bigrams),
        "bigent" | "8" => Ok(oxi::FilterStrategy::BigEnt),
        "brute" | "9" => Ok(oxi::FilterStrategy::Brute {
            num_lines: 3,
            level: 1,
        }),
        _ => Err(PyValueError::new_err(
            "filter must be one of: none, sub, up, average, paeth, minsum, entropy, bigrams, bigent, brute, 0-9",
        )),
    }
}

fn parse_filters(value: &Bound<'_, PyAny>) -> PyResult<IndexSet<oxi::FilterStrategy>> {
    let mut filters = IndexSet::new();

    if value.downcast::<PyString>().is_ok() || value.getattr("value").is_ok() {
        filters.insert(parse_filter_strategy(value)?);
        return Ok(filters);
    }

    if let Ok(list) = value.downcast::<PyList>() {
        if list.is_empty() {
            return Err(PyValueError::new_err("filter must not be empty"));
        }
        for item in list.iter() {
            filters.insert(parse_filter_strategy(&item)?);
        }
        return Ok(filters);
    }

    if let Ok(tuple) = value.downcast::<PyTuple>() {
        if tuple.is_empty() {
            return Err(PyValueError::new_err("filter must not be empty"));
        }
        for item in tuple.iter() {
            filters.insert(parse_filter_strategy(&item)?);
        }
        return Ok(filters);
    }

    Err(PyValueError::new_err(
        "filter must be a string, enum value, or non-empty sequence",
    ))
}

fn parse_options(kwargs: Option<&Bound<'_, PyDict>>, mode: ParseMode) -> PyResult<ParsedOptions> {
    let mut level = 2_u8;
    let mut interlace = None;
    let mut strip = None;
    let mut deflate = None;
    let mut filters = None;
    let mut fix_errors = false;
    let mut force = false;
    let mut backup = false;
    let mut preserve_attrs = false;

    if let Some(dict) = kwargs {
        for (key, value) in dict.iter() {
            let key: String = key.extract()?;

            match key.as_str() {
                "level" => level = parse_level(&value)?,
                "interlace" => {
                    if !value.is_none() {
                        interlace = Some(parse_interlace(&value)?);
                    }
                }
                "strip" => {
                    if !value.is_none() {
                        strip = Some(parse_strip(&value)?);
                    }
                }
                "deflate" => {
                    if !value.is_none() {
                        deflate = Some(value.unbind());
                    }
                }
                "filter" => {
                    if !value.is_none() {
                        filters = Some(parse_filters(&value)?);
                    }
                }
                "fix_errors" => fix_errors = parse_bool(&value, "fix_errors")?,
                "force" => force = parse_bool(&value, "force")?,
                "backup" if matches!(mode, ParseMode::File) => {
                    backup = parse_bool(&value, "backup")?;
                }
                "preserve_attrs" if matches!(mode, ParseMode::File) => {
                    preserve_attrs = parse_bool(&value, "preserve_attrs")?;
                }
                "backup" | "preserve_attrs" => {
                    return Err(PyTypeError::new_err(format!("unsupported option: {key}")));
                }
                _ => {
                    return Err(PyTypeError::new_err(format!("unsupported option: {key}")));
                }
            }
        }
    }

    let mut options = oxi::Options::from_preset(level);
    if let Some(value) = interlace {
        options.interlace = value;
    }
    if let Some(value) = strip {
        options.strip = value;
    }
    if let Some(value) = deflate {
        Python::with_gil(|py| {
            options.deflater = parse_deflater(value.bind(py), options.deflater)?;
            Ok::<(), PyErr>(())
        })?;
    }
    if let Some(value) = filters {
        options.filters = value;
    }
    options.fix_errors = fix_errors;
    options.force = force;

    Ok(ParsedOptions {
        options,
        backup,
        preserve_attrs,
    })
}

fn map_png_error(error: oxi::PngError) -> PyErr {
    PngError::new_err(error.to_string())
}

#[pyfunction]
#[pyo3(signature = (input, output=None, **kwargs))]
#[pyo3(
    text_signature = "(input, output=None, *, level=2, interlace=None, strip=None, deflate=None, filter=None, fix_errors=False, force=False, backup=False, preserve_attrs=False)"
)]
fn optimize(
    py: Python<'_>,
    input: PathBuf,
    output: Option<PathBuf>,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<()> {
    let parsed = parse_options(kwargs, ParseMode::File)?;

    if parsed.backup && output.is_some() {
        return Err(PyValueError::new_err(
            "backup=True requires in-place optimization",
        ));
    }

    if parsed.backup {
        let backup = PathBuf::from(format!("{}.bak", input.display()));
        if backup.exists() {
            return Err(PyFileExistsError::new_err(backup.display().to_string()));
        }
        fs::copy(&input, &backup).map_err(PyOSError::new_err)?;
    }

    let input_file = oxi::InFile::Path(input);
    let output_file = oxi::OutFile::Path {
        path: output,
        preserve_attrs: parsed.preserve_attrs,
    };

    py.allow_threads(move || oxi::optimize(&input_file, &output_file, &parsed.options))
        .map_err(map_png_error)?;
    Ok(())
}

fn bytes_like_to_vec(data: &Bound<'_, PyAny>) -> PyResult<Vec<u8>> {
    if let Ok(bytes) = data.downcast::<PyBytes>() {
        return Ok(bytes.as_bytes().to_vec());
    }
    if let Ok(bytearray) = data.downcast::<PyByteArray>() {
        return Ok(unsafe { bytearray.as_bytes() }.to_vec());
    }
    if let Ok(bytes) = data.call_method0("tobytes") {
        if let Ok(py_bytes) = bytes.downcast::<PyBytes>() {
            return Ok(py_bytes.as_bytes().to_vec());
        }
    }
    Err(PyTypeError::new_err(
        "data must be bytes, bytearray, or memoryview",
    ))
}

#[pyfunction]
#[pyo3(signature = (data, **kwargs))]
#[pyo3(
    text_signature = "(data, *, level=2, interlace=None, strip=None, deflate=None, filter=None, fix_errors=False, force=False)"
)]
fn optimize_from_memory(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<Vec<u8>> {
    let data = bytes_like_to_vec(data)?;
    let parsed = parse_options(kwargs, ParseMode::Memory)?;

    py.allow_threads(move || oxi::optimize_from_memory(&data, &parsed.options))
        .map_err(map_png_error)
}

#[pymodule]
fn _oxipng(py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("PngError", py.get_type::<PngError>())?;
    module.add_function(wrap_pyfunction!(optimize, module)?)?;
    module.add_function(wrap_pyfunction!(optimize_from_memory, module)?)?;
    Ok(())
}
