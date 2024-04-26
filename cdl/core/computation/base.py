# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
.. Common computation objects (see parent package :mod:`cdl.core.computation`)
"""

# pylint: disable=invalid-name  # Allows short reference names like x, y, ...

# Note:
# ----
# All dataset classes must also be imported in the cdl.core.computation.param module.

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Self, TypeVar

import guidata.dataset as gds
import numpy as np
import scipy.signal as sps

from cdl.config import _
from cdl.core.model.signal import create_signal

if TYPE_CHECKING:
    from cdl.core.model.image import ImageObj
    from cdl.core.model.signal import SignalObj


class GaussianParam(gds.DataSet):
    """Gaussian filter parameters"""

    sigma = gds.FloatItem("σ", default=1.0)


class MovingAverageParam(gds.DataSet):
    """Moving average parameters"""

    n = gds.IntItem(_("Size of the moving window"), default=3, min=1)


class MovingMedianParam(gds.DataSet):
    """Moving median parameters"""

    n = gds.IntItem(_("Size of the moving window"), default=3, min=1, even=False)


class ThresholdParam(gds.DataSet):
    """Threshold parameters"""

    value = gds.FloatItem(_("Threshold"))


class ClipParam(gds.DataSet):
    """Data clipping parameters"""

    value = gds.FloatItem(_("Clipping value"))


class HistogramParam(gds.DataSet):
    """Histogram parameters"""

    def get_suffix(self, data: np.ndarray) -> str:
        """Return suffix for the histogram computation

        Args:
            data: data array
        """
        suffix = f"bins={self.bins:d}"
        if self.lower is not None:
            suffix += f", ymin={self.lower:.3f}"
        else:
            self.lower = np.min(data)
        if self.upper is not None:
            suffix += f", ymax={self.upper:.3f}"
        else:
            self.upper = np.max(data)

    bins = gds.IntItem(_("Number of bins"), default=256, min=1)
    lower = gds.FloatItem(_("Lower limit"), default=None, check=False)
    upper = gds.FloatItem(_("Upper limit"), default=None, check=False)


class ROIDataParam(gds.DataSet):
    """ROI Editor data"""

    roidata = gds.FloatArrayItem(
        _("ROI data"),
        help=_(
            "For convenience, this item accepts a 2D NumPy array, a list of list "
            "of numbers, or None. In the end, the data is converted to a 2D NumPy "
            "array of integers (if not None)."
        ),
    )
    singleobj = gds.BoolItem(
        _("Single object"),
        help=_("Whether to extract the ROI as a single object or not."),
    )

    @property
    def is_empty(self) -> bool:
        """Return True if there is no ROI"""
        return self.roidata is None or np.array(self.roidata).size == 0


class FFTParam(gds.DataSet):
    """FFT parameters"""

    shift = gds.BoolItem(_("Shift"), help=_("Shift zero frequency to center"))


def new_signal_result(
    src: SignalObj | ImageObj,
    name: str,
    suffix: str | None = None,
    units: tuple[str, str] | None = None,
    labels: tuple[str, str] | None = None,
) -> SignalObj:
    """Create new signal object as a result of a compute_11 function

    As opposed to the `dst_11` functions, this function creates a new signal object
    without copying the original object metadata, except for the "source" entry.

    Args:
        src: input signal or image object
        name: name of the processing function
        suffix: suffix to add to the title
        units: units of the output signal
        labels: labels of the output signal

    Returns:
        Output signal object
    """
    title = f"{name}({src.short_id})"
    dst = create_signal(title=title, units=units, labels=labels)
    if suffix is not None:
        dst.title += "|" + suffix
    if "source" in src.metadata:
        dst.metadata["source"] = src.metadata["source"]  # Keep track of the source
    return dst
