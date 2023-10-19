# Configuration

The Configuration follows the [Gauge configuration](https://docs.gauge.org/configuration.html?os=linux&language=python&ide=vscode) approach.
The following properties are supported:

| Property | Type | Default | Description |
|--|--|--|--|
| `replace_whitespace_in_report` | string | `None` | The HTML report will cut multiple whitespace characters as well as leading and trailing whitespaces. This library cannot prevent that, but it can replace whitespace, f.i. by setting `replace_whitespace_in_report = •` |
