lemoncheesecake-requests
========================

.. image:: https://github.com/lemoncheesecake/lemoncheesecake-requests/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/lemoncheesecake/lemoncheesecake-requests/actions/workflows/tests.yml

.. image:: https://codecov.io/gh/lemoncheesecake/lemoncheesecake-requests/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/lemoncheesecake/lemoncheesecake-requests

.. image:: https://img.shields.io/pypi/v/lemoncheesecake-requests.svg
    :target: https://pypi.org/project/lemoncheesecake-requests/

.. image:: https://img.shields.io/pypi/pyversions/lemoncheesecake-requests.svg
    :target: https://pypi.org/project/lemoncheesecake-requests/

lemoncheesecake-requests provides logging facilities to `requests <https://docs.python-requests.org/>`_ for
tests written with the `lemoncheesecake <http://lemoncheesecake.io>`_ test framework.

In this example, we implement a very basic test on a Github API endpoint:

.. code-block:: python

   # suites/github.py

   import lemoncheesecake.api as lcc
   from lemoncheesecake.matching import *
   from lemoncheesecake_requests import Session, is_2xx

   @lcc.test()
   def get_org():
       session = Session(base_url="https://api.github.com")

       resp = session.get("/orgs/lemoncheesecake")
       resp.require_status_code(is_2xx())

       check_that_in(
           resp.json(),
           "id", is_integer(),
           "name", equal_to("lemoncheesecake")
       )


We run the test:

.. code-block:: console

   $ lcc.py run
   =================================== github ====================================
    OK  1 # github.get_org

   Statistics :
    * Duration: 0.214s
    * Tests: 1
    * Successes: 1 (100%)
    * Failures: 0

And here is the report details :

.. image:: https://github.com/lemoncheesecake/lemoncheesecake-requests/blob/master/doc/_static/report-sample.png?raw=true
    :alt: test result

Installation
------------

Install through pip:

.. code-block:: console

   $ pip install lemoncheesecake-requests

lemoncheesecake-requests is compatible with Python 3.7-3.10.

Features
--------

- request/response data logging into lemoncheesecake

- response status code checking using lemoncheesecake matching mechanism

Documentation
-------------

The documentation is available on https://lemoncheesecake-requests.readthedocs.io.


Contact
-------

Bug reports and improvement ideas are welcomed in tickets.
A Google Groups forum is also available for discussions about lemoncheesecake:
https://groups.google.com/forum/#!forum/lemoncheesecake.
