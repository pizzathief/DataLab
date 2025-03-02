# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
ROI editor
==========

The :mod:`cdl.core.gui.roieditor` module provides the ROI editor widgets
for signals and images.

Signal ROI editor
-----------------

.. autoclass:: SignalROIEditor
    :members:

Image ROI editor
----------------

.. autoclass:: ImageROIEditor
    :members:
"""

# pylint: disable=invalid-name  # Allows short reference names like x, y, ...

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic, TypeVar, Union

from guidata.configtools import get_icon
from guidata.qthelpers import add_actions, create_action
from plotpy.builder import make
from plotpy.interfaces import IImageItemType
from plotpy.items import (
    AnnotatedCircle,
    AnnotatedPolygon,
    AnnotatedRectangle,
    CurveItem,
    MaskedImageItem,
    ObjectInfo,
    XRangeSelection,
)
from plotpy.plot import PlotDialog, PlotManager
from plotpy.tools import CircleTool, HRangeTool, PolygonTool, RectangleTool
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

import cdl.obj as dlo
from cdl.config import Conf, _
from cdl.core.model.base import (
    TypeObj,
    TypePlotItem,
    TypeROI,
    TypeROIItem,
    configure_roi_item,
)
from cdl.core.model.image import CircularROI, PolygonalROI, RectangularROI
from cdl.core.model.signal import SegmentROI
from cdl.env import execenv
from cdl.obj import ImageObj, ImageROI, SignalObj, SignalROI

if TYPE_CHECKING:
    from plotpy.plot import BasePlot
    from plotpy.tools.base import InteractiveTool


def plot_item_to_single_roi(
    item: XRangeSelection | AnnotatedRectangle | AnnotatedCircle | AnnotatedPolygon,
) -> SegmentROI | CircularROI | RectangularROI | PolygonalROI:
    """Factory function to create a single ROI object from plot item

    Args:
        item: Plot item

    Returns:
        Single ROI object
    """
    if isinstance(item, XRangeSelection):
        cls = SegmentROI
    elif isinstance(item, AnnotatedRectangle):
        cls = RectangularROI
    elif isinstance(item, AnnotatedCircle):
        cls = CircularROI
    elif isinstance(item, AnnotatedPolygon):
        cls = PolygonalROI
    else:
        raise TypeError(f"Unsupported ROI item type: {type(item)}")
    return cls.from_plot_item(item)


ROI_EDITOR_TOOLBAR_ID = "roi_editor_toolbar"


def configure_roi_item_in_tool(shape, obj: dlo.SignalObj | dlo.ImageObj) -> None:
    """Configure ROI item in tool"""
    fmt = obj.get_metadata_option("format")
    configure_roi_item(shape, fmt, lbl=True, editable=True, option=obj.PREFIX)


def tool_activate(tool: InteractiveTool) -> None:
    """Tool activate"""
    plot = tool.get_active_plot()
    plot.select_some_items([])  # Deselect all items
    tool.activate()


def tool_setup_shape(shape: TypeROIItem, obj: dlo.SignalObj | dlo.ImageObj) -> None:
    """Tool setup shape"""
    shape.setTitle("ROI")
    configure_roi_item_in_tool(shape, obj)


class ROISegmentTool(HRangeTool):
    """ROI segment tool"""

    TITLE = _("Add ROI")
    ICON = "signal_roi.svg"

    def __init__(self, manager: PlotManager, obj: dlo.SignalObj) -> None:
        super().__init__(
            manager, switch_to_default_tool=True, toolbar_id=ROI_EDITOR_TOOLBAR_ID
        )
        self.roi = SegmentROI([0, 1], False)
        self.obj = obj
        self.activate = tool_activate

    def create_shape(self) -> XRangeSelection:
        """Create shape"""
        shape = self.roi.to_plot_item(self.obj)
        configure_roi_item_in_tool(shape, self.obj)
        shape.selected = True
        return shape


class ROIRectangleTool(RectangleTool):
    """ROI rectangle tool"""

    TITLE = _("Add rectangular ROI")
    ICON = "roi_new_rectangle.svg"

    def __init__(self, manager: PlotManager, obj: dlo.ImageObj) -> None:
        super().__init__(
            manager,
            switch_to_default_tool=True,
            toolbar_id=ROI_EDITOR_TOOLBAR_ID,
            setup_shape_cb=tool_setup_shape,
        )
        self.roi = RectangularROI([0, 0, 1, 1], True)
        self.obj = obj
        self.activate = tool_activate

    def create_shape(self) -> tuple[AnnotatedRectangle, int, int]:
        """Create shape"""
        item = self.roi.to_plot_item(self.obj)
        return item, 0, 2

    def setup_shape(self, shape: AnnotatedRectangle) -> None:
        """Setup shape"""
        tool_setup_shape(shape, self.obj)


class ROICircleTool(CircleTool):
    """ROI circle tool"""

    TITLE = _("Add circular ROI")
    ICON = "roi_new_circle.svg"

    def __init__(self, manager: PlotManager, obj: dlo.ImageObj) -> None:
        super().__init__(
            manager,
            switch_to_default_tool=True,
            toolbar_id=ROI_EDITOR_TOOLBAR_ID,
            setup_shape_cb=tool_setup_shape,
        )
        self.roi = CircularROI([0, 0, 1], True)
        self.obj = obj
        self.activate = tool_activate

    def create_shape(self) -> tuple[AnnotatedCircle, int, int]:
        """Create shape"""
        item = self.roi.to_plot_item(self.obj)
        return item, 0, 1

    def setup_shape(self, shape: AnnotatedCircle) -> None:
        """Setup shape"""
        tool_setup_shape(shape, self.obj)


class ROIPolygonTool(PolygonTool):
    """ROI polygon tool"""

    TITLE = _("Add polygonal ROI")
    ICON = "roi_new_polygon.svg"

    def __init__(self, manager: PlotManager, obj: dlo.ImageObj) -> None:
        super().__init__(
            manager,
            switch_to_default_tool=True,
            toolbar_id=ROI_EDITOR_TOOLBAR_ID,
            setup_shape_cb=tool_setup_shape,
        )
        self.roi = PolygonalROI([[0, 0], [1, 0], [1, 1], [0, 1]], True)
        self.obj = obj
        self.activate = tool_activate

    def create_shape(self) -> tuple[AnnotatedPolygon, int, int]:
        """Create shape"""
        return self.roi.to_plot_item(self.obj)

    def setup_shape(self, shape: AnnotatedPolygon) -> None:
        """Setup shape"""
        tool_setup_shape(shape, self.obj)


TypeROIEditor = TypeVar("TypeROIEditor", bound="BaseROIEditor")


class BaseROIEditorMeta(type(QW.QWidget), abc.ABCMeta):
    """Mixed metaclass to avoid conflicts"""


class BaseROIEditor(
    QW.QWidget,
    Generic[TypeObj, TypeROI, TypePlotItem, TypeROIItem],
    metaclass=BaseROIEditorMeta,
):
    """ROI Editor"""

    ICON_NAME = None
    OBJ_NAME = None
    ROI_ITEM_TYPES = ()

    def __init__(
        self,
        parent: PlotDialog,
        obj: TypeObj,
        extract: bool,
        item: TypePlotItem | None = None,
    ) -> None:
        super().__init__(parent)
        self.plot_dialog = parent
        parent.accepted.connect(self.dialog_accepted)
        self.plot = parent.get_plot()
        self.toolbar = QW.QToolBar(self)
        self.obj = obj
        self.extract = extract
        self.__modified: bool | None = None

        roi = obj.roi
        if roi is None:
            roi = self.get_obj_roi_class()()
        self.__roi: TypeROI = roi

        fmt = obj.get_metadata_option("format")
        self.roi_items: list[TypeROIItem] = list(
            self.__roi.iterate_roi_items(obj, fmt, True, True)
        )

        self.add_tools_to_plot_dialog()
        item = obj.make_item() if item is None else item
        item.set_selectable(False)
        item.set_readonly(True)
        self.plot.add_item(item)
        for roi_item in self.roi_items:
            self.plot.add_item(roi_item)
            self.plot.set_active_item(roi_item)

        self.remove_all_action: QW.QAction | None = None
        self.singleobj_btn: QW.QToolButton | None = None

        self.setup_widget()

        # force update of ROI titles and remove_all_btn state
        self.items_changed(self.plot)

        self.plot.SIG_ITEMS_CHANGED.connect(self.items_changed)
        self.plot.SIG_ITEM_REMOVED.connect(self.item_removed)
        self.plot.SIG_RANGE_CHANGED.connect(lambda _rng, _min, _max: self.item_moved())
        self.plot.SIG_ANNOTATION_CHANGED.connect(lambda _plt: self.item_moved())

        #  In "extract mode", the dialog box OK button should always been enabled
        #  when at least one ROI is defined,
        #  whereas in non-extract mode (when editing ROIs) the OK button is by default
        #  disabled (until ROI data is modified)
        if extract:
            self.modified = len(self.roi_items) > 0
        else:
            self.modified = False

    @abc.abstractmethod
    def get_obj_roi_class(self) -> type[TypeROI]:
        """Get object ROI class"""

    @abc.abstractmethod
    def add_tools_to_plot_dialog(self) -> None:
        """Add tools to plot dialog"""

    @property
    def modified(self) -> bool:
        """Return dialog modified state"""
        return self.__modified

    @modified.setter
    def modified(self, value: bool) -> None:
        """Set dialog modified state"""
        self.__modified = value
        if self.extract:
            #  In "extract mode", OK button is enabled when at least one ROI is defined
            value = value and len(self.roi_items) > 0
        self.plot_dialog.button_box.button(QW.QDialogButtonBox.Ok).setEnabled(value)

    def dialog_accepted(self) -> None:
        """Parent dialog was accepted: updating ROI Editor data"""
        self.__roi.empty()
        for roi_item in self.roi_items:
            self.__roi.add_roi(plot_item_to_single_roi(roi_item))
        if self.singleobj_btn is not None:
            singleobj = self.singleobj_btn.isChecked()
            self.__roi.singleobj = singleobj
            Conf.proc.extract_roi_singleobj.set(singleobj)

    def get_roieditor_results(self) -> tuple[TypeROI, bool]:
        """Get ROI editor results

        Returns:
            A tuple containing the ROI data parameters and ROI modified state.
            ROI modified state is True if the ROI data has been modified within
            the dialog box.
        """
        return self.__roi, self.modified

    def create_actions(self) -> list[QW.QAction]:
        """Create actions"""
        self.remove_all_action = create_action(
            self,
            _("Remove all ROIs"),
            icon=get_icon("roi_delete.svg"),
            triggered=self.remove_all_rois,
        )
        return [None, self.remove_all_action]

    def setup_widget(self) -> None:
        """Setup ROI editor widget"""
        layout = QW.QHBoxLayout()
        self.toolbar.setToolButtonStyle(QC.Qt.ToolButtonTextUnderIcon)
        add_actions(self.toolbar, self.create_actions())
        layout.addWidget(self.toolbar)
        if self.extract:
            self.singleobj_btn = QW.QCheckBox(
                _("Extract all ROIs into a single %s object") % self.OBJ_NAME,
                self,
            )
            layout.addWidget(self.singleobj_btn)
            self.singleobj_btn.setChecked(self.__roi.singleobj)
        layout.addStretch()
        self.setLayout(layout)

    def remove_all_rois(self) -> None:
        """Remove all ROIs"""
        if (
            execenv.unattended
            or QW.QMessageBox.question(
                self,
                _("Remove all ROIs"),
                _("Are you sure you want to remove all ROIs?"),
            )
            == QW.QMessageBox.Yes
        ):
            self.plot.del_items(self.roi_items)

    @abc.abstractmethod
    def update_roi_titles(self) -> None:
        """Update ROI annotation titles"""

    def update_roi_items(self) -> None:
        """Update ROI items"""
        old_nb_items = len(self.roi_items)
        self.roi_items = [
            item
            for item in self.plot.get_items()
            if isinstance(item, self.ROI_ITEM_TYPES)
        ]
        self.plot.select_some_items([])
        self.update_roi_titles()
        if old_nb_items != len(self.roi_items):
            self.modified = True

    def items_changed(self, _plot: BasePlot) -> None:
        """Items have changed"""
        self.update_roi_items()
        self.remove_all_action.setEnabled(len(self.roi_items) > 0)

    def item_removed(self, item) -> None:
        """Item was removed. Since all items are read-only except ROIs...
        this must be an ROI."""
        assert item in self.roi_items
        self.update_roi_items()
        self.modified = True

    def item_moved(self) -> None:
        """ROI plot item has just been moved"""
        self.modified = True


class ROIRangeInfo(ObjectInfo):
    """ObjectInfo for ROI selection"""

    def __init__(self, roi_items) -> None:
        self.roi_items = roi_items

    def get_text(self) -> str:
        textlist = []
        for index, roi_item in enumerate(self.roi_items):
            x0, x1 = roi_item.get_range()
            textlist.append(f"ROI{index:02d}: {x0} ≤ x ≤ {x1}")
        return "<br>".join(textlist)


class SignalROIEditor(BaseROIEditor[SignalObj, SignalROI, CurveItem, XRangeSelection]):
    """Signal ROI Editor"""

    ICON_NAME = "signal_roi.svg"
    OBJ_NAME = _("signal")
    ROI_ITEM_TYPES = (XRangeSelection,)

    def get_obj_roi_class(self) -> type[SignalROI]:
        """Get object ROI class"""
        return SignalROI

    def add_tools_to_plot_dialog(self) -> None:
        """Add tools to plot dialog"""
        mgr = self.plot_dialog.get_manager()
        mgr.add_toolbar(self.toolbar, ROI_EDITOR_TOOLBAR_ID)
        mgr.add_tool(ROISegmentTool, self.obj)

    def setup_widget(self) -> None:
        """Setup ROI editor widget"""
        super().setup_widget()
        info = ROIRangeInfo(self.roi_items)
        info_label = make.info_label("BL", info, title=_("Regions of interest"))
        self.plot.add_item(info_label)
        self.info_label = info_label

    def update_roi_titles(self):
        """Update ROI annotation titles"""
        super().update_roi_titles()
        self.info_label.update_text()


class ImageROIEditor(
    BaseROIEditor[
        ImageObj,
        ImageROI,
        MaskedImageItem,
        # `Union` is mandatory here for Python 3.9-3.10 compatibility:
        Union[AnnotatedPolygon, AnnotatedRectangle, AnnotatedCircle],
    ]
):
    """Image ROI Editor"""

    ICON_NAME = "image_roi.svg"
    OBJ_NAME = _("image")
    ROI_ITEM_TYPES = (AnnotatedRectangle, AnnotatedCircle, AnnotatedPolygon)

    def get_obj_roi_class(self) -> type[ImageROI]:
        """Get object ROI class"""
        return ImageROI

    def add_tools_to_plot_dialog(self) -> None:
        """Add tools to plot dialog"""
        mgr = self.plot_dialog.get_manager()
        mgr.add_toolbar(self.toolbar, ROI_EDITOR_TOOLBAR_ID)
        mgr.add_tool(ROIRectangleTool, self.obj)
        mgr.add_tool(ROICircleTool, self.obj)
        mgr.add_tool(ROIPolygonTool, self.obj)

    def setup_widget(self) -> None:
        """Setup ROI editor widget"""
        super().setup_widget()
        item: MaskedImageItem = self.plot.get_items(item_type=IImageItemType)[0]
        item.set_mask_visible(False)

    def update_roi_titles(self) -> None:
        """Update ROI annotation titles"""
        super().update_roi_titles()
        for index, roi_item in enumerate(self.roi_items):
            roi_item: AnnotatedRectangle | AnnotatedCircle | AnnotatedPolygon
            roi_item.annotationparam.title = f"ROI{index:02d}"
            roi_item.annotationparam.update_item(roi_item)
