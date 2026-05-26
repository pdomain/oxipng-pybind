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
    palette_len: usize,
    bit_depth: oxi::BitDepth,
) -> PyResult<()> {
    let max_palette_len = 1_usize << bit_depth_value(bit_depth);
    if palette_len > max_palette_len {
        return Err(PyValueError::new_err(format!(
            "palette length must be at most {max_palette_len} for this bit depth"
        )));
    }

    match bit_depth_value(bit_depth) {
        8 => {
            if data.iter().any(|index| usize::from(*index) >= palette_len) {
                return Err(PyValueError::new_err(
                    "pixel index must be less than palette length",
                ));
            }
        }
        4 => {
            for byte in data {
                for index in [byte >> 4, byte & 0x0f] {
                    if usize::from(index) >= palette_len {
                        return Err(PyValueError::new_err(
                            "pixel index must be less than palette length",
                        ));
                    }
                }
            }
        }
        2 => {
            for byte in data {
                for shift in [6, 4, 2, 0] {
                    if usize::from((byte >> shift) & 0x03) >= palette_len {
                        return Err(PyValueError::new_err(
                            "pixel index must be less than palette length",
                        ));
                    }
                }
            }
        }
        1 => {
            if palette_len < 2 && data.iter().any(|byte| *byte != 0) {
                return Err(PyValueError::new_err(
                    "pixel index must be less than palette length",
                ));
            }
        }
        _ => {}
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

#[pyclass(name = "RawImage")]
struct PyRawImage {
    inner: oxi::RawImage,
}

#[pymethods]
impl PyRawImage {
    #[new]
    #[pyo3(signature = (width, height, color_type, bit_depth, data, *, palette=None, transparent=None))]
    fn new(
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
            validate_indexed_pixels(&data, palette.len(), bit_depth)?;
        }
        let inner = oxi::RawImage::new(width, height, color_type, bit_depth, data)
            .map_err(map_png_error)?;
        Ok(Self { inner })
    }

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

    fn add_icc_profile(&mut self, data: &Bound<'_, PyAny>) -> PyResult<()> {
        let data = bytes_like_to_vec(data)?;
        self.inner.add_icc_profile(&data);
        Ok(())
    }

    #[pyo3(signature = (**kwargs))]
    #[pyo3(
        text_signature = "(*, level=2, interlace=None, strip=None, deflate=None, filter=None, fix_errors=False, force=False)"
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
    module.add_class::<PyRawImage>()?;
    module.add_function(wrap_pyfunction!(optimize, module)?)?;
    module.add_function(wrap_pyfunction!(optimize_from_memory, module)?)?;
    Ok(())
}
