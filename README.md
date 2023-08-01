# Gauge API Steps

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENCE)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-31012/)
[![Gauge](https://img.shields.io/badge/Framework-Gauge-blue)](https://github.com/getgauge)
[![XPath](https://img.shields.io/badge/XPath-blue)](https://www.w3schools.com/xml/xpath_syntax.asp)
[![JSONPath](https://img.shields.io/badge/JSONPath-blue)](https://github.com/h2non/jsonpath-ng)

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

[Contributions are welcome](./docs/CONTRIBUTING.md).

## Placeholders and Expressions

Step parameters allow the use of placeholders, that can be defined in the environment properties files. Some steps also allow to set a placeholder value manually. Property keys act as placeholders, they are defined like "\${key}" and they will be replaced by its value if such a property key/value pair exists in any _env/\*/\*.properties_ file or within the execution scope.
Some steps include parameters, that allow **expressions**, that will be evaluated.
Examples of allowed expressions include: `=1` , `>1` , `<1` , `>=1` , `<=1`.

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

## Maintainers

[Maintainers](./docs/MAINTAINERS.md)
