# Configuration

The Configuration follows the [Gauge configuration](https://docs.gauge.org/configuration.html?os=linux&language=python&ide=vscode) approach.
The following properties are supported:

| Property | Type | Default | Description |
|--|--|--|--|
| `lenient_json_str_comparison` | bool | `false` | JSON strings have double quotes `"`. If this flag is set to `true`, the double quotes are optional for string comparisons. Thus, it would be possible to write: `* Assert jsonpath "$.text" = "text content"` instead of `* Assert jsonpath "$.text" = "\"text content\""` |
| `replace_whitespace_in_report` | string | `None` | The HTML report will cut multiple whitespace characters as well as leading and trailing whitespaces. This library cannot prevent that, but it can replace whitespace, f.i. by setting `replace_whitespace_in_report = •` |
| `session_properties` | string | `env/default/session.properties` | Session properties will be persisted in this file. They are then available over multiple test runs. This applies to:  <ul><li>`key`-parameters in steps, that look like "Store .. as \<key>" or "Save .. as \<key>"</li><li>CSRF response header values</li></ul> |
