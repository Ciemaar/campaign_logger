##############
 Contributing
##############

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

*************
 Bug reports
*************

When `reporting a bug
<https://github.com/Ciemaar/campaign_logger/issues>`_ please include:

   -  Your operating system name and version.
   -  Any details about your local setup that might be helpful in
      troubleshooting.
   -  Detailed steps to reproduce the bug.

****************************
 Documentation improvements
****************************

Campaign Logger could always use more documentation, whether as part of
the official Campaign Logger docs, in docstrings, or even on the web in
blog posts, articles, and such.

*******************************
 Feature requests and feedback
*******************************

The best way to send feedback is to file an issue at
https://github.com/Ciemaar/campaign_logger/issues.

If you are proposing a feature:

-  Explain in detail how it would work.
-  Keep the scope as narrow as possible, to make it easier to implement.
-  Remember that this is a volunteer-driven project, and that code
   contributions are welcome :)

*************
 Development
*************

We strongly encourage the use of `pre-commit <https://pre-commit.com/>`_
to automatically run linting and code quality checks before each commit.

**Setting up pre-commit:**

#. Install pre-commit (if not already installed globally): `pip install
   pre-commit` or `uv pip install pre-commit`.
#. Install the git hook scripts: `pre-commit install`.
#. (Optional) Run against all files manually: `pre-commit run
   --all-files`.

If you cannot use pre-commit, you are responsible for manually running
the tools listed in `.pre-commit-config.yaml` (e.g., `ruff check .`,
`ruff format .`, `mdformat .`) prior to submitting your code.

To set up `campaign_logger` for local development:

#. Fork `campaign_logger <https://github.com/Ciemaar/campaign_logger>`_
   (look for the "Fork" button).

#. Clone your fork locally:

   .. code::

      git clone git@github.com:YOURGITHUBNAME/campaign_logger.git

#. Create a branch for local development:

   .. code::

      git checkout -b name-of-your-bugfix-or-feature

#. Set up a virtual environment. You can use standard `pip` and `venv`
   or the modern `uv` tool.

   **Using standard Python tools (venv and pip):**

   .. code:: bash

      python -m venv .venv
      source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
      pip install -e ".[test]"

   **Using uv (faster alternative):**

   .. code:: bash

      uv venv
      source .venv/bin/activate
      uv pip install -e ".[test]"

   Now you can make your changes locally.

#. Make sure to run the formatting and linting tools before submitting:

   .. code::

      ruff format .
      ruff check .
      pyright .

#. When you're done making changes, run all the checks and docs builder
   with `tox <https://tox.wiki/en/latest/installation.html>`_ in one
   command:

   .. code::

      tox

#. Commit your changes and push your branch to GitHub:

   .. code::

      git add .
      git commit -m "Your detailed description of your changes."
      git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

Pull Request Guidelines
=======================

If you need some code review or feedback while you're developing the
code just make the pull request.

For merging, you should:

#. Include passing tests (run ``tox``).
#. Update documentation when there's new API, functionality etc.
#. Add a note to ``CHANGELOG.rst`` about the changes.
#. Add yourself to ``AUTHORS.rst``.

Tips
====

To run a subset of tests:

.. code::

   tox -e envname -- pytest -k test_myfeature

To run all the test environments in *parallel*:

.. code::

   tox -p auto
