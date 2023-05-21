# -*- coding: utf-8 -*-
#
# Copyright © 2022 Codra
# Pierre Raybaut

"""
Module providing test utilities
"""

from __future__ import annotations

import functools
import os
import os.path as osp
import pathlib
import subprocess
import sys
import tempfile
from collections.abc import Callable, Generator
from contextlib import contextmanager

from guidata.configtools import get_module_data_path

from cdl.env import execenv

TST_PATH = []


def add_test_path_from_env(envvar: str) -> None:
    """Appends test data path from environment variable (fails silently)"""
    path = os.environ.get(envvar)
    if path:
        TST_PATH.append(path)


def add_test_module_path(modname: str, relpath: str) -> None:
    """
    Appends test data path relative to a module name.
    Used to add module local data that resides in a module directory
    but will be shipped under sys.prefix / share/ ...

    modname must be the name of an already imported module as found in
    sys.modules
    """
    TST_PATH.append(get_module_data_path(modname, relpath=relpath))


def get_test_fnames(pattern: str) -> list[str]:
    """
    Return the absolute path list to test files with specified pattern

    Pattern may be a file name (basename), a wildcard (e.g. *.txt)...
    """
    pathlist = []
    for pth in TST_PATH:
        pathlist += sorted(pathlib.Path(pth).rglob(pattern))
    if not pathlist:
        raise FileNotFoundError(f"Test file(s) {pattern} not found")
    return [str(path) for path in pathlist]


def try_open_test_data(title: str, pattern: str) -> Callable:
    """Decorator handling test data opening"""

    def try_open_test_data_decorator(func: Callable) -> Callable:
        """Decorator handling test data opening"""

        @functools.wraps(func)
        def func_wrapper() -> None:
            """Decorator wrapper function"""
            execenv.print(title + ":")
            execenv.print("-" * len(title))
            try:
                for fname in get_test_fnames(pattern):
                    execenv.print(f"=> Opening: {fname}")
                    func(fname)
            except FileNotFoundError:
                execenv.print(f"  No test data available for {pattern}")
            finally:
                execenv.print(os.linesep)

        return func_wrapper

    return try_open_test_data_decorator


def get_default_test_name(suffix: str | None = None) -> str:
    """Return default test name based on script name"""
    name = osp.splitext(osp.basename(sys.argv[0]))[0]
    if suffix is not None:
        name += "_" + suffix
    return name


def get_output_data_path(extension: str, suffix: str | None = None) -> str:
    """Return full path for data file with extension, generated by a test script"""
    name = get_default_test_name(suffix)
    return osp.join(TST_PATH[0], f"{name}.{extension}")


@contextmanager
def temporary_directory() -> Generator[str, None, None]:
    """Create a temporary directory and clean-up afterwards"""
    #  TemporaryDirectory is not used within a "with" statement in order to ignore
    #  errors occuring when cleaning up directory at exit
    #  TODO: [P3] Requires Python 3.10 / Use "ignore_cleanup_errors=True" instead
    #  In other words: this function will be replaced by TemporaryDirectory context mgr
    tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
    try:
        yield tmp.name
    finally:
        try:
            tmp.cleanup()
        except (PermissionError, RecursionError):
            pass


def exec_script(
    path: str, wait: bool = True, args: str = "", env: dict[str, str] | None = None
) -> None:
    """Run test script.

    Args:
        path: path to script
        wait: wait for script to finish
        args: arguments to pass to script
        env: environment variables to pass to script
    """
    command = [sys.executable, '"' + path + '"']
    if args:
        command.append(args)
    stderr = subprocess.DEVNULL if execenv.unattended else None
    # pylint: disable=consider-using-with
    proc = subprocess.Popen(" ".join(command), shell=True, stderr=stderr, env=env)
    if wait:
        proc.wait()
