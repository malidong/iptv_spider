# pylint: disable=line-too-long
"""
# this file is *not* meant to cover or endorse the use of nox or pytest or
# testing in general,
#
#  It's meant to show the use of:
#
#  - check-manifest
#     confirm items checked into vcs are in your sdist
#  - readme_renderer (when using a reStructuredText README)
#     confirms your long_description will render correctly on PyPI.
#
#  and also to help confirm pull requests to this project.
"""
import os

import nox

nox.options.sessions = ["lint"]

# Define the minimal nox version required to run
nox.options.needs_version = ">= 2024.3.2"


@nox.session
def lint(session):
    """
    针对session用flake8进行代码规范性检测。
    :param session: current session
    :return:
    """
    session.install("flake8")
    session.run(
        "flake8", "--exclude", ".nox,*.egg,build,data",
        "--select", "E,W,F", "."
    )


@nox.session
def build_and_check_dists(session):
    """
    在session中安装测试需要的库并执行build测试。
    :param session:
    :return:
    """
    session.install("build", "check-manifest >= 0.42", "twine")
    # If your project uses README.rst, uncomment the following:
    # session.install("readme_renderer")

    session.run("check-manifest", "--ignore", ".flake8,noxfile.py,tests/**")
    session.run("python", "-m", "build")
    session.run("python", "-m", "twine", "check", "dist/*")


@nox.session(python=["3.11", "3.12", "3.13"])
def tests(session):
    """
    针对3.11, 3.12, 3.13版本的Python进行测试。
    :param session: current session
    :return:
    """
    session.install("pytest")
    build_and_check_dists(session)

    generated_files = os.listdir("dist/")
    generated_sdist = os.path.join("dist/", generated_files[1])

    session.install(generated_sdist)

    session.run("py.test", "tests/", *session.posargs)
