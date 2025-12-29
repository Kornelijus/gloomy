from gloomy import gloom, assign

assert gloom({"a": {"b": {"c": [123]}}}, "a.b.c.0") == 123
assert gloom({}, "a.b.c", default=None) is None
assert assign({"a": {"b": {"c": [123]}}}, "a.b.c.0", 456) == {"a": {"b": {"c": [456]}}}
