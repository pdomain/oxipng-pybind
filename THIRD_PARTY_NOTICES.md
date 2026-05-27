# Third-Party Notices

`oxipng-pybind` wraps upstream `oxipng`.

The Python wheel includes a native Rust extension. Runtime Rust dependencies
retain their upstream licenses and notices.

## Runtime Rust Dependencies

- Project: [oxipng](https://github.com/oxipng/oxipng)
- License: MIT
- Purpose: lossless PNG optimization library

- Project: [PyO3](https://github.com/PyO3/pyo3)
- License: Apache-2.0 OR MIT
- Purpose: Python extension-module bindings for Rust

- Project: [indexmap](https://github.com/indexmap-rs/indexmap)
- License: Apache-2.0 OR MIT
- Purpose: deterministic insertion-ordered maps and sets

- Project: [libdeflater](https://github.com/adamkewley/libdeflater)
- License: MIT
- Purpose: Rust bindings around libdeflate compression

- Project: [zopfli](https://github.com/carols10cents/zopfli)
- License: Apache-2.0
- Purpose: DEFLATE compression backend

- Project: [rayon](https://github.com/rayon-rs/rayon)
- License: Apache-2.0 OR MIT
- Purpose: data-parallel execution used by upstream optimization

- Project: [crossbeam](https://github.com/crossbeam-rs/crossbeam)
- License: Apache-2.0 OR MIT
- Purpose: concurrency primitives used by Rayon

- Project: [rgb](https://github.com/kornelski/rust-rgb)
- License: MIT
- Purpose: pixel color data types

- Project: [bytemuck](https://github.com/Lokathor/bytemuck)
- License: Apache-2.0 OR MIT OR Zlib
- Purpose: byte casting support used by image/color dependencies

Run `make rust-deny` to verify Rust dependency license policy.
