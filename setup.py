#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")) as fh:
        return fh.read()


setup(
    name="campaign-logger",
    version="0.0.1",
    license="LGPL-3.0-or-later",
    description="A module to support interaction with campaign logger https://campaign-logger.com/.",
    long_description="{}\n{}".format(
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub("", read("README.rst")),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst")),
    ),
    author="Andy Fundinger",
    author_email="andy@ciemaar.com",
    url="https://github.com/Ciemaar/campaign_logger",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Utilities",
    ],
    project_urls={
        "Documentation": "https://campaign_logger.readthedocs.io/",
        "Changelog": "https://campaign_logger.readthedocs.io/en/latest/changelog.html",
        "Issue Tracker": "https://github.com/Ciemaar/campaign_logger/issues",
    },
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires=">=3.11",
    install_requires=[
        "click",
        "requests",
        "pydantic>=2.0",
    ],
    extras_require={
        "test": ["requests-mock", "pytest", "pytest-cov", "pytest-mock"],
    },
    entry_points={
        "console_scripts": [
            "campaign-logger = campaign_logger.cli:main",
        ]
    },
)
