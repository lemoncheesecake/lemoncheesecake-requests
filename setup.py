#!/usr/bin/env python3

import os.path as osp
from setuptools import setup, find_packages


top_dir = osp.abspath(osp.dirname(__file__))

info = {}
with open(osp.join(top_dir, "lemoncheesecake_requests", "__version__.py")) as fh:
    exec(fh.read(), info)

setup(
    name="lemoncheesecake-requests",
    version=info["__version__"],
    description="Test Storytelling for requests",
    long_description=open(osp.join(top_dir, "README.rst")).read(),
    author="Nicolas Delon",
    author_email="nicolas.delon@gmail.com",
    license="Apache License (Version 2.0)",
    url="https://lemoncheesecake-requests.readthedocs.io",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    keywords="QA testing lemoncheesecake requests",
    project_urls={
        'Documentation': 'https://lemoncheesecake-requests.readthedocs.io.',
        'Source': 'https://github.com/lemoncheesecake/lemoncheesecake-requests',
        'Tracker': 'https://github.com/lemoncheesecake/lemoncheesecake-requests/issues',
    },

    packages=find_packages(),
    install_requires=("lemoncheesecake~=1.6", "requests~=2.23.0")
)
