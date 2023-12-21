# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see cdl/LICENSE for details)

"""
DataLab Miscelleneous utilities
"""

from __future__ import annotations

import os.path as osp
import re
import subprocess

from cdl.config import Conf, get_mod_source_dir


def go_to_error(text: str) -> None:
    """Go to error: open file and go to line number.

    Args:
        text (str): Error text
    """
    pattern = r'File "(.+)", line (\d+),'
    match = re.search(pattern, text)
    if match:
        path = match.group(1)
        line_number = match.group(2)
        mod_src_dir = get_mod_source_dir()
        if not osp.isfile(path) and mod_src_dir is not None:
            otherpath = osp.join(mod_src_dir, path)
            if not osp.isfile(otherpath):
                # TODO: [P3] For frozen app, go to error is implemented only when the
                # source code is available locally (development mode).
                # How about using a web browser to open the source code on github?
                return
            path = otherpath
        if not osp.isfile(path):
            return  # File not found (unhandled case)
        fdict = {"path": path, "line_number": line_number}
        args = Conf.console.external_editor_args.get().format(**fdict).split(" ")
        editor_path = Conf.console.external_editor_path.get()
        subprocess.run([editor_path] + args, shell=True, check=False)


def is_version_at_least(version1: str, version2: str) -> bool:
    """
    Compare two version strings to check if the first version is at least
    equal to the second.

    Args:
        version1 (str): The first version string.
        version2 (str): The second version string.

    Returns:
        bool: True if version1 is greater than or equal to version2, False otherwise.
    """
    # Split the version strings into parts
    parts1 = [int(part) for part in version1.split(".")]
    parts2 = [int(part) for part in version2.split(".")]

    # Compare each part
    for part1, part2 in zip(parts1, parts2):
        if part1 > part2:
            return True
        elif part1 < part2:
            return False

    # Check if version1 is shorter and thus less than version2
    return len(parts1) >= len(parts2)
