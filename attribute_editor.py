# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AttributeEditor
                                 A QGIS plugin
 Просмотр и редактирование атрибутов объекта
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-02-17
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Karo
        email                : example@mail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import QTableWidget, QTableWidgetItem, QLabel, QVBoxLayout, QLineEdit, QHBoxLayout
from qgis.gui import QgsMapTool
from qgis.core import QgsGeometry, QgsPointXY
from qgis._core import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .attribute_editor_dialog import AttributeEditorDialog
import os.path


class PointTool(QgsMapTool):   
    def __init__(self, parent, iface, canvas):
        self.line_edit_list = []
        self.parent = parent
        self.iface = iface

        self.first_start = True
        self.selected_features = []

        self.ctrl_pressed = False

        # set callback at first satrt
        if self.first_start:
            self.parent.saveBtn.clicked.connect(self.on_saveBtn_clicked)
            self.first_start = False

        QgsMapTool.__init__(self, canvas)

    def keyPressEvent(self, event):
        # if event.modifiers() & Qt.ControlModifier:
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = True
    
    def keyReleaseEvent(self, event):
        # if event.modifiers() & Qt.ControlModifier:
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False

    def canvasReleaseEvent(self, event):
        # определяем координаты клика
        point = QgsGeometry.fromPointXY(event.mapPoint())
        
        pressed_features = self.get_features_in_geometry(point)
        layer = self.iface.activeLayer()

        # widgets should be removed anyway
        self.clear_layout(self.parent.attrBox)
        
        # support selection with ctrl
        if not self.ctrl_pressed:
            layer.removeSelection()
            self.selected_features = []
            if len(pressed_features) == 0:
                self.clear_layout(self.parent.attrBox)
                self.line_edit_list = []
                # remove old saveBtn callback
                # self.parent.saveBtn.clicked.connect(lambda *args: None)
                # self.parent.saveBtn.clicked.disconnect()

                return None

        # select pressed features on the layer
        for feature in pressed_features:
            layer.select(feature.id())
            self.selected_features.append(feature)

        self.display_attrs(self.selected_features)

    def get_features_in_geometry(self, geometry):
        """Returns features in geometry"""

        # get active layer
        layer = self.iface.activeLayer()

        # list of found features
        result = []

        # iterate over features in the layer to find features that intersect the point
        layer_features = layer.getFeatures()
        for feature in layer_features:
            if geometry.intersects(feature.geometry()):
                result.append(feature)

        return result

    def clear_layout(self, layout):
        """Gets layout and clears it"""

        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def display_attrs(self, features):
        """Принимает список объектов и отображает их атрибуты"""


        # создаем словарь с объектами вида "атрибут -> [список значений данного атрибута из всех features]"
        data = {}
        for feature in features:
            feature_attr_map = feature.attributeMap()
            for item in list(feature_attr_map.items()):
                if item[0] in data:
                    data[item[0]].append(item[1])
                else:
                    data[item[0]] = [item[1]]

        # если значение конкретного атрибута одинаковы для всех features, то данное значение показывается
        # если значения конкретного атрибута неодинаковы для всех features, то напротив атрибута вместо зачения выводится '***'
        for key in data:
            distinct_attrs = set(data[key])
            if len(distinct_attrs) > 1:
                data[key] = "***"
            elif list(distinct_attrs)[0] == "":
                data[key] = "-"
            else:
                data[key] = str(list(distinct_attrs)[0])
      

        # TODO: снятие выделения по нажатию на выделенный объект с нажатым ctrl
        # TODO: после закрытия окна активный инструмент меняется на инструмент перемещения (иконка руки). Искать по запросу: "pyqgis activate tool"

        # list of QLineEdit widgets
        self.line_edit_list = []

        # show attributes
        for i, item in enumerate(data.items()):
            label = QLabel(item[0])
            line_edit = QLineEdit()
            line_edit.setTextMargins(2, 0, 2, 0)
            self.line_edit_list.append(line_edit)

            if item[1] == '-' or item[1] == '***':
                line_edit.setPlaceholderText(str(item[1]))
            else:
                line_edit.setText(str(item[1]))

            hbox = QHBoxLayout()
            hbox.insertWidget(-1, label)
            hbox.insertWidget(-1, line_edit)

            self.parent.attrBox.insertLayout(-1, hbox)


    def on_saveBtn_clicked(self):
        if len(self.line_edit_list) == 0:
            return None

        new_attr_values = []
        for widget in self.line_edit_list:
            new_attr_values.append(widget.text())

        # l.startEditing()
        # l.commitChanges()

        # self.iface.activeLayer().startEditing()
        for feature in self.selected_features:
            f_attr_map = feature.attributeMap()
            f_attr_values = feature.attributes()
            for i in 

            # for ...
                # self.iface.activeLayer().changeAttributeValue(feature.id(), feature.attribute().index(''))
        # self.iface.activeLayer().commitChanges()

        print("saved")

class AttributeEditor:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        self.canvas = self.iface.mapCanvas()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'AttributeEditor_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Редактор атрибутов')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('AttributeEditor', message)


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

        icon_path = ':/plugins/attribute_editor/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Редактор атрибутов'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Редактор атрибутов'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = AttributeEditorDialog()

        # установка "always on top" (не работает в Linux)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        self.map_tool = PointTool(self.dlg, self.iface, self.canvas)
        self.canvas.setMapTool(self.map_tool)

        # показываем атрибуты объектов, которые были выделены ДО открытия окна плагина
        selected_features = list(self.iface.activeLayer().getSelectedFeatures())
        self.map_tool.display_attrs(selected_features)

        # show the dialog
        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            print("OK")
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    # def set_map_tool(self):
    #     self.canvas.setMapTool(self.map_tool)
    
    # def unset_map_tool(self):
    #     self.map_tool.layer.canvas.unsetMapTool(self.map_tool)
        
    