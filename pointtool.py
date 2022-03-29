# -*- coding: utf-8 -*-
from typing import *

from qgis.PyQt.QtWidgets import QLineEdit, QPushButton, QComboBox
from qgis.core import *
from qgis.gui import QgsMapTool

from .attribute_editor_dialog import *


class PointTool(QgsMapTool):
    def __init__(self, parent, iface, canvas, classifier, mode: str):
        """Constructor.

        :param mode: Can be 'normal' or 'switch'
        """
        self.classifier = classifier
        self.parent = parent
        self.iface = iface
        # self.provider = RequirementsProvider("/RS/RS.mixml")
        self.old_attr_values = []
        self.input_widget_list = []  # needs for saving
        self.first_start = True
        self.changed_inputs = []
        self.combo_box_list = []
        self.mode = mode

        self.mult_press_data = {"pressed_list": [], "current_index": 0}

        self.ctrl_pressed = False

        # set callback at first start
        if self.first_start:
            # print('Произошло присваивание коллбека событию save')
            self.parent.saveBtn.clicked.connect(self.on_saveBtn_clicked)
            # self.parent.resetChangesBtn.clicked.connect(self.on_resetChangesBtn_clicked)
            if self.mode == "switch":
                self.parent.gotoRight.clicked.connect(self.on_gotoRight_click)
                self.parent.gotoLeft.clicked.connect(self.on_gotoLeft_click)
            elif self.mode == "normal":
                self.parent.temp_tool.clicked.connect(self.on_temp_tool_clicked)

            self.first_start = False

        QgsMapTool.__init__(self, canvas)

    def on_temp_tool_clicked(self):
        layer = self.iface.activeLayer()
        self.display_attrs(layer.selectedFeatures())

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
        # print("pixel:", event.pixelPoint().x(), event.pixelPoint().y())

        if self.mode == "normal" and self.iface.activeLayer().wkbType() == QgsWkbTypes.Polygon:
            point = QgsGeometry.fromPointXY(event.mapPoint())
            pressed_features = self.get_features_in_geometry(point)
        else:
            radius = 17
            origin = event.pixelPoint()

            # алиас для длинной функции
            toMapCoordinates = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates
            a1 = toMapCoordinates(int(origin.x() - radius / 2), int(origin.y() - radius / 2))
            a2 = toMapCoordinates(int(origin.x() + radius / 2), int(origin.y() - radius / 2))
            a3 = toMapCoordinates(int(origin.x() + radius / 2), int(origin.y() + radius / 2))
            a4 = toMapCoordinates(int(origin.x() - radius / 2), int(origin.y() + radius / 2))

            area = QgsGeometry.fromPolygonXY([[a1, a2, a3, a4]])

            pressed_features = self.get_features_in_geometry(area)

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
                    self.parent.selected_object_count.setText("Кол-во выбранных объектов: 0")
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
        layer_name = self.iface.activeLayer().name()
        self.parent.setWindowTitle(f"{layer_name} — Слой")

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

        if self.classifier.get_layer_ref(layer_name) is None:
            widget = self.iface.messageBar().createMessage("Ошибка", "Слой не найден в системе требований")
            self.iface.messageBar().pushWidget(widget, Qgis.Warning)
            return
        readable_values = self.classifier.get_readable_names()
        meta: dict[str] = self.classifier.get_fields_meta(layer_name)

        self.parent.table.setRowCount(len(data))

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
            input_widget.layer = self.iface.activeLayer()
            self.input_widget_list.append(input_widget)

            self.parent.table.setRowHeight(i, 4)
            self.parent.table.setCellWidget(i, 0, label)
            self.parent.table.setCellWidget(i, 1, input_widget)

        if hasattr(self.parent, "selected_object_count"):
            self.parent.selected_object_count.setText(f"Кол-во выбранных объектов: {len(features)}")
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
        # print('Длина self.input_widget_list при сохранении --', len(self.input_widget_list))
        for i, widget in enumerate(self.input_widget_list):
            """
            при некоторых условиях (неизвестно, каких) возникает RuntimeError из-за обращения к удаленному C++ 
            объекту - виджету; обращение происходит на строчке current_attr_values.append(widget.text());
            ошибка на сохранение не влияет
            """
            # try:
            if isinstance(widget, QLineEdit):
                current_attr_values.append(widget.text())
                widget.old_text = widget.text()
                # self.old_attr_values[i] = widget.text()
            elif isinstance(widget, QComboBox):
                current_attr_values.append(widget.currentText())
                widget.old_text = widget.currentText()
                # self.old_attr_values[i] = widget.currentText()
            else:
                raise Exception("Input widget has unknown type")
            # except RuntimeError:
            #     print('RuntimeError')
                # pass
        new_attr_values = self.get_changed_attrs(self.old_attr_values, current_attr_values)
        # print(new_attr_values)

        # layer = self.iface.activeLayer()
        layer = self.input_widget_list[0].layer

        # ---
        current_attr_values = dict(zip([i for i in range(len(current_attr_values))], current_attr_values))
        # ---

        edit_mode_was_active = layer.isEditable()
        if not edit_mode_was_active:
            layer.startEditing()

        for feature in layer.selectedFeatures():
            layer.changeAttributeValues(feature.id(), current_attr_values)
            if self.mode == "switch":
                index = self.mult_press_data["current_index"]
                self.mult_press_data["pressed_list"].remove(self.mult_press_data["pressed_list"][index])
                self.mult_press_data["pressed_list"].insert(index, layer.selectedFeatures()[0])

        if not edit_mode_was_active:
            layer.commitChanges()

        # self.old_attr_values = current_attr_values

        self.parent.saveBtn.setEnabled(False)
        # self.parent.resetChangesBtn.setEnabled(False)

    def on_currentIndexChanged(self, combo_box: QComboBox, other_combo_box: QComboBox) -> Callable:
        def closure(index: int) -> None:
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
