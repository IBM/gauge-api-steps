# Configuration

The Configuration follows the [Gauge configuration](https://docs.gauge.org/configuration.html?os=linux&language=python&ide=vscode) approach.
The following properties are supported:

| Property | Type | Default | Description |
|--|--|--|--|
| `report_request` | bool | `false` | Print request information into the console and report. |
| `report_response` | bool | `false` | Print response information into the console and report. |
| `lenient_json_str_comparison` | bool | `false` | JSON strings have double quotes `"`. If this flag is set to `true`, the double quotes are optional for string comparisons. Thus, it would be possible to write: `* Assert jsonpath "$.text" = "text content"` instead of `* Assert jsonpath "$.text" = "\"text content\""` |
| `replace_whitespace_in_console` | string | `None` | The console and log output will cut multiple whitespace characters as well as leading and trailing whitespaces. This library cannot prevent that, but it can replace whitespace, f.i. by setting `replace_whitespace_in_console = •` |
| `session_properties` | string | `env/default/session.properties` | Session properties will be persisted in this file. They are then available over multiple test runs. This applies to:  <ul><li>`key`-parameters in steps, that look like "Store .. as \<key>" or "Save .. as \<key>"</li><li>CSRF response header values</li></ul> |
| `follow_redirects` | bool | `false` | Follow HTTP redirects (HTTP status codes 301, 302, 303, 307). This configuration can also be changed inside a scenario with [* Store "follow_redirects" = "True" in scenario](../docs/STEPS.md#store-key--value-in-scenario) |
| `mask_secrets` | string | `None` | This property should list any other properties or environment variables, that contain secrets. Those will be masked with `********` in the console and report. Separate with comma and/or space. |
