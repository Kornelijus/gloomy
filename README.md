# gloomy

> glom, but not as slow

An utility for retrieving values from deeply nested object attributes, mapping keys, sequence indexes, or any combination of them.

Not meant as a drop in replacement for `glom`, only basic functionality is implemented.  
A good use-case would be to improve existing codebases in which the `glom` pattern is commonly used for convenience, as it can significantly affect performance.

### Planned features
🏗️ `assign` utility  
🏗️ `Path` object 

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
