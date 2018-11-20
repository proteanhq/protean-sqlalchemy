========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |
        |
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|

.. |docs| image:: https://readthedocs.org/projects/protean-sqlalchemy/badge/?style=flat
    :target: https://readthedocs.org/projects/protean-sqlalchemy
    :alt: Documentation Status

.. |version| image:: https://img.shields.io/pypi/v/protean-sqlalchemy.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/protean-sqlalchemy

.. |wheel| image:: https://img.shields.io/pypi/wheel/protean-sqlalchemy.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/protean-sqlalchemy

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/protean-sqlalchemy.svg
    :alt: Supported versions
    :target: https://pypi.org/project/protean-sqlalchemy

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/protean-sqlalchemy.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/protean-sqlalchemy


.. end-badges

Protean Sqlalchemy Extension

* Free software: BSD 3-Clause License

Installation
============

::

    pip install protean-sqlalchemy

Documentation
=============

https://protean-sqlalchemy.readthedocs.io/

Development
===========

::

    pyenv virtualenv -p python3.6 3.6.5 protean-es-dev

To run the all tests run::

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
