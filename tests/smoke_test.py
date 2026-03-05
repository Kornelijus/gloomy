from gloomy import gloom, assign, delete

assert gloom({"a": {"b": {"c": [123]}}}, "a.b.c.0") == 123
assert gloom({}, "a.b.c", default=None) is None
assert assign({"a": {"b": {"c": [123]}}}, "a.b.c.0", 456) == {"a": {"b": {"c": [456]}}}
assert delete({"a": {"b": {"c": 1}, "d": 2}}, "a.b") == {"a": {"d": 2}}
