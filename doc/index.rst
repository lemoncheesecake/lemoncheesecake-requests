.. lemoncheesecake-requests documentation master file, created by
   sphinx-quickstart on Sun Aug 22 12:49:56 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

lemoncheesecake-requests
========================

lemoncheesecake-requests provides logging facilities when using `requests <https://docs.python-requests.org/>`_ in
tests using the `lemoncheesecake <http://lemoncheesecake.io>`_ test framework.

In this example, we implement a very basic Github API endpoint test::

   # suites/github.py file

   import lemoncheesecake.api as lcc
   from lemoncheesecake.matching import *
   from lemoncheesecake_requests import Session, Logger

   @lcc.test()
   def get_org():
       session = Session(base_url="https://api.github.com")

       resp = session.get("/orgs/lemoncheesecake")
       resp.require_ok()

       check_that_in(
           resp.json(),
           "id", is_integer(),
           "name", equal_to("lemoncheesecake")
       )


We run the test::

   $ lcc.py run
   =================================== github ====================================
    OK  1 # github.get_org

   Statistics :
    * Duration: 0.214s
    * Tests: 1
    * Successes: 1 (100%)
    * Failures: 0

And here is the report details :

.. image:: _static/report-sample.png

Installation
------------

Install through pip::

   $ pip install lemoncheesecake-requests

lemoncheesecake-requests is compatible with Python 3.6-3.9.

Features
--------

Session
~~~~~~~

lemoncheesecake-requests extends :py:class:`requests.Session` to add logging features through a
:py:class:`lemoncheesecake_requests.Logger` instance.

This logger which can be set session-wide (it is set to :py:func:`Logger.on() <lemoncheesecake_requests.Logger.on>`
by default)::

   session = Session(base_url="https://api.github.com", logger=Logger.no_headers())
   session.get("/orgs/lemoncheesecake")

or per method-wide::

   session = Session(base_url="https://api.github.com")
   session.get("/orgs/lemoncheesecake", logger=Logger.no_headers())

The :py:attr:`base_url <lemoncheesecake_requests.Session.base_url>` argument is optional and an
extra :py:attr:`hint <lemoncheesecake_requests.Session.hint>` argument is also available to provide more context in the
logs to the report reader.

As you might guess from the previous examples, the logger can be fine tuned to control exactly the HTTP request/response details
that will be logged through the following logger boolean attributes:

- :py:attr:`request_line_logging <lemoncheesecake_requests.Logger.request_line_logging>`
- :py:attr:`request_headers_logging <lemoncheesecake_requests.Logger.request_headers_logging>`
- :py:attr:`request_body_logging <lemoncheesecake_requests.Logger.request_body_logging>`
- :py:attr:`response_code_logging <lemoncheesecake_requests.Logger.response_code_logging>`
- :py:attr:`response_headers_logging <lemoncheesecake_requests.Logger.response_headers_logging>`
- :py:attr:`response_body_logging <lemoncheesecake_requests.Logger.response_body_logging>`

If you want for instance to create a logger that only logs data coming from the response::

   logger = Logger(
      request_line_logging=False
      request_headers_logging=False
      request_body_logging=False
   )

and then pass this logger to a session or to a specific HTTP method call.

The :py:class:`lemoncheesecake_requests.Logger` also provide class methods to easily create instances for common usage
cases:

- :py:func:`Logger.on() <lemoncheesecake_requests.Logger.on>`
- :py:func:`Logger.off() <lemoncheesecake_requests.Logger.off>`
- :py:func:`Logger.no_headers() <lemoncheesecake_requests.Logger.no_headers>`
- :py:func:`Logger.no_response_body() <lemoncheesecake_requests.Logger.no_response_body>`

HTTP request bodies and especially response bodies might be very large and make the final report unreadable.
That's why the logger will log the request/response bodies as attachment if their (serialized) content size
exceed a certain size. This size can be configured through the
:py:attr:`max_body_size <lemoncheesecake_requests.Logger.max_body_size>` logger attribute.

Response
~~~~~~~~

TODO

lemoncheesecake-requests interacts with requests by extending two classes: :py:class:`requests.Session` and
:py:class:`requests.Response`.