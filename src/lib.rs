use indexmap::IndexSet;
use pyo3::buffer::PyBuffer;
use pyo3::create_exception;
use pyo3::exceptions::{
    PyAttributeError, PyDeprecationWarning, PyException, PyFileExistsError, PyOSError, PyTypeError,
    PyValueError,
};
use pyo3::ffi::c_str;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyByteArray, PyBytes, PyDict, PyList, PySet, PyString, PyTuple};
use std::fs::{self, OpenOptions};
use std::io;
use std::num::NonZeroU64;
use std::path::PathBuf;
use std::time::Duration;

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

fn parse_advanced_bool(value: &Bound<'_, PyAny>, option: &str) -> PyResult<Option<bool>> {
    if value.is_none() {
        return Ok(None);
    }
    parse_bool(value, option).map(Some)
}

fn parse_timeout(value: &Bound<'_, PyAny>) -> PyResult<Option<Duration>> {
    if value.is_none() {
        return Ok(None);
    }

    if value.is_instance_of::<PyBool>() {
        return Err(PyTypeError::new_err(
            "timeout must be a non-negative number of seconds or None",
        ));
    }

    let seconds: f64 = value.extract().map_err(|_| {
        PyTypeError::new_err("timeout must be a non-negative number of seconds or None")
    })?;
    if !seconds.is_finite() || seconds < 0.0 {
        return Err(PyValueError::new_err(
            "timeout must be a non-negative number of seconds or None",
        ));
    }

    Duration::try_from_secs_f64(seconds).map(Some).map_err(|_| {
        PyValueError::new_err("timeout must be a non-negative number of seconds or None")
    })
}

fn parse_max_decompressed_size(value: &Bound<'_, PyAny>) -> PyResult<Option<usize>> {
    if value.is_none() {
        return Ok(None);
    }

    if value.is_instance_of::<PyBool>() {
        return Err(PyTypeError::new_err(
            "max_decompressed_size must be a non-negative integer or None",
        ));
    }

    let parsed: i128 = value.extract().map_err(|_| {
        PyTypeError::new_err("max_decompressed_size must be a non-negative integer or None")
    })?;
    if parsed < 0 {
        return Err(PyValueError::new_err(
            "max_decompressed_size must be a non-negative integer or None",
        ));
    }

    usize::try_from(parsed).map(Some).map_err(|_| {
        PyValueError::new_err("max_decompressed_size must be a non-negative integer or None")
    })
}

fn warn_pyoxipng_compat(py: Python<'_>) -> PyResult<()> {
    PyErr::warn(
        py,
        &py.get_type::<PyDeprecationWarning>(),
        c_str!(
            "pyoxipng compatibility path is unsupported; migrate to oxipng-pybind's stable API; this compatibility path will be removed in a future release."
        ),
        2,
    )
}

fn is_oxipng_compat_type(value: &Bound<'_, PyAny>, qualname: &str) -> PyResult<bool> {
    let value_type = value.get_type();
    let module = value_type.module()?.to_str()?.to_owned();
    let actual_qualname = value_type.qualname()?.to_str()?.to_owned();
    let helper_qualname = qualname.trim_start_matches('_');
    Ok((module == "oxipng" && actual_qualname == qualname)
        || (module == "oxipng._pyoxipng_compat" && actual_qualname == helper_qualname))
}

fn py_string_attr(value: &Bound<'_, PyAny>, name: &str) -> PyResult<Option<String>> {
    match value.getattr(name) {
        Ok(attr) => Ok(Some(attr.extract()?)),
        Err(error) if error.is_instance_of::<PyAttributeError>(value.py()) => Ok(None),
        Err(error) => Err(error),
    }
}

fn py_int_attr(value: &Bound<'_, PyAny>, name: &str) -> PyResult<Option<i64>> {
    match value.getattr(name) {
        Ok(attr) => Ok(Some(attr.extract()?)),
        Err(error) if error.is_instance_of::<PyAttributeError>(value.py()) => Ok(None),
        Err(error) => Err(error),
    }
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

fn parse_chunk_name_text(name: &str) -> PyResult<[u8; 4]> {
    let bytes = name.as_bytes();
    let name: [u8; 4] = bytes
        .try_into()
        .map_err(|_| PyValueError::new_err("chunk name must be exactly 4 ASCII letters"))?;
    if !name.iter().all(u8::is_ascii_alphabetic) {
        return Err(PyValueError::new_err(
            "chunk name must be exactly 4 ASCII letters",
        ));
    }
    Ok(name)
}

fn parse_strip(value: &Bound<'_, PyAny>) -> PyResult<oxi::StripChunks> {
    if is_oxipng_compat_type(value, "_CompatStripChunks")? {
        let mode = py_string_attr(value, "mode")?
            .ok_or_else(|| PyValueError::new_err("strip compatibility object missing mode"))?;
        let names = value
            .getattr("names")?
            .downcast_into::<PyTuple>()
            .map_err(|_| {
                PyValueError::new_err("strip compatibility object names must be a tuple")
            })?;
        let mut parsed = IndexSet::new();
        for item in names.iter() {
            let name: String = item.extract()?;
            parsed.insert(parse_chunk_name_text(&name)?);
        }
        return match mode.as_str() {
            "strip" => Ok(oxi::StripChunks::Strip(parsed)),
            "keep" => Ok(oxi::StripChunks::Keep(parsed)),
            _ => Err(PyValueError::new_err(
                "strip compatibility mode must be strip or keep",
            )),
        };
    }

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
    if is_oxipng_compat_type(value, "_CompatDeflater")? {
        let kind = py_string_attr(value, "kind")?
            .ok_or_else(|| PyValueError::new_err("deflate compatibility object missing kind"))?;
        let raw_value = py_int_attr(value, "value")?
            .ok_or_else(|| PyValueError::new_err("deflate compatibility object missing value"))?;
        return match kind.as_str() {
            "libdeflater" => {
                let compression = u8::try_from(raw_value).map_err(|_| {
                    PyValueError::new_err("deflate libdeflater compression must be 0-12")
                })?;
                if compression > 12 {
                    return Err(PyValueError::new_err(
                        "deflate libdeflater compression must be 0-12",
                    ));
                }
                Ok(oxi::Deflater::Libdeflater { compression })
            }
            "zopfli" => {
                let iterations = u8::try_from(raw_value)
                    .ok()
                    .map(u64::from)
                    .and_then(NonZeroU64::new)
                    .ok_or_else(|| {
                        PyValueError::new_err("deflate zopfli iterations must be 1-255")
                    })?;
                Ok(oxi::Deflater::Zopfli(oxi::ZopfliOptions {
                    iteration_count: iterations,
                    ..Default::default()
                }))
            }
            _ => Err(PyValueError::new_err(
                "deflate compatibility kind must be libdeflater or zopfli",
            )),
        };
    }

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

fn parse_basic_row_filter(value: &str) -> PyResult<oxi::RowFilter> {
    match value {
        "none" | "0" => Ok(oxi::RowFilter::None),
        "sub" | "1" => Ok(oxi::RowFilter::Sub),
        "up" | "2" => Ok(oxi::RowFilter::Up),
        "average" | "3" => Ok(oxi::RowFilter::Average),
        "paeth" | "4" => Ok(oxi::RowFilter::Paeth),
        _ => Err(PyValueError::new_err(
            "predefined filter entries must be one of: none, sub, up, average, paeth, 0-4",
        )),
    }
}

fn parse_predefined_filters(value: &Bound<'_, PyAny>) -> PyResult<oxi::FilterStrategy> {
    let filters = value
        .getattr("filters")?
        .downcast_into::<PyTuple>()
        .map_err(|_| PyValueError::new_err("predefined filter entries must be a tuple"))?;
    if filters.is_empty() {
        return Err(PyValueError::new_err("predefined filter must not be empty"));
    }

    let mut parsed = Vec::with_capacity(filters.len());
    for item in filters.iter() {
        let filter: String = item.extract()?;
        parsed.push(parse_basic_row_filter(&filter)?);
    }
    Ok(oxi::FilterStrategy::Predefined(parsed))
}

fn parse_filters(value: &Bound<'_, PyAny>) -> PyResult<IndexSet<oxi::FilterStrategy>> {
    let mut filters = IndexSet::new();

    if is_oxipng_compat_type(value, "_PredefinedFilters")? {
        filters.insert(parse_predefined_filters(value)?);
        return Ok(filters);
    }

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

    if let Ok(set) = value.downcast::<PySet>() {
        if set.is_empty() {
            return Err(PyValueError::new_err("filter must not be empty"));
        }
        for item in set.iter() {
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
    let mut optimize_alpha = None;
    let mut bit_depth_reduction = None;
    let mut color_type_reduction = None;
    let mut palette_reduction = None;
    let mut grayscale_reduction = None;
    let mut idat_recoding = None;
    let mut scale_16 = None;
    let mut fast_evaluation = None;
    let mut timeout = None;
    let mut max_decompressed_size = None;

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
                "optimize_alpha" => {
                    optimize_alpha = parse_advanced_bool(&value, "optimize_alpha")?;
                }
                "bit_depth_reduction" => {
                    bit_depth_reduction = parse_advanced_bool(&value, "bit_depth_reduction")?;
                }
                "color_type_reduction" => {
                    color_type_reduction = parse_advanced_bool(&value, "color_type_reduction")?;
                }
                "palette_reduction" => {
                    palette_reduction = parse_advanced_bool(&value, "palette_reduction")?;
                }
                "grayscale_reduction" => {
                    grayscale_reduction = parse_advanced_bool(&value, "grayscale_reduction")?;
                }
                "idat_recoding" => {
                    idat_recoding = parse_advanced_bool(&value, "idat_recoding")?;
                }
                "scale_16" => {
                    scale_16 = parse_advanced_bool(&value, "scale_16")?;
                }
                "fast_evaluation" => {
                    fast_evaluation = parse_advanced_bool(&value, "fast_evaluation")?;
                }
                "timeout" => {
                    timeout = parse_timeout(&value)?;
                }
                "max_decompressed_size" => {
                    max_decompressed_size = parse_max_decompressed_size(&value)?;
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
    if let Some(value) = optimize_alpha {
        options.optimize_alpha = value;
    }
    if let Some(value) = bit_depth_reduction {
        options.bit_depth_reduction = value;
    }
    if let Some(value) = color_type_reduction {
        options.color_type_reduction = value;
    }
    if let Some(value) = palette_reduction {
        options.palette_reduction = value;
    }
    if let Some(value) = grayscale_reduction {
        options.grayscale_reduction = value;
    }
    if let Some(value) = idat_recoding {
        options.idat_recoding = value;
    }
    if let Some(value) = scale_16 {
        options.scale_16 = value;
    }
    if let Some(value) = fast_evaluation {
        options.fast_evaluation = value;
    }
    options.timeout = timeout;
    if let Some(value) = max_decompressed_size {
        options.max_decompressed_size = Some(value);
    }
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

fn backup_path_for(input: &std::path::Path) -> PathBuf {
    let mut backup = input.as_os_str().to_os_string();
    backup.push(".bak");
    PathBuf::from(backup)
}

fn create_backup(input: &std::path::Path) -> io::Result<PathBuf> {
    let backup = backup_path_for(input);
    let mut source = fs::File::open(input)?;
    let mut destination = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&backup)?;
    io::copy(&mut source, &mut destination)?;
    Ok(backup)
}

/// PNG optimization sizes from a dry run.
#[pyclass(name = "OptimizationResult", frozen)]
struct PyOptimizationResult {
    original_size: usize,
    optimized_size: usize,
}

#[pymethods]
impl PyOptimizationResult {
    #[getter]
    fn original_size(&self) -> usize {
        self.original_size
    }

    #[getter]
    fn optimized_size(&self) -> usize {
        self.optimized_size
    }
}

/// Optimize a PNG file on disk.
#[pyfunction]
#[pyo3(signature = (input, output=None, **kwargs))]
#[pyo3(
    text_signature = "(input, output=None, *, level=2, interlace=None, strip=None, deflate=None, filter=None, fix_errors=False, force=False, backup=False, preserve_attrs=False, optimize_alpha=None, bit_depth_reduction=None, color_type_reduction=None, palette_reduction=None, grayscale_reduction=None, idat_recoding=None, scale_16=None, fast_evaluation=None, timeout=None, max_decompressed_size=None)"
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
        let backup_input = input.clone();
        py.allow_threads(move || create_backup(&backup_input))
            .map_err(|error| {
                if error.kind() == io::ErrorKind::AlreadyExists {
                    PyFileExistsError::new_err(backup_path_for(&input).display().to_string())
                } else {
                    PyOSError::new_err(error)
                }
            })?;
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

/// Return PNG optimization sizes without writing output.
#[pyfunction]
#[pyo3(signature = (input, **kwargs))]
#[pyo3(
    text_signature = "(input, *, level=2, interlace=None, strip=None, deflate=None, filter=None, fix_errors=False, force=False, optimize_alpha=None, bit_depth_reduction=None, color_type_reduction=None, palette_reduction=None, grayscale_reduction=None, idat_recoding=None, scale_16=None, fast_evaluation=None, timeout=None, max_decompressed_size=None)"
)]
fn analyze(
    py: Python<'_>,
    input: PathBuf,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<PyOptimizationResult> {
    let parsed = parse_options(kwargs, ParseMode::Memory)?;
    let input_file = oxi::InFile::Path(input);
    let output_file = oxi::OutFile::None;

    let (original_size, optimized_size) = py
        .allow_threads(move || oxi::optimize(&input_file, &output_file, &parsed.options))
        .map_err(map_png_error)?;

    Ok(PyOptimizationResult {
        original_size,
        optimized_size,
    })
}

fn bytes_like_to_vec(data: &Bound<'_, PyAny>) -> PyResult<Vec<u8>> {
    if let Ok(bytes) = data.downcast::<PyBytes>() {
        return Ok(bytes.as_bytes().to_vec());
    }
    if let Ok(bytearray) = data.downcast::<PyByteArray>() {
        return Ok(unsafe { bytearray.as_bytes() }.to_vec());
    }
    if let Ok(buffer) = PyBuffer::<u8>::get(data) {
        return buffer.to_vec(data.py());
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

fn parse_bit_depth(value: &Bound<'_, PyAny>) -> PyResult<oxi::BitDepth> {
    let raw_value = if let Ok(enum_value) = value.getattr("value") {
        enum_value.extract::<u8>()
    } else {
        value.extract::<u8>()
    }
    .map_err(|_| PyValueError::new_err("bit_depth must be one of: 1, 2, 4, 8, 16"))?;

    oxi::BitDepth::try_from(raw_value)
        .map_err(|_| PyValueError::new_err("bit_depth must be one of: 1, 2, 4, 8, 16"))
}

fn extract_u16(value: &Bound<'_, PyAny>, context: &str) -> PyResult<u16> {
    let parsed: u32 = value
        .extract()
        .map_err(|_| PyValueError::new_err(format!("{context} must contain integers")))?;
    u16::try_from(parsed)
        .map_err(|_| PyValueError::new_err(format!("{context} values must fit in u16")))
}

fn extract_u8(value: &Bound<'_, PyAny>, context: &str) -> PyResult<u8> {
    let parsed: u32 = value
        .extract()
        .map_err(|_| PyValueError::new_err(format!("{context} must contain integers")))?;
    u8::try_from(parsed)
        .map_err(|_| PyValueError::new_err(format!("{context} values must fit in u8")))
}

fn bit_depth_value(bit_depth: oxi::BitDepth) -> u8 {
    bit_depth as u8
}

fn max_sample_value(bit_depth: oxi::BitDepth) -> u16 {
    match bit_depth_value(bit_depth) {
        16 => u16::MAX,
        value => (1_u16 << value) - 1,
    }
}

fn validate_transparent_value(value: u16, bit_depth: oxi::BitDepth) -> PyResult<()> {
    let max = max_sample_value(bit_depth);
    if value > max {
        return Err(PyValueError::new_err(format!(
            "transparent values must be between 0 and {max} for this bit depth"
        )));
    }
    Ok(())
}

fn parse_rgb16_with_depth(
    value: &Bound<'_, PyAny>,
    context: &str,
    bit_depth: oxi::BitDepth,
) -> PyResult<oxi::RGB16> {
    let tuple = value
        .downcast::<PyTuple>()
        .map_err(|_| PyValueError::new_err(format!("{context} must be a 3-tuple")))?;
    if tuple.len() != 3 {
        return Err(PyValueError::new_err(format!(
            "{context} must be a 3-tuple"
        )));
    }
    let r = extract_u16(&tuple.get_item(0)?, context)?;
    let g = extract_u16(&tuple.get_item(1)?, context)?;
    let b = extract_u16(&tuple.get_item(2)?, context)?;
    validate_transparent_value(r, bit_depth)?;
    validate_transparent_value(g, bit_depth)?;
    validate_transparent_value(b, bit_depth)?;
    Ok(oxi::RGB16::new(r, g, b))
}

fn validate_png_chunk_name(name: [u8; 4]) -> PyResult<[u8; 4]> {
    if !name.iter().all(u8::is_ascii_alphabetic) {
        return Err(PyValueError::new_err(
            "chunk name must contain exactly 4 ASCII letters",
        ));
    }
    if !name[0].is_ascii_lowercase() {
        return Err(PyValueError::new_err(
            "chunk name must be an ancillary PNG chunk",
        ));
    }
    if !name[1].is_ascii_uppercase() {
        return Err(PyValueError::new_err(
            "chunk name must be a public PNG chunk",
        ));
    }
    if !name[2].is_ascii_uppercase() {
        return Err(PyValueError::new_err(
            "chunk name must use a valid reserved bit",
        ));
    }
    if !name[3].is_ascii_lowercase() {
        return Err(PyValueError::new_err(
            "chunk name must be a safe-to-copy ancillary PNG chunk",
        ));
    }
    if matches!(
        &name,
        b"IHDR" | b"PLTE" | b"IDAT" | b"IEND" | b"tRNS" | b"iCCP"
    ) {
        return Err(PyValueError::new_err(
            "chunk name is reserved for structured RawImage data",
        ));
    }
    Ok(name)
}

fn validate_indexed_pixels(
    data: &[u8],
    width: u32,
    height: u32,
    palette_len: usize,
    bit_depth: oxi::BitDepth,
) -> PyResult<()> {
    let max_palette_len = 1_usize << bit_depth_value(bit_depth);
    if palette_len > max_palette_len {
        return Err(PyValueError::new_err(format!(
            "palette length must be at most {max_palette_len} for this bit depth"
        )));
    }

    let bit_depth = usize::from(bit_depth_value(bit_depth));
    if bit_depth > 8 {
        return Ok(());
    }
    let width = width as usize;
    let row_bytes = (width * bit_depth).div_ceil(8);
    let mask = ((1_u16 << bit_depth) - 1) as u8;

    for row in 0..height as usize {
        let start = row * row_bytes;
        let end = start + row_bytes;
        if end > data.len() {
            break;
        }
        let row_data = &data[start..end];
        for x in 0..width {
            let byte = row_data[x * bit_depth / 8];
            let shift = 8 - bit_depth - (x * bit_depth % 8);
            let index = (byte >> shift) & mask;
            if usize::from(index) >= palette_len {
                return Err(PyValueError::new_err(
                    "pixel index must be less than palette length",
                ));
            }
        }
    }
    Ok(())
}

fn parse_palette_color(value: &Bound<'_, PyAny>) -> PyResult<oxi::RGBA8> {
    let tuple = value
        .downcast::<PyTuple>()
        .map_err(|_| PyValueError::new_err("palette entries must be 3- or 4-tuples"))?;
    if tuple.len() != 3 && tuple.len() != 4 {
        return Err(PyValueError::new_err(
            "palette entries must be 3- or 4-tuples",
        ));
    }
    let alpha = if tuple.len() == 4 {
        extract_u8(&tuple.get_item(3)?, "palette")?
    } else {
        255
    };
    Ok(oxi::RGBA8::new(
        extract_u8(&tuple.get_item(0)?, "palette")?,
        extract_u8(&tuple.get_item(1)?, "palette")?,
        extract_u8(&tuple.get_item(2)?, "palette")?,
        alpha,
    ))
}

fn parse_palette(value: Option<&Bound<'_, PyAny>>) -> PyResult<Vec<oxi::RGBA8>> {
    let Some(value) = value else {
        return Err(PyValueError::new_err(
            "palette is required for indexed raw images",
        ));
    };
    let list = value
        .downcast::<PyList>()
        .map_err(|_| PyValueError::new_err("palette must be a list of colors"))?;
    if list.is_empty() || list.len() > 256 {
        return Err(PyValueError::new_err(
            "palette must contain between 1 and 256 colors",
        ));
    }
    list.iter().map(|item| parse_palette_color(&item)).collect()
}

fn parse_color_type(
    color_type: &Bound<'_, PyAny>,
    bit_depth: oxi::BitDepth,
    palette: Option<&Bound<'_, PyAny>>,
    transparent: Option<&Bound<'_, PyAny>>,
) -> PyResult<oxi::ColorType> {
    match value_as_string(color_type, "color_type")?.as_str() {
        "grayscale" => {
            let transparent_shade = transparent
                .map(|value| extract_u16(value, "transparent"))
                .transpose()?;
            if let Some(value) = transparent_shade {
                validate_transparent_value(value, bit_depth)?;
            }
            Ok(oxi::ColorType::Grayscale { transparent_shade })
        }
        "rgb" => {
            let transparent_color = transparent
                .map(|value| parse_rgb16_with_depth(value, "transparent", bit_depth))
                .transpose()?;
            Ok(oxi::ColorType::RGB { transparent_color })
        }
        "indexed" => {
            if transparent.is_some() {
                return Err(PyValueError::new_err(
                    "transparent is not supported for indexed raw images; use alpha values in palette entries",
                ));
            }
            Ok(oxi::ColorType::Indexed {
                palette: parse_palette(palette)?,
            })
        }
        "grayscale_alpha" => {
            if transparent.is_some() {
                return Err(PyValueError::new_err(
                    "transparent is not supported for grayscale_alpha raw images",
                ));
            }
            Ok(oxi::ColorType::GrayscaleAlpha)
        }
        "rgba" => {
            if transparent.is_some() {
                return Err(PyValueError::new_err(
                    "transparent is not supported for rgba raw images",
                ));
            }
            Ok(oxi::ColorType::RGBA)
        }
        _ => Err(PyValueError::new_err(
            "color_type must be one of: grayscale, rgb, indexed, grayscale_alpha, rgba",
        )),
    }
}

/// Raw image data for creating optimized PNG bytes.
#[pyclass(name = "RawImage")]
struct PyRawImage {
    inner: oxi::RawImage,
}

impl PyRawImage {
    fn new_stable(args: &Bound<'_, PyTuple>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        Self::reject_extra_kwargs(
            kwargs,
            &[
                "width",
                "height",
                "color_type",
                "bit_depth",
                "data",
                "palette",
                "transparent",
            ],
        )?;
        let width: u32 = Self::raw_image_required_arg(args, kwargs, 0, "width")?.extract()?;
        let height: u32 = Self::raw_image_required_arg(args, kwargs, 1, "height")?.extract()?;
        let color_type = Self::raw_image_required_arg(args, kwargs, 2, "color_type")?;
        let bit_depth = Self::raw_image_required_arg(args, kwargs, 3, "bit_depth")?;
        let data = Self::raw_image_required_arg(args, kwargs, 4, "data")?;
        let palette = Self::raw_image_kwarg(kwargs, "palette")?;
        let transparent = Self::raw_image_kwarg(kwargs, "transparent")?;
        Self::from_parts(
            width,
            height,
            &color_type,
            &bit_depth,
            &data,
            palette.as_ref(),
            transparent.as_ref(),
        )
    }

    fn new_pyoxipng_compat(
        args: &Bound<'_, PyTuple>,
        kwargs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Self> {
        warn_pyoxipng_compat(args.py())?;

        let data = args.get_item(0)?;
        let width: u32 = args.get_item(1)?.extract()?;
        let height: u32 = args.get_item(2)?.extract()?;
        let kwargs = kwargs.ok_or_else(|| PyTypeError::new_err("color_type is required"))?;
        let color_type = kwargs
            .get_item("color_type")?
            .ok_or_else(|| PyTypeError::new_err("color_type is required"))?;
        Self::reject_extra_kwargs(Some(kwargs), &["color_type"])?;

        if !is_oxipng_compat_type(&color_type, "_CompatColorType")? {
            return Err(PyTypeError::new_err(
                "color_type must be created by ColorType compatibility factories",
            ));
        }

        let kind = py_string_attr(&color_type, "kind")?
            .ok_or_else(|| PyValueError::new_err("color_type compatibility object missing kind"))?;
        let raw_bit_depth = py_int_attr(&color_type, "bit_depth")?.ok_or_else(|| {
            PyValueError::new_err("color_type compatibility object missing bit_depth")
        })?;
        let bit_depth = u8::try_from(raw_bit_depth)
            .map_err(|_| PyValueError::new_err("bit_depth must be one of: 1, 2, 4, 8, 16"))?;
        let palette = color_type.getattr("palette")?;
        let transparent = color_type.getattr("transparent")?;
        let kind = PyString::new(args.py(), &kind);
        let bit_depth = bit_depth.into_pyobject(args.py())?;

        Self::from_parts(
            width,
            height,
            kind.as_any(),
            bit_depth.as_any(),
            &data,
            (!palette.is_none()).then_some(palette.as_any()),
            (!transparent.is_none()).then_some(transparent.as_any()),
        )
    }

    fn raw_image_kwarg<'py>(
        kwargs: Option<&Bound<'py, PyDict>>,
        name: &str,
    ) -> PyResult<Option<Bound<'py, PyAny>>> {
        kwargs
            .map(|dict| dict.get_item(name))
            .transpose()
            .map(Option::flatten)
    }

    fn raw_image_required_arg<'py>(
        args: &Bound<'py, PyTuple>,
        kwargs: Option<&Bound<'py, PyDict>>,
        index: usize,
        name: &str,
    ) -> PyResult<Bound<'py, PyAny>> {
        let keyword_value = Self::raw_image_kwarg(kwargs, name)?;
        if index < args.len() {
            if keyword_value.is_some() {
                return Err(PyTypeError::new_err(format!(
                    "RawImage got multiple values for argument '{name}'"
                )));
            }
            return args.get_item(index);
        }
        keyword_value.ok_or_else(|| {
            PyTypeError::new_err(format!(
                "RawImage missing required argument '{name}' for stable constructor"
            ))
        })
    }

    fn has_raw_image_kwarg(kwargs: Option<&Bound<'_, PyDict>>, name: &str) -> PyResult<bool> {
        Ok(Self::raw_image_kwarg(kwargs, name)?.is_some())
    }

    fn reject_extra_kwargs(kwargs: Option<&Bound<'_, PyDict>>, allowed: &[&str]) -> PyResult<()> {
        if let Some(dict) = kwargs {
            for key in dict.keys().iter() {
                let key: String = key.extract()?;
                if !allowed.contains(&key.as_str()) {
                    return Err(PyTypeError::new_err(format!(
                        "unsupported RawImage option: {key}"
                    )));
                }
            }
        }
        Ok(())
    }

    fn from_parts(
        width: u32,
        height: u32,
        color_type: &Bound<'_, PyAny>,
        bit_depth: &Bound<'_, PyAny>,
        data: &Bound<'_, PyAny>,
        palette: Option<&Bound<'_, PyAny>>,
        transparent: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Self> {
        let bit_depth = parse_bit_depth(bit_depth)?;
        let color_type = parse_color_type(color_type, bit_depth, palette, transparent)?;
        let data = bytes_like_to_vec(data)?;
        if let oxi::ColorType::Indexed { palette } = &color_type {
            validate_indexed_pixels(&data, width, height, palette.len(), bit_depth)?;
        }
        let inner = oxi::RawImage::new(width, height, color_type, bit_depth, data)
            .map_err(map_png_error)?;
        Ok(Self { inner })
    }
}

#[pymethods]
impl PyRawImage {
    #[new]
    #[pyo3(signature = (*args, **kwargs))]
    fn new(args: &Bound<'_, PyTuple>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        if args.len() == 3 && Self::has_raw_image_kwarg(kwargs, "color_type")? {
            return Self::new_pyoxipng_compat(args, kwargs);
        }
        if args.len() <= 5 {
            return Self::new_stable(args, kwargs);
        }

        Err(PyTypeError::new_err(
            "RawImage expects either (width, height, color_type, bit_depth, data) or (data, width, height, color_type=...)",
        ))
    }

    /// Add an auxiliary PNG chunk.
    fn add_png_chunk(&mut self, name: &Bound<'_, PyAny>, data: &Bound<'_, PyAny>) -> PyResult<()> {
        let name = bytes_like_to_vec(name)?;
        let data = bytes_like_to_vec(data)?;
        let name: [u8; 4] = name
            .try_into()
            .map_err(|_| PyValueError::new_err("chunk name must be exactly 4 bytes"))?;
        let name = validate_png_chunk_name(name)?;
        self.inner.add_png_chunk(name, data);
        Ok(())
    }

    /// Add an ICC profile.
    fn add_icc_profile(&mut self, data: &Bound<'_, PyAny>) -> PyResult<()> {
        let data = bytes_like_to_vec(data)?;
        self.inner.add_icc_profile(&data);
        Ok(())
    }

    /// Return optimized PNG bytes.
    #[pyo3(signature = (**kwargs))]
    #[pyo3(
        text_signature = "(*, level=2, interlace=None, strip=None, deflate=None, filter=None, fix_errors=False, force=False, optimize_alpha=None, bit_depth_reduction=None, color_type_reduction=None, palette_reduction=None, grayscale_reduction=None, idat_recoding=None, scale_16=None, fast_evaluation=None, timeout=None, max_decompressed_size=None)"
    )]
    fn create_optimized_png(
        &self,
        py: Python<'_>,
        kwargs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Vec<u8>> {
        let parsed = parse_options(kwargs, ParseMode::Memory)?;
        py.allow_threads(|| self.inner.create_optimized_png(&parsed.options))
            .map_err(map_png_error)
    }
}

/// Optimize PNG bytes in memory.
#[pyfunction]
#[pyo3(signature = (data, **kwargs))]
#[pyo3(
    text_signature = "(data, *, level=2, interlace=None, strip=None, deflate=None, filter=None, fix_errors=False, force=False, optimize_alpha=None, bit_depth_reduction=None, color_type_reduction=None, palette_reduction=None, grayscale_reduction=None, idat_recoding=None, scale_16=None, fast_evaluation=None, timeout=None, max_decompressed_size=None)"
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
    module.add_class::<PyRawImage>()?;
    module.add_class::<PyOptimizationResult>()?;
    module.add_function(wrap_pyfunction!(analyze, module)?)?;
    module.add_function(wrap_pyfunction!(optimize, module)?)?;
    module.add_function(wrap_pyfunction!(optimize_from_memory, module)?)?;
    Ok(())
}
