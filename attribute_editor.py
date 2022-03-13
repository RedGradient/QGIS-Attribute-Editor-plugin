# -*- coding: utf-8 -*-
import os.path
from typing import *

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import QLineEdit, QPushButton, QComboBox, QWidget
from qgis._core import *
from qgis.core import edit
from qgis.gui import QgsMapTool, QgsMapToolPan

from .RequirementsProvider import RequirementsProvider
# Initialize Qt resources from file resources.py
# Import the code for the dialog
from .attribute_editor_dialog import *


# CLASSIFIER = ET.parse(os.path.dirname(__file__) + '/RS/classifier.grq')
# RS = ET.parse(os.path.dirname(__file__) + '/RS/RS.mixml')
CLASSIFIER = RequirementsProvider("/RS/RS.mixml")


class PointTool(QgsMapTool):
    def __init__(self, parent, iface, canvas, mode: str):
        """
        :mode Can be 'normal' or 'switch'
        """
        self.parent = parent
        self.iface = iface
        # self.provider = RequirementsProvider("/RS/RS.mixml")
        self.old_attr_values = []
        self.input_widget_list = []  # needs for saving
        self.first_start = True
        self.changed_inputs = []
        self.combo_box_list = []
        self.mode = mode  # "normal" or "switch"

        self.mult_press_data = {"pressed_list": [], "current_index": 0}

        self.ctrl_pressed = False

        # set callback at first start
        if self.first_start:
            self.parent.saveBtn.clicked.connect(self.on_saveBtn_clicked)
            # self.parent.resetChangesBtn.clicked.connect(self.on_resetChangesBtn_clicked)

            if self.mode == "switch":
                self.parent.gotoRight.clicked.connect(self.on_gotoRight_click)
                self.parent.gotoLeft.clicked.connect(self.on_gotoLeft_click)

            self.first_start = False

        QgsMapTool.__init__(self, canvas)

    def keyPressEvent(self, event):
        # if event.modifiers() & Qt.ControlModifier:
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = True
            self.parent.ctrl_status.setText("CTRL нажат")

    def keyReleaseEvent(self, event):
        # if event.modifiers() & Qt.ControlModifier:
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False
            self.parent.ctrl_status.setText("CTRL не нажат")

    def canvasReleaseEvent(self, event):
        point = QgsGeometry.fromPointXY(event.mapPoint())
        pressed_features = self.get_features_in_geometry(point)
        layer = self.iface.activeLayer()

        # these should be removed anyway
        self.parent.table.setRowCount(0)
        self.old_attr_values = []
        self.changed_inputs = []

        # support selection with ctrl
        if self.mode == "normal":
            if not self.ctrl_pressed:
                layer.removeSelection()
                if len(pressed_features) == 0:
                    self.parent.table.setRowCount(0)
                    self.input_widget_list = []
                    return
        if self.mode == "switch":
            layer.removeSelection()

        # show dialog with choice of features if there are more than one feature on press point
        if len(pressed_features) > 1:
            self.mult_press_data.update({"pressed_list": pressed_features, "current_index": 0})
            # show dialog with layer selector
            self.feat_select_dlg = FeatureSelectDialog()
            for feature in pressed_features:
                btn = QPushButton()
                btn.setText(str(feature.attributes()[0]))
                btn.clicked.connect(self.on_select_feat_btn_clicked(feature))
                self.feat_select_dlg.featBox.insertWidget(-1, btn)

            self.feat_select_dlg.show()
            result = self.feat_select_dlg.exec_()
            return

        if len(pressed_features) < 2:
            if self.mode == "switch":
                return

        # select pressed features on the layer
        for feature in pressed_features:
            layer.select(feature.id())

        self.display_attrs(layer.selectedFeatures())

        if not self.parent.isVisible():
            self.parent.show()

    def on_select_feat_btn_clicked(self, feature) -> Callable:
        """It is callback for feature button in feature choice dialog. It gets feature and show it"""

        def closure():
            self.display_attrs([feature])
            self.iface.activeLayer().select(feature.id())
            # self.selected_features.append(feature)
            self.feat_select_dlg.reject()
            if not self.parent.isVisible():
                if self.mode == "switch":
                    list_length = len(self.mult_press_data["pressed_list"])
                    label_text = f"{1}/{list_length}"
                    self.parent.label.setText(label_text)
                self.parent.show()

        return closure

    def get_features_in_geometry(self, geometry) -> List:
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

    def clear_layout(self, layout) -> None:
        """Gets layout and clears it"""

        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def display_attrs(self, features: List) -> None:
        """Takes feature list and display their attributes"""

        # dict with item format "атрибут -> [список значений данного атрибута из всех features]"
        data = {}
        for feature in features:
            feature_attr_map = dict(zip(
                list(map(lambda f: f.displayName(), feature.fields())),
                feature.attributes()
            ))
            for item in list(feature_attr_map.items()):
                if item[0] in data:
                    data[item[0]].append(item[1])
                else:
                    data[item[0]] = [item[1]]

        # атрибут одинаковый для всех features => значение показывается
        # атрибуты разные для всех features => выводится '***'
        # атрибут пустой => выводится '-'
        for key in data:
            distinct_attrs = set(data[key])
            if len(distinct_attrs) > 1:
                data[key] = "***"
            elif list(distinct_attrs)[0] == "":
                data[key] = "-"
            else:
                data[key] = str(list(distinct_attrs)[0])

        # self.parent.table.setRowCount(len(data))
        # layer_ref = self.get_layer_ref(RS.getroot(), self.iface.activeLayer().name())
        # if layer_ref is None:
        #     widget = self.iface.messageBar().createMessage("Ошибка", "Слой не найден в системе требований")
        #     self.iface.messageBar().pushWidget(widget, Qgis.Warning)
        #     return
        # node = self.get_layer_node(RS.getroot(), layer_ref)
        # readable_values = self.get_readable_name(CLASSIFIER.find("Source/Classifier"), {})
        layer_name = self.iface.activeLayer().name()
        readable_values = CLASSIFIER.get_readable_names()
        meta: dict[str] = CLASSIFIER.get_fields_meta(layer_name)

        # show attributes
        self.combo_box_list = []
        self.input_widget_list = []
        self.no_field_list = []
        for i, item in enumerate(data.items()):
            label = CustomLabel(item[0])
            # input_widget = QWidget()

            field_data = meta.get(item[0])
            if field_data is not None:
                field_type = field_data["type"]
            else:
                self.no_field_list.append(item[0])
                continue

            if field_type in ["Char", "Int", "Decimal", "Date"]:
                input_widget = CustomLineEdit()
                if item[1] in ['-', '***']:
                    input_widget.setPlaceholderText(str(item[1]))
                    self.old_attr_values.append('')
                    input_widget.old_text = ''
                else:
                    input_widget.setText(item[1])
                    self.old_attr_values.append(str(item[1]))
                    input_widget.old_text = item[1]
                input_widget.textChanged.connect(self.on_textChanged(input_widget))

            elif field_type == "Dir":
                input_widget = CustomComboBox()
                input_widget.setEditable(True)

                attribute = item[0]

                variants = [""]
                input_widget.addItems([""])
                for code in meta[attribute]["choice_fullcode"]:
                    rv = readable_values[code]["code"]
                    input_widget.addItem(rv)
                    variants.append(rv)

                if item[1] in ['-', '***']:
                    input_widget.lineEdit().setPlaceholderText(str(item[1]))
                    self.old_attr_values.append('')
                    input_widget.old_text = ''
                else:
                    if item[1] in variants:
                        index = variants.index(item[1])
                        input_widget.setCurrentIndex(index)
                    else:
                        input_widget.setCurrentText(item[1])
                    self.old_attr_values.append(str(item[1]))
                    input_widget.old_text = item[1]

                input_widget.variants = variants
                self.combo_box_list.append(input_widget)
                self.show_invalid_inputs(input_widget.lineEdit(), variants)
                # input_widget.lineEdit().textEdited.connect(self.on_textEdited(input_widget.lineEdit()))
                # input_widget.lineEdit().textEdited.connect(
                #     self.show_invalid_inputs_callback(input_widget.lineEdit(), variants)
                # )
                input_widget.currentTextChanged.connect(
                    self.show_invalid_inputs_callback(input_widget.lineEdit(), variants)
                )

            elif field_type == "DirValue":
                input_widget = CustomComboBox()
                input_widget.setEditable(True)

                attribute = meta[item[0]]["fieldRef"]

                variants = [""]
                input_widget.addItem("")
                for code in meta[attribute]["choice_fullcode"]:
                    rv = readable_values[code]["text"]
                    input_widget.addItem(rv)
                    variants.append(rv)

                if item[1] in ['-', '***']:
                    input_widget.lineEdit().setPlaceholderText(str(item[1]))
                    self.old_attr_values.append('')
                    input_widget.old_text = ''
                else:
                    if item[1] in variants:
                        index = variants.index(item[1])
                        input_widget.setCurrentIndex(index)
                    else:
                        input_widget.setCurrentText(item[1])
                    self.old_attr_values.append(str(item[1]))
                    input_widget.old_text = item[1]

                input_widget.variants = variants
                self.show_invalid_inputs(input_widget.lineEdit(), variants)

                # set event handlers
                # input_widget.lineEdit().textEdited.connect(self.on_textEdited(input_widget.lineEdit()))
                # input_widget.lineEdit().textEdited.connect(
                #     self.show_invalid_inputs_callback(input_widget.lineEdit(), variants)
                # )
                input_widget.currentTextChanged.connect(
                    self.show_invalid_inputs_callback(input_widget.lineEdit(), variants)
                )

                self.combo_box_list[-1].currentIndexChanged.connect(
                    self.on_currentIndexChanged(self.combo_box_list[-1], input_widget)
                )
                input_widget.currentIndexChanged.connect(
                    self.on_currentIndexChanged(input_widget, self.combo_box_list[-1])
                )

            else:
                self.no_field_list.append(item[0])
                continue

            input_widget.label = label
            self.input_widget_list.append(input_widget)
            self.parent.table.setRowCount(self.parent.table.rowCount() + 1)
            self.parent.table.setRowHeight(i, 4)
            self.parent.table.setCellWidget(i, 0, label)
            self.parent.table.setCellWidget(i, 1, input_widget)

        self.parent.saveBtn.setEnabled(False)
        # self.parent.resetChangesBtn.setEnabled(False)
        if self.no_field_list:
            widget = self.iface.messageBar().createMessage(
                "Следующие атрибуты не показаны, т.к. отсутствуют в системе требований",
                str(tuple(self.no_field_list))
            )
            self.iface.messageBar().pushWidget(widget, Qgis.Warning)

    def on_gotoRight_click(self):
        index = self.mult_press_data["current_index"] + 1
        pressed_list = self.mult_press_data["pressed_list"]
        if index > len(pressed_list) - 1:
            return
        self.parent.label.setText(f"{index + 1}/{len(pressed_list)}")
        feature = pressed_list[index]
        self.mult_press_data["current_index"] += 1

        # select feature
        self.iface.activeLayer().removeSelection()
        layer = self.iface.activeLayer()
        layer.select(feature.id())

        self.display_attrs([feature])

    def on_gotoLeft_click(self):
        index = self.mult_press_data["current_index"] - 1
        if index < 0:
            return
        list_length = len(self.mult_press_data["pressed_list"])
        self.parent.label.setText(f"{index + 1}/{list_length}")
        feature = self.mult_press_data["pressed_list"][index]
        self.mult_press_data["current_index"] -= 1

        # select feature
        self.iface.activeLayer().removeSelection()
        layer = self.iface.activeLayer()
        layer.select(feature.id())

        self.display_attrs([feature])

    def on_textChanged(self, lineEdit: QLineEdit) -> Callable:
        def closure():
            if lineEdit.old_text != lineEdit.text():
                lineEdit.label.setChanged(True)
                self.parent.saveBtn.setEnabled(True)
                if lineEdit not in self.changed_inputs:
                    self.changed_inputs.append(lineEdit)
            else:
                lineEdit.label.setChanged(False)
                if lineEdit in self.changed_inputs:
                    self.changed_inputs.remove(lineEdit)
                if len(self.changed_inputs) == 0:
                    self.parent.saveBtn.setEnabled(False)

        return closure

    @staticmethod
    def get_changed_attrs(old_attrs: List, new_attrs: List) -> Dict:
        """Gets changed attributes"""
        result = {}
        index = -1
        for old, new in zip(old_attrs, new_attrs):
            index += 1
            if old != new:
                result[index] = new
        return result

    def on_saveBtn_clicked(self) -> None:
        """Saves changed attributes"""
        if not self.input_widget_list:
            return

        current_attr_values = []
        for widget in self.input_widget_list:
            """
            при некоторых условиях (неизвестно, каких) возникает RuntimeError из-за обращения к удаленному C++ 
            объекту - виджету; обращение происходит на строчке current_attr_values.append(widget.text());
            ошибка на сохранение не влияет
            """
            # if isinstance(widget, QLineEdit):
            #     try:
            #         current_attr_values.append(widget.text())
            #     except RuntimeError:
            #         pass
            # elif isinstance(widget, QComboBox):
            #     try:
            #         current_attr_values.append(widget.currentText())
            #     except RuntimeError:
            #         pass
            try:
                if isinstance(widget, QLineEdit):
                    current_attr_values.append(widget.text())
                elif isinstance(widget, QComboBox):
                    current_attr_values.append(widget.currentText())
                else:
                    raise Exception("Input widget has unknown type")
            except RuntimeError:
                pass
        new_attr_values = self.get_changed_attrs(self.old_attr_values, current_attr_values)

        layer = self.iface.activeLayer()
        with edit(layer):
            for feature in layer.selectedFeatures():
                # for feat_idx, new_value in new_attr_values.items():
                layer.changeAttributeValues(feature.id(), new_attr_values)
                if self.mode == "switch":
                    index = self.mult_press_data["current_index"]
                    self.mult_press_data["pressed_list"].remove(self.mult_press_data["pressed_list"][index])
                    self.mult_press_data["pressed_list"].insert(index, layer.selectedFeatures()[0])

        self.parent.saveBtn.setEnabled(False)
        # self.parent.resetChangesBtn.setEnabled(False)

    def on_currentIndexChanged(self, combo_box: QComboBox, other_combo_box: QComboBox) -> Callable:
        def closure(index: int):
            other_combo_box.setCurrentIndex(index)
            if combo_box.old_text != combo_box.currentText():
                combo_box.label.setChanged(True)
                self.parent.saveBtn.setEnabled(True)
                # self.parent.resetChangesBtn.setEnabled(True)
                if combo_box not in self.changed_inputs:
                    self.changed_inputs.append(combo_box)
            else:
                combo_box.label.setChanged(False)
                if combo_box in self.changed_inputs:
                    self.changed_inputs.remove(combo_box)
                if len(self.changed_inputs) == 0:
                    self.parent.saveBtn.setEnabled(False)
                    # self.parent.resetChangesBtn.setEnabled(False)

        return closure

    def on_resetChangesBtn_clicked(self) -> None:
        """Resets changes in input widgets to old values"""
        if len(self.changed_inputs) == 0:
            return None

        while self.changed_inputs:
            widget = self.changed_inputs.pop()
            if isinstance(widget, QLineEdit):
                widget.setText(widget.old_text)
            elif isinstance(widget, QComboBox):
                if widget.old_text in widget.variants:
                    index = widget.variants.index(widget.old_text)
                    widget.setCurrentIndex(index)
                else:
                    widget.setCurrentText(widget.old_text)
            widget.label.setChanged(False)

        self.parent.resetChangesBtn.setEnabled(False)
        self.parent.saveBtn.setEnabled(False)

    @staticmethod
    def is_correct(item: str, choice: List) -> bool:
        if item not in choice:
            return False
        return True

    def show_invalid_inputs(self, lineEdit: QLineEdit, choice: List) -> None:
        text = lineEdit.text()
        if not self.is_correct(text, choice):
            lineEdit.setDangerStyle()
        else:
            lineEdit.setNormalStyle()

    def show_invalid_inputs_callback(self, lineEdit: QLineEdit, choice: List) -> Callable:
        def closure():
            self.show_invalid_inputs(lineEdit, choice)

        return closure


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
        # locale = QSettings().value('locale/userLocale')[0:2]
        # locale_path = os.path.join(
        #     self.plugin_dir,
        #     'i18n',
        #     'AttributeEditor_{}.qm'.format(locale))
        #
        # if os.path.exists(locale_path):
        #     self.translator = QTranslator()
        #     self.translator.load(locale_path)
        #     QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = "Редактор атрибутов"
        # self.menu = self.tr(u'&Редактор атрибутов')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.mult_editor_first_start = None
        self.switch_editor_first_start = None

        self.normal_dlg = None
        self.switch_dlg = None

        self.switch_pressed = False
        self.normal_pressed = False

    # noinspection PyMethodMayBeStatic
    # def tr(self, message):
    #     """Get the translation for a string using Qt translation API.
    #
    #     We implement this ourselves since we do not inherit QObject.
    #
    #     :param message: String for translation.
    #     :type message: str, QString
    #
    #     :returns: Translated version of message.
    #     :rtype: QString
    #     """
    #     # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
    #     return QCoreApplication.translate('AttributeEditor', message)

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

        icon_path = ':/plugins/attribute_editor/icon.png'

        self.add_action(
            icon_path,
            text="Одиночное и множественное редактирование",
            callback=self.run_normal_mode,
            parent=self.iface.mainWindow()
        )

        self.add_action(
            icon_path,
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

        if self.switch_editor_first_start == True:
            self.switch_editor_first_start = False
            self.switch_dlg = AttributeEditorSwitchDialog()
            # self.switch_dlg.rejected.connect(self.on_switch_dlg_rejected)
            # установка "always on top" (не работает в Linux)
            self.switch_dlg.setWindowFlags(Qt.WindowStaysOnTopHint)

        if not self.actions[1].isChecked():
            self.canvas.setMapTool(QgsMapToolPan(self.canvas))
            if self.switch_dlg.isVisible():
                self.switch_dlg.reject()
            return
        self.actions[0].setChecked(False)

        # prelude
        self.switch_map_tool = PointTool(self.switch_dlg, self.iface, self.canvas, mode="switch")
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
        if self.mult_editor_first_start == True:
            self.mult_editor_first_start = False
            self.normal_dlg = AttributeEditorDialog(parent=self.iface.mainWindow())
            # self.normal_dlg.rejected.connect(self.on_normal_dlg_rejected)
            # установка "always on top" (не работает в Linux)
            # self.normal_dlg.setWindowFlags(Qt.WindowStaysOnTopHint)

        # on de-check: close window & unset tool
        if not self.actions[0].isChecked():
            self.canvas.setMapTool(QgsMapToolPan(self.canvas))
            if self.normal_dlg.isVisible():
                self.normal_dlg.reject()
            return
        self.actions[1].setChecked(False)

        self.normal_map_tool = PointTool(self.normal_dlg, self.iface, self.canvas, mode="normal")
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
