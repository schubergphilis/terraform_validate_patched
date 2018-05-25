=====
Usage
=====


To develop on terraform_validate_patched:

.. code-block:: bash

    # The following commands require pipenv as a dependency

    # To lint the project
    _CI/scripts/lint

    # To execute the testing
    _CI/scripts/test

    # To create a graph of the package and dependency tree
    _CI/scripts/graph

    # To build a package of the project under the directory "dist/"
    _CI/scripts/build

    # To see the package version
    _CI/scipts/tag

    # To bump semantic versioning [major|minor|patch]
    _CI/scipts/tag major|minor|patch

    # To upload the project to a pypi repo if user and password is properly provided
    _CI/scripts/upload

    # To build the documentation of the project
    _CI/scripts/document



To use terraform_validate_patched in a project:

.. code-block:: python

    from terraform_validate_patched import Terraform_validate_patched
    terraform_validate_patched = Terraform_validate_patched()
