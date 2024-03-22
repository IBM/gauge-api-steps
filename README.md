# Gauge API Steps

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENCE)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-31012/)
[![Gauge](https://img.shields.io/badge/Framework-Gauge-blue)](https://github.com/getgauge)
[![XPath](https://img.shields.io/badge/XPath-blue)](https://www.w3schools.com/xml/xpath_syntax.asp)
[![JSONPath](https://img.shields.io/badge/JSONPath-blue)](https://github.com/h2non/jsonpath-ng)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/IBM/gauge-api-steps/badge)](https://securityscorecards.dev/viewer/?uri=github.com/IBM/gauge-api-steps)

A Python module, that provides re-usable steps for testing APIs with the [Gauge](https://gauge.org/) framework.

## Description

This is an extensible and flexible test-automation library for [Gauge](https://gauge.org). It enables users with and without programming knowledge to create end-to-end test scenarios in [Markdown](https://www.markdownguide.org/) syntax. Developers can still easily extend their test scenarios with custom code. Python's `urllib` is used to make requests against APIs. XML and JSON are supported and API responses can be validated with XPath and JSONPath.

## Gauge Step Overview

Find the documentation on all Gauge steps of this project in the overview:

[Gauge Step Overview](./docs/STEPS.md)

## Quick Start

This is a library for the Gauge framework, so Gauge+Python must be installed first.

* Install Python >= 3.10 on your platform and make it available in the \$PATH
* Install [Gauge](https://docs.gauge.org/getting_started/installing-gauge.html?language=python&ide=vscode) and [create a test project with Python](https://docs.gauge.org/getting_started/create-test-project.html?os=macos&language=python&ide=vscode)

It is useful to understand the basic workings of Gauge first. The [documentation](https://docs.gauge.org/?os=macos&language=python&ide=vscode) is excellent.

* Install [this module](#installation)
* Find out the path to this module after installation:
  ```shell
  echo $( python -m site --user-site )/gauge_api_steps
  ```
* Add that path to the property `STEP_IMPL_DIR` inside the test project file `env/default/python.properties`. Paths to multiple modules are comma separated.\
  Example on a Mac:
  ```
  STEP_IMPL_DIR = /Users/<user>/Library/Python/3.10/lib/python/site-packages/gauge_api_steps, step_impl
  ```
* Reload Visual Studio Code
* Write a new scenario in `specs/example.spec`. VSC offers **auto-completion**

## Installation

This module can be installed from source:

```shell
cd path/to/gauge-api-steps
pip install --user .
```

Or the latest package can be downloaded and installed from [PyPi](https://pypi.org/project/gauge-api-steps):

```shell
pip install gauge-api-steps --user --upgrade
```

## Development

When coding on this project, unit tests can be executed like this:

```shell
python -m unittest discover -v -s tests/ -p 'test_*.py'
```

[Contributions are welcome](./docs/CONTRIBUTING.md).

## Expressions in Parameters

### Property Placeholders

Step parameters allow the use of placeholders, that can be defined in the Gauge environment properties files. Some steps also allow to set a placeholder value manually. Property keys act as placeholders, they are defined like `${key}`. They will be replaced by its value if such a property key/value pair exists in any _env/\*/\*.properties_ file or within the execution scope.

### Mathematical Expressions

Mathematical expressions can also be evaluated. For example: `#{5 + 5 * 5}` is evaluated to `30`.

It is possible to combine the two features. Placeholder substitution takes place before mathematical expression evaluation.

### Functional Expressions

Functional expressions will generate a result during step execution. There are different expressions:
* UUID generation: `!{uuid}`
* Time: `!{time}`, `!{time:%Y-%m-%d}`. The time format is optional. If omitted, ISO format will be used. The time format pattern is described in the [Python language documentation](https://docs.python.org/3.10/library/time.html#time.strftime).
* Load content from text file: `!{file:resources/file.json}` The File must be inside the project directory.
* Load graphQL from file: `!{gql:resources/file.gql}` or `!{graphql:resources/file.gql}` This will automatically generate the JSON format, that can be used in the request body.


### Expression Examples

Note that the property expressions start with `$`, mathematical expressions with `#`, and functional expressions with `!`.

The property "homepage_url" can be defined in _env/default/test.properties_ like this:

> homepage_url = https://my-app.net

> \* Request "GET" "\${homepage_url}/home"

> \* Print "5 + 6 = #{5 + 6}"

It is also possible to define a property in a step:

> \* Store "addend" "5"

> \* Print "5 + 5 * 5 = #{$addend + 5 * 5}"

And also to create new properties from old:

> \* Store "new\_url" "${base_url}/id=!{uuid}&created=!{time}"

> \* Print "!{uuid}"

> \* Print "!{time}"

> \* Print "!{time:%Y-%m-%d}"

> \* With body "!{file:resources/request.json}"

> \* With body "!{file:resources/request.xml}"

> \* With body "!{gql:resources/request.gql}"

### Internal Placeholders

Following placeholders are used internally to store data over multiple steps:

* \_opener
* \_response\_csrf\_header
* \_request\_csrf\_header
* \_csrf\_value
* \_body
* \_response
* \_headers

It is possible to access and manipulate them with certain steps.

## Configuration

The Configuration follows the [Gauge configuration](https://docs.gauge.org/configuration.html?os=linux&language=python&ide=vscode) approach.
Some behaviour can be determined with properties.

[Configuration Overview](./docs/CONFIG.md)

## Maintainers

[Maintainers](./docs/MAINTAINERS.md)
