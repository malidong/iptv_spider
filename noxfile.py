# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""
Nox automation for IPTV Spider testing and linting.

Supported Python versions: 3.11, 3.12, 3.13, 3.14
Nox version: 2024.x or later (compatible with Python 3.11+)

Sessions:
  - lint: Code style checking with flake8
  - build_and_check_dists: Build and distribution checks
  - tests: Run pytest for specified Python versions
"""
import os

import nox

# Default sessions to run
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
        "flake8", "--exclude", ".nox,.venv,*.egg,build,data",
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

    # Find generated distribution file
    dist_files = os.listdir("dist/")
    if len(dist_files) < 2:
        session.error("No distribution files generated. Build may have failed.")

    # Get the source distribution (.tar.gz)
    generated_sdist = None
    for f in dist_files:
        if f.endswith(".tar.gz"):
            generated_sdist = os.path.join("dist/", f)
            break

    if not generated_sdist:
        session.error("No .tar.gz distribution file found in dist/")

    session.install(generated_sdist)
    session.run("pytest", "tests/", *session.posargs)
