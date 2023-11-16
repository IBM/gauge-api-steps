# Gauge Steps

An overview of how to write Gauge specifications can be found [here](https://docs.gauge.org/writing-specifications.html?os=macos&language=python&ide=vscode).\
The following Gauge steps are implemented in this module:

## Overview

  - [Response CSRF header \<header>](#response-csrf-header-header)
  - [Request CSRF header \<header>](#request-csrf-header-header)
  - [Store \<key> \<value>](#Store-key-value)
  - [Print \<message>](#print-message)
  - [Pretty print \<json>](#pretty-print-json)
  - [Print placeholders](#print-placeholders)
  - [Append to \<file>: \<value>](#append-to-file-value)
  - [With header \<header>: \<value>](#with-header-header-value)
  - [With body \<body>](#with-body-body)
  - [Simulate response body: \<value>](#simulate-response-body-value)
  - [Request \<method> \<url>](#request-method-url)
  - [Assert status \<status\_code>](#assert-status-status_code)
  - [Assert header \<header>: \<value>](#assert-header-header-value)
  - [Assert jsonpath \<jsonpath> exists](#assert-jsonpath-jsonpath-exists)
  - [Assert xpath \<xpath> exists](#Assert-xpath-xpath-exists)
  - [Assert jsonpath \<jsonpath> exists \<expr>](#assert-jsonpath-jsonpath-exists-expr)
  - [Assert xpath \<xpath> exists \<expr>](#assert-xpath-xpath-exists-expr)
  - [Assert jsonpath \<jsonpath> contains \<text>](#assert-jsonpath-jsonpath-contains-text)
  - [Assert xpath \<xpath> contains \<text>](#assert-xpath-xpath-contains-text)
  - [Assert jsonpath \<jsonpath> does not contain \<text>](#assert-jsonpath-jsonpath-does-not-contain-text)
  - [Assert xpath \<xpath> does not contain \<text>](#assert-xpath-xpath-does-not-contain-text)
  - [Assert jsonpath \<jsonpath> = \<json\_value>](#assert-jsonpath-jsonpath--json_value)
  - [Assert xpath \<xpath> = \<xml\_value>](#assert-xpath-xpath--xml_value)
  - [Save jsonpath \<jsonpath> as \<key>](#save-jsonpath-jsonpath-as-key)
  - [Save xpath \<xpath> as \<key>](#save-xpath-xpath-as-key)
  - [Save file \<download>](#save-file-download)

## Response CSRF header \<header>

> \* Response CSRF header "X-CSRF-TOKEN"

Define the response header name, that holds the CSRF token, which should be used in subsequent requests.
A typical header for CSRF tokens is `X-CSRF-TOKEN`.
Use this step together with [Request CSRF header \<header>](#request-csrf-header-header) to also specify the request header, that should be used with the token.

## Request CSRF header \<header>

> \* Request CSRF header "X-CSRF-TOKEN"

The CSRF token, that has previously been stored with the step [Response CSRF header \<header>](#response-csrf-header-header), can be used to make calls with that token now. This step specifies the header name for requests.
A typical header for CSRF tokens is `X-CSRF-TOKEN`.

## Store \<key> \<value>

> \* Store "url" "\${domain}\${path}"

Store a placeholder value for later use. This can also be used to concatenate other placeholders, like values from API responses.


## Print \<message>

> \* Print "custom debug: Using these headers in requests: \${\_headers}"

Prints the specified text in the terminal output and into the report.

## Pretty print \<json>

> \* Pretty print "{\"key\": \"value\"}"

Pretty-prints the specified JSON value in the terminal output and into the report.

## Print placeholders

> \* Print placeholders

Prints the comprehensive list of placeholders in the terminal output and into the report. This includes every property in the used `*.env` files and the system properties.
This can be useful for debugging.

## Append to \<file>: \<value>

> \* Append to "reports/users.csv": "\${user_name},\${user_phone}"

This writes the value to the specified text file. The file must be located inside of the Gauge project.
The value is appended to the file, and does not overwrite it, even over multiple test runs.
Each append ends with a newline '\n' character.

## With header \<header>: \<value>

> \* With header "Authorization": "Basic dXNlcjpwYXNzd29yZA=="

Sets a custom HTTP header for the next request.

## With body \<body>

> \* With body "{\\"request-data\\": 5}"

Sets the body for the next request.

## Simulate response body: \<value>

> \* Simulate response body: "{\\"request-data\\": 5}"

Sets the response body for further assertion steps, without the need to make an actual request.
This can be helpful during test development, when playing around with XPath or JSONPath expressions.

## Request \<method> \<url>

> \* Request "GET" "http://localhost"

Execute the request to the server with the optionally previously defined headers and body.

## Assert status \<status\_code>

> \* Assert status "200"

Make sure the response status matches the expected status.

## Assert header \<header>: \<value>

> \* Assert header "content-type": "text/javascript"

Make sure that the defined header is present in the response.

## Assert jsonpath \<jsonpath> exists

> \* Assert jsonpath "$.resp[0].value" exists

Make sure that exactly one result has been found in the response body under the specified JSONPath.

## Assert xpath \<xpath> exists

> \* Assert xpath "//rsp[1]/elem[@color = 'green']" exists

Make sure that exactly one result has been found in the response body under the specified XPath.

## Assert jsonpath \<jsonpath> exists \<expr>

> \* Assert jsonpath "$.resp[0].value" exists ">=3"

Make sure that the specified amount of results has been found under the specified JSONPath. The `expr` param allows simple expressions to compare the number of results. See [Placeholders and Expressions](#placeholders-and-expressions).

## Assert xpath \<xpath> exists \<expr>

> \* Assert xpath "//rsp[1]/elem[@color = 'green']" exists "=2"

Make sure that the specified amount of results has been found under the specified XPath. The `expr` param allows simple expressions to compare the number of results. See [Placeholders and Expressions](#placeholders-and-expressions).

## Assert jsonpath \<jsonpath> contains \<text>

> \* Assert jsonpath ".$fox.jumps" contains "fence"

Make sure that the specified text is contained somewhere under the specified JSONPath. This is not as fine-grained as the corresponding XPath-step.

## Assert xpath \<xpath> contains \<text>

> \* Assert xpath "string(//fox/jumps)" contains "fence"

Make sure that the specified text is contained in the specified XPath. This differs slightly from the JSONPath version, as XPath allows finer expressions. Therefore, the XPath must return the specific element that includes the text or the text itself. Useful XPath functions in combination with this step are `string()` and `text()`.

## Assert jsonpath \<jsonpath> does not contain \<text>

> \* Assert jsonpath ".$fox.jumps" does not contain "dog"

Make sure that the specified text is not contained somewhere under the specified JSONPath. This is the inverted version of [Assert jsonpath \<jsonpath> contains \<text>](#assert-jsonpath-jsonpath-contains-text)

## Assert xpath \<xpath> does not contain \<text>

> \* Assert xpath "string(//fox/jumps)" does not contain "dog"

Make sure that the specified text is not contained somewhere under the specified XPath. This is the inverted version of [Assert xpath \<xpath> does not contain \<text>](#assert-xpath-xpath-contains-text)

## Assert jsonpath \<jsonpath> = \<json\_value>

> \* Assert jsonpath ".$fox.jumps" = "{\\"over\\": \\"fence\\"}"
> \* Assert jsonpath ".$fox.jumps.over" = "\\"fence\\""

Make sure, that the result of the JSONPath exactly matches the specified value. The value can be a simple type or a nested JSON structure.

## Assert xpath \<xpath> = \<xml\_value>

> \* Assert xpath "//fox/jumps" = "\<over>fence\</over>"

Make sure, that the result of the XPath exactly matches the specified value. The value can be a simple type or a nested XML structure.

## Save jsonpath \<jsonpath> as \<key>

> \* Save jsonpath ".$fox.jumps" as "obstacle"

Saves the result as a placeholder variable with the given name. That placeholder can be used afterwards in the same scenario.

## Save xpath \<xpath> as \<key>

> \* Save xpath "//fox/jumps" as "obstacle"

Saves the result as a placeholder variable with the given name. That placeholder can be used afterwards in the same scenario.

## Save file \<download>

> \* Save file "downloads/image.png"

Saves the response body as a file. The file must be inside the project directory.
