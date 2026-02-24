# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""
# This file is *not* meant to cover or endorse the use of nox, pytest, or
# testing in general,
#
# It's meant to show the use of:
#
# - check-manifest
#     Confirms items checked into VCS are in your source distribution (sdist).
# - readme_renderer (when using a reStructuredText README)
#     Ensures your long_description will render correctly on PyPI.
#
# Also, it is intended to help confirm pull requests to this project.
"""
import os

import nox

nox.options.sessions = ["lint"]


@nox.session
def lint(session):
    """
    Perform code style checking using flake8 for the session.

    This session installs flake8 and runs it on the codebase, excluding
    specific directories and files such as .nox, .egg, build, and data.
    It selects errors and warnings related to style (E), whitespace (W),
    and function errors (F).

    :param session: Current session
    :return: None
    """
    session.install("flake8")
    session.run(
        "flake8", "--exclude", ".nox,*.egg,build,data",
        "--select", "E,W,F", "."
    )


@nox.session
def build_and_check_dists(session):
    """
    Install necessary libraries for testing and execute build checks.

    This session installs the required dependencies like build,
    check-manifest, and twine. It also runs check-manifest to confirm that
    all files checked into version control are included in the source distribution,
    followed by running the build and twine check commands to ensure the package is valid.

    If the project uses a README in reStructuredText format, you can uncomment
    the session.install("readme_renderer") line.

    :param session: Current session
    :return: None
    """
    session.install("build", "check-manifest >= 0.42", "twine")
    # If your project uses README.rst, uncomment the following:
    # session.install("readme_renderer")

    session.run("check-manifest", "--ignore", ".flake8,noxfile.py,*.txt,tests/**")
    session.run("python", "-m", "build")
    session.run("python", "-m", "twine", "check", "dist/*")


@nox.session(python=["3.11", "3.12", "3.13", "3.14"])
def tests(session):
    """
    Run tests for Python versions 3.11, 3.12, 3.13, and 3.14.

    This session installs pytest, builds and checks the distributions,
    and runs the tests for the specified Python versions. It checks that the
    distributions were generated correctly and installs the generated distribution
    before running the tests.

    :param session: Current session
    :return: None
    """
    session.install("pytest")
    build_and_check_dists(session)

    generated_files = os.listdir("dist/")
    generated_sdist = os.path.join("dist/", generated_files[1])

    session.install(generated_sdist)

    session.run("py.test", "tests/", *session.posargs)
