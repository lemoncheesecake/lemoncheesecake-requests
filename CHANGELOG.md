# 0.4.0 (2023-01-23)

- Add the following new methods to the `Response` class:
  - `check_header`
  - `require_header`
  - `assert_header`
  - `check_headers`
  - `require_headers`
  - `assert_headers`
  - `check_json`
  - `require_json`
  - `assert_json`

# 0.3.0 (2022-05-04)

- Improve `is_Nxx` matcher descriptions (for instance `is between 200 and 299` becomes `is 2xx`)
- Improve the way the content-type hint is displayed in request & response bodies
- Fix wrong URL formatting when the `params` argument contains multivalued parameters (simply use the full URL already
  computed by requests through `PreparedRequest`)
- Drop Python 3.6 support

# 0.2.1 (2021-11-10)

- Fix incorrect dependencies

# 0.2.0 (2021-10-06)

- Add `Logger.debug` to control whether logging is done with 'debug' or 'info' level
- Add official support for Python 3.10

# 0.1.1 (2021-09-27)

- Fix possible duplicated query string parameters in logged URLs

# 0.1.0 (2021-08-29)

- First release
