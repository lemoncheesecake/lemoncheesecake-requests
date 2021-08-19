#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(
    name="lemoncheesecake-requests",
    version="0.1.0",
    description="Test Storytelling",
    # long_description=open("README.rst").read(),
    author="Nicolas Delon",
    author_email="nicolas.delon@gmail.com",
    license="Apache License (Version 2.0)",
    # url="http://lemoncheesecake.io",
    classifiers=[
        # "Development Status :: 5 - Production/Stable",
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
    keywords="QA testing requests",
    project_urls={
        # 'Documentation': 'http://docs.lemoncheesecake.io/',
        # 'Source': 'https://github.com/lemoncheesecake/lemoncheesecake',
        # 'Tracker': 'https://github.com/lemoncheesecake/lemoncheesecake/issues',
    },

    packages=find_packages(),
    include_package_data=True,
    install_requires=("lemoncheesecake~=1.0", "requests~=2.20.0"),
)
