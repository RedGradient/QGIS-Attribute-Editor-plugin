# -*- coding: utf-8 -*-
import os.path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import QWidget
from qgis.gui import QgsMapToolPan

from .resources import *
from .pointtool import PointTool
from .req_provider import RequirementsProvider
from .attribute_editor_dialog import *


class AttributeEditor:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface

        self.canvas = self.iface.mapCanvas()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        self.actions = []
        self.menu = "Редактор атрибутов"

        # инструмент: флаг первого запуска
        self.mult_editor_first_start = True
        self.switch_editor_first_start = True

        # событие: снимаем нажатие с инструмента PointTool, если был выбран другой инструмент
        self.iface.mapCanvas().mapToolSet.connect(self.on_mapToolSet)

        # справочник
        self.classifier = RequirementsProvider("/RS/RS.mixml")

        # окна
        self.normal_dlg = None
        self.switch_dlg = None

        # кнопки инструментов: нажаты или нет
        self.switch_pressed = False
        self.normal_pressed = False

    def on_mapToolSet(self, new, old):
        """Снимает нажатие с инструмента PointTool, если был выбран другой инструмент"""
        if isinstance(old, PointTool) and not isinstance(new, PointTool):
            for action in self.actions:
                action.setChecked(False)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(True)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # icon_path = ':/plugins/attribute_editor/new_icon.png'

        normal_mode_icon = ':/plugins/attribute_editor/icons/normal_mode_icon.png'
        switch_mode_icon = ':/plugins/attribute_editor/icons/switch_mode_icon.png'

        self.add_action(
            normal_mode_icon,
            text="Одиночное и множественное редактирование",
            callback=self.run_normal_mode,
            parent=self.iface.mainWindow()
        )

        self.add_action(
            switch_mode_icon,
            text="Перечисление наложенных объектов",
            callback=self.run_switch_mode,
            parent=self.iface.mainWindow()
        )

        # will be set False in run()
        self.mult_editor_first_start = True
        self.switch_editor_first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                # self.tr(u'&Редактор атрибутов'),
                "Редактор атрибутов",
                action)
            self.iface.removeToolBarIcon(action)

    def run_switch_mode(self):
        layer = self.iface.activeLayer()
        if layer is None:
            # self.switch_pressed = False
            self.actions[1].setChecked(False)
            return
        # if layer has no geometry
        if layer.wkbType() == 100:
            self.actions[1].setChecked(False)
            print("Активный слой не имеет геометрии")
            return

        if self.switch_editor_first_start:
            self.switch_editor_first_start = False
            self.switch_dlg = AttributeEditorSwitchDialog()
            # self.switch_dlg.rejected.connect(self.on_switch_dlg_rejected)
            # установка "always on top" (не работает в Linux)
            self.switch_dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
            self.switch_map_tool = PointTool(self.switch_dlg, self.iface, self.canvas, self.classifier, mode="switch")

        if not self.actions[1].isChecked():
            self.canvas.setMapTool(QgsMapToolPan(self.canvas))
            if self.switch_dlg.isVisible():
                self.switch_dlg.reject()
            return
        self.actions[0].setChecked(False)

        # prelude
        # self.switch_map_tool = PointTool(self.switch_dlg, self.iface, self.canvas, self.classifier, mode="switch")
        self.canvas.setMapTool(self.switch_map_tool)

    def run_normal_mode(self):
        """Run method that performs all the real work"""
        layer = self.iface.activeLayer()
        if layer is None:
            # self.normal_pressed = False
            self.actions[0].setChecked(False)
            return

        # if layer has no geometry
        # QgsWkbTypes.Unknown
        if layer.wkbType() == 100:
            print("Активный слой не имеет геометрии")
            self.actions[0].setChecked(False)
            return

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.mult_editor_first_start:
            self.mult_editor_first_start = False
            self.normal_dlg = AttributeEditorDialog(parent=self.iface.mainWindow())
            # self.normal_dlg.rejected.connect(self.on_normal_dlg_rejected)
            # установка "always on top" (не работает в Linux)
            # self.normal_dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
            self.normal_map_tool = PointTool(self.normal_dlg, self.iface, self.canvas, self.classifier, mode="normal")

        # on de-check: close window & unset tool
        if not self.actions[0].isChecked():
            self.canvas.setMapTool(QgsMapToolPan(self.canvas))
            if self.normal_dlg.isVisible():
                self.normal_dlg.reject()
            return
        self.actions[1].setChecked(False)

        # self.normal_map_tool = PointTool(self.normal_dlg, self.iface, self.canvas, self.classifier, mode="normal")
        self.canvas.setMapTool(self.normal_map_tool)

        selected_features = list(self.iface.activeLayer().getSelectedFeatures())
        if len(selected_features) == 0:
            return

        # показываем атрибуты объектов, которые были выделены ДО открытия окна плагина
        self.normal_dlg.table.setRowCount(0)
        self.normal_map_tool.old_attr_values = []
        self.normal_map_tool.input_widget_list = []

        self.normal_map_tool.display_attrs(selected_features)

        # show the dialog
        self.normal_dlg.show()

        # Run the dialog event loop
        result = self.normal_dlg.exec_()

        # if result == 0:
        #     self.actions[0].setChecked(False)
        # self.canvas.setMapTool(QgsMapToolPan(self.canvas))
        # return
        # self.canvas.setMapTool(QgsMapToolPan(self.canvas))

    def on_switch_dlg_rejected(self):
        self.canvas.setMapTool(QgsMapToolPan(self.canvas))
        self.actions[1].setChecked(False)

    def on_normal_dlg_rejected(self):
        self.canvas.setMapTool(QgsMapToolPan(self.canvas))
        self.actions[0].setChecked(False)
