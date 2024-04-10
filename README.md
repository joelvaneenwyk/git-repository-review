# Git Repository Review

[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/joelvaneenwyk/git-repository-review/actions/workflows/test-package.yaml/badge.svg)](https://github.com/joelvaneenwyk/git-repository-review/actions/workflows/test-package.yaml)

This is a general-purpose Python library for reviewing a Git repository to make sure it matches expected style settings and is not doing anything that is not cross-platform compatible.

To ensure code quality, several tools are configured:

- [mypy](https://mypy.readthedocs.io/en/stable/) for static type checking
- [ruff](https://github.com/astral-sh/ruff) as the linter and code formatter
- [codespell](https://github.com/codespell-project/codespell) to check spelling
- [pytest](https://docs.pytest.org/en/7.4.x/) as the test engine

In addition, [Git hooks](https://pre-commit.com/) can be used to guarantee consistency and leverage the aforementioned tools. The workflow [test-package.yaml](.github/workflows/test-package.yaml) runs them automatically for you.

The documentation is initialized with [Jupyter Books](https://jupyterbook.org/en/stable/intro.html), providing a promising approach for interactive tutorials.

## Quick Start

1. If you don't have poetry, [download and install Poetry](https://python-poetry.org/docs/#installation) following the instructions for your OS.
2. Clone your repository and make it your working directory.
3. To install the project, its development dependencies, and the pre-commit hooks, just run:

    ```bash
    poetry install
    poetry shell
    ```

4. The regular maintenance tasks are handled by [taskipy](https://github.com/taskipy/taskipy/tree/master).
You can see the available tasks by running:

    ```plain
    $ task --list
    pre_commit_install pre-commit install
    test               pytest
    pre_lint           task pre_commit_install
    lint               pre-commit run --all-files
    qa                 task lint && task test
    pre_docs           poetry install --with docs
    docs               jupyter-book build docs --path-output build
    pre_docs_serve     task pre_docs
    docs_serve         sphinx-autobuild docs build/_build/html
    wizard             python ./scripts/rename_project_content.py
    ```

    Type `task <task_name>` to run a task. For example, to run the tests, try `task test`.

5. Assert that everything is up and running:

    ```bash
    task qa
    ```

6. A helper script is included to rename the git username and project name from the template to your new project, try it with:

    ```bash
    task wizard
    ```

7. You can now review the changes, stage, and commit them on your repo. Run `task qa` another time to assert everything is still all right.

## Copyright and License

© 2024 [Joel Van Eenwyk](https://github.com/joelvaneenwyk).
© 2023 [Felipe N. Schuch](https://github.com/fschuch).

All content is under [MIT License](https://github.com/joelvaneenwyk/git-repository-review/blob/main/LICENSE).
