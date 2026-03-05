# gloomy

> glom, but not as slow

An utility for retrieving values from deeply nested object attributes, mapping keys, sequence indexes, or any combination of them.

Not meant as a drop in replacement for `glom`, only basic functionality is implemented.  
A good use-case would be to improve existing codebases in which the `glom` pattern is commonly used for convenience, as it can significantly affect performance.

### Features

- `gloom` (replaces `glom`)
- `assign`
- `delete`
- dot separated `str` and `tuple[str, ...]` paths supported for traversal

🏗️ `delete` utility

### Installation

```sh
uv pip install gloomy
```

### Usage

```python
from gloomy import gloom

assert gloom({"a": {"b": {"c": [123]}}}, "a.b.c.0") == 123

# Or with a default in case the path is invalid
assert gloom({}, "a.b.c", default=None) is None
```

### Benchmarks

### `gloom (fetch)`

| Scenario                  |  gloomy |     glom |  speedup  |
| ------------------------- | ------: | -------: | :-------: |
| 5-level dict (hit)        | 1.37 µs | 22.58 µs | **16.5×** |
| 5-level dict (miss)       | 1.35 µs | 22.26 µs | **16.5×** |
| 3-level object attr (hit) |  263 ns |  7.16 µs | **27.2×** |
| 5-level list index (hit)  |  500 ns | 10.47 µs | **20.9×** |

### `assign`

| Scenario               |  gloomy |     glom |  speedup  |
| ---------------------- | ------: | -------: | :-------: |
| 1-level dict           |  496 ns |  6.05 µs | **12.2×** |
| 5-level dict           | 1.73 µs | 13.87 µs | **8.0×**  |
| list index             |  895 ns |  8.25 µs | **9.2×**  |
| realistic API response | 3.38 µs | 14.16 µs | **4.2×**  |

### `delete`

| Scenario               | gloomy |     glom |  speedup  |
| ---------------------- | -----: | -------: | :-------: |
| 1-level dict           | 245 ns |  4.97 µs | **20.3×** |
| 5-level dict           | 406 ns | 12.86 µs | **31.7×** |
| list index             | 284 ns |  7.01 µs | **24.7×** |
| realistic API response | 565 ns | 11.22 µs | **19.9×** |
