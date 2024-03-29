.. _`api`:

API Reference
=============

API compatibility / stability
-----------------------------

lemoncheesecake-requests follows the well know `Semantic Versioning <https://semver.org/>`_ for its public API.
Since lemoncheesecake-requests is still on 0.y.z major version, API breaking changes might occur; it is then advised to
pin the version.

What is considered as "public" is everything documented on https://lemoncheesecake-requests.readthedocs.io.
Everything else is internal and is subject to changes at anytime.

.. module:: lemoncheesecake_requests


Session
-------

.. autoclass:: Session
    :members: base_url, logger, hint


Logger
------

.. autoclass:: Logger
    :members:


Response
--------

.. autoclass:: Response
    :members: check_status_code, check_ok, require_status_code, require_ok, assert_status_code, assert_ok,
        raise_unless_status_code, raise_unless_ok,
        check_header, require_header, assert_header,
        check_headers, require_headers, assert_headers,
        check_json, require_json, assert_json


Matchers
--------

.. autofunction:: is_2xx
.. autofunction:: is_3xx
.. autofunction:: is_4xx
.. autofunction:: is_5xx


Exceptions
----------

.. autoexception:: LemoncheesecakeRequestsException
.. autoexception:: StatusCodeMismatch
