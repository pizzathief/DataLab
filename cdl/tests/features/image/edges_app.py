# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see cdl/LICENSE for details)

"""
Edges processing application test
"""

# pylint: disable=invalid-name  # Allows short reference names like x, y, ...

import cdl.param
from cdl.tests import cdl_app_context
from cdl.tests.data import get_test_image

SHOW = True  # Show test in GUI-based test launcher


def test():
    """Run edges processing application test scenario"""
    with cdl_app_context() as win:
        win.showMaximized()
        panel = win.imagepanel
        panel.add_object(get_test_image("flower.npy"))
        proc = panel.processor
        proc.compute_all_edges()
        panel.objview.select_groups([0])
        param = cdl.param.GridParam()
        param.cols = 4
        proc.distribute_on_grid(param)
        panel.add_label_with_title()


if __name__ == "__main__":
    test()
