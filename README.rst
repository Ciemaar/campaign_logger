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
        | |codacy| |codeclimate|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://app.readthedocs.org/projects/campaign-logger/badge/?style=flat
    :target: https://campaign-logger.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/Ciemaar/campaign_logger/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/Ciemaar/campaign_logger/actions

.. |requires| image:: https://requires.io/github/Ciemaar/campaign_logger/requirements.svg?branch=main
     :target: https://requires.io/github/Ciemaar/campaign_logger/requirements/?branch=main
     :alt: Requirements Status

.. |codacy| image:: https://app.codacy.com/project/badge/Grade/ab86dd91d20d43e0bc3c2a023e5ee061
    :target: https://app.codacy.com/gh/Ciemaar/campaign_logger/dashboard
    :alt: Codacy Code Quality Status

.. |codeclimate| image:: https://qlty.sh/gh/Ciemaar/projects/campaign_logger/maintainability.svg
   :target: https://qlty.sh/login?returnTo=%2Fgh%2FCiemaar%2Fprojects%2Fcampaign_logger
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

.. |commits-since| image:: https://img.shields.io/github/commits-since/Ciemaar/campaign_logger/v0.0.1.svg
    :alt: Commits since latest release
    :target: https://github.com/Ciemaar/campaign_logger/compare/v0.0.1...main




.. end-badges

A module to support interaction with `Campaign Logger <https://campaign-logger.com/>`_.
This library provides a Python client and CLI for the `Generator API <https://generator.campaign-logger.com/>`_.

* Free software: GNU Lesser General Public License v3 or later (LGPLv3+)

Installation
============

::

    pip install campaign-logger

You can also install the in-development version with::

    pip install https://github.com/Ciemaar/campaign_logger/archive/main.zip


Documentation
=============


https://campaign-logger.readthedocs.io/


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
