========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |github-actions| |requires|
        | |coveralls| |codecov|
        | |scrutinizer| |codacy| |codeclimate|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/campaign_logger/badge/?style=flat
    :target: https://campaign_logger.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/andriod/campaign_logger/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/Ciemaar/campaign_logger/actions

.. |requires| image:: https://requires.io/github/Ciemaar/campaign_logger/requirements.svg?branch=main
    :alt: Requirements Status
    :target: https://requires.io/github/Ciemaar/campaign_logger/requirements/?branch=main

.. |coveralls| image:: https://coveralls.io/repos/Ciemaar/campaign_logger/badge.svg?branch=main&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/Ciemaar/campaign_logger

.. |codecov| image:: https://codecov.io/gh/Ciemaar/campaign_logger/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage Status
    :target: https://codecov.io/github/Ciemaar/campaign_logger

.. |codacy| image:: https://img.shields.io/codacy/grade/ab86dd91d20d43e0bc3c2a023e5ee061.svg
    :target: https://www.codacy.com/app/Ciemaar/campaign_logger
    :alt: Codacy Code Quality Status

.. |codeclimate| image:: https://codeclimate.com/github/Ciemaar/campaign_logger/badges/gpa.svg
   :target: https://codeclimate.com/github/Ciemaar/campaign_logger
   :alt: CodeClimate Quality Status

.. |version| image:: https://img.shields.io/pypi/v/campaign-logger.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/campaign-logger

.. |wheel| image:: https://img.shields.io/pypi/wheel/campaign-logger.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/campaign-logger

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/campaign-logger.svg
    :alt: Supported versions
    :target: https://pypi.org/project/campaign-logger

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/campaign-logger.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/campaign-logger

.. |commits-since| image:: https://img.shields.io/github/commits-since/Ciemaar/campaign_logger/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/Ciemaar/campaign_logger/compare/v0.0.0...main


.. |scrutinizer| image:: https://img.shields.io/scrutinizer/quality/g/Ciemaar/campaign_logger/main.svg
    :alt: Scrutinizer Status
    :target: https://scrutinizer-ci.com/g/Ciemaar/campaign_logger/


.. end-badges

A module to support interaction with campaign logger https://campaign-logger.com/.

* Free software: GNU Lesser General Public License v3 or later (LGPLv3+)

Installation
============

::

    pip install campaign-logger

You can also install the in-development version with::

    pip install https://github.com/Ciemaar/campaign_logger/archive/main.zip


Documentation
=============


https://campaign_logger.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
