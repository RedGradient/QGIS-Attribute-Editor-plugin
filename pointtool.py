# -*- coding: utf-8 -*-
from typing import Callable, List, Dict

from qgis.PyQt import QtCore
from qgis.PyQt.QtCore import Qt, QPoint
from qgis.PyQt.QtGui import QIntValidator, QColor
from qgis.PyQt.QtWidgets import QLineEdit, QComboBox, QListWidgetItem
from qgis.core import *
from qgis.gui import QgsMapTool

from .attribute_editor_dialog import (FeatureSelectDialog,
                                      CustomLineEdit,
                                      CustomComboBox,
                                      CustomTableItem)


# TODO: исправить формат даты:
#  - в редакторе
#  - в диалоге

# TODO: увеличить ширину item-ов в диалоге

# TODO: реализовать выделение перетягиванием

# TODO: выделять объект подсветкой границ; это может привести к

# TODO: появление редактора после создания объекта


class PointTool(QgsMapTool):
    def __init__(self, parent, iface, canvas, classifier, mode: str):
        """Конструктор.

        :param mode: Может быть 'normal' или 'switch'
        """
        self.classifier = classifier    # система требований
        self.parent = parent            # ссылка на QDialog
        self.iface = iface

        # храним значения старых атрибутов
        # это нужно, чтобы уметь отличить новые атрибуты и выделить их жирным
        self.old_attr_values = []

        self.input_widget_list = []     # список input-ов
        self.first_start = True         # флаг первого запуска
        self.changed_inputs = []        # отслеживаем только измененные input-ы
        self.combo_box_list = []        # список QComboBox-ов
        self.mode = mode                # режим инструмента

        self.no_field_list = []

        self.indexes = {}

        # (только для 'switch' режима)
        # храним список объектов, по которым будем переключаться
        self.mult_press_data = {'pressed_list': [], 'current_index': 0}

        # задаем обратные вызовы при первом старте
        if self.first_start:
            self.parent.save_btn.clicked.connect(self.on_save_btn_clicked)
            # self.parent.resetChangesBtn.clicked.connect(self.on_resetChangesBtn_clicked)
            if self.mode == 'normal':
                self.parent.update_btn.clicked.connect(
                    self.on_update_btn_clicked
                )
            elif self.mode == 'switch':
                # обратные вызовы для кнопок вправо-влево
                self.parent.gotoRight.clicked.connect(self.on_gotoRight_click)
                self.parent.gotoLeft.clicked.connect(self.on_gotoLeft_click)
            else:
                raise Exception(f"Неизвестный режим инструмента: {self.mode}")

            # создание и обновление индекса
            self.parent.create_update_index_btn.clicked.connect(self.on_create_update_index_btn)

            self.first_start = False

        QgsMapTool.__init__(self, canvas)

    def on_create_update_index_btn(self):
        """Обрабатывает нажатие на кнопку 'Создать/Обновить индекс'"""
        layer = self.iface.activeLayer()

        # if self.indexes.get(layer.id()) is not None:
        #     self.parent.create_update_index_btn.setEnabled(False)
        #     return

        print(f"Создание индекса для слоя {layer.name()}...")
        index = QgsSpatialIndex(layer.getFeatures())
        self.indexes[layer.id()] = index
        print("Индекс создан!")

    def on_update_index_btn(self):
        pass

    def on_update_btn_clicked(self):
        layer = self.iface.activeLayer()
        self.display_attrs(layer.selectedFeatures())

    def canvasReleaseEvent(self, event):
        """Обрабатывает нажатие на карту"""
        layer = self.iface.activeLayer()

        # выбираем радиус окружности буфера
        if layer.wkbType() == QgsWkbTypes.Polygon:
            radius = 5
        else:
            radius = 8.5

        point = QgsGeometry.fromQPointF(event.pixelPoint())
        buffer = point.buffer(distance=radius, segments=10)

        vertices = []

        # переводим из пиксельных координат в координаты карты
        canvas = self.iface.mapCanvas()
        for vert in buffer.vertices():
            # переводим из пиксельных координат в координаты слоя
            point = QgsMapTool(canvas).toLayerCoordinates(
                layer,
                QPoint(int(vert.x()), int(vert.y()))
            )
            vertices.append(point)

        area = QgsGeometry.fromPolygonXY([vertices])

        pressed_features = self.get_features_in_geometry(area)

        # these should be removed anyway
        self.parent.table.setRowCount(0)
        self.old_attr_values = []
        self.changed_inputs = []

        layer.removeSelection()
        if len(pressed_features) == 0:
            self.parent.table.setRowCount(0)
            self.input_widget_list = []
            if hasattr(self.parent, 'selected_object_count'):
                self.parent.selected_object_count.setText('Выбрано объектов: 0')
            return
        if self.mode == 'switch':
            layer.removeSelection()

        # show dialog with choice of features if there are more than one feature on press point
        if len(pressed_features) > 1:
            self.mult_press_data.update({'pressed_list': pressed_features, 'current_index': 0})
            # show dialog with layer selector
            self.feat_select_dlg = FeatureSelectDialog()

            # храним состояние зебры
            color_code = {True: '#ffffff', False: '#f4f4f4'}
            color_code_status = True

            for feature in pressed_features:
                # элемент списка
                item = QListWidgetItem()

                # задаем текст и данные
                if len(feature.attributes()) > 0:
                    item.setText(str(feature.attributes()[0]))
                else:
                    item.setText(str(feature.id()))
                item.setData(QtCore.Qt.UserRole, feature)

                # выравнивание
                item.setTextAlignment(QtCore.Qt.AlignHCenter)

                # зебра
                color = QColor(color_code[color_code_status])
                color_code_status = not color_code_status
                item.setBackground(color)

                # задаем размер шрифта
                font = item.font()
                font.setPointSize(14)
                item.setFont(font)

                self.feat_select_dlg.list.addItem(item)

            self.feat_select_dlg.list.itemClicked.connect(self.on_select_feat_btn_clicked())

            self.feat_select_dlg.show()
            result = self.feat_select_dlg.exec_()
            return

        if len(pressed_features) < 2:
            if self.mode == 'switch':
                return

        # select pressed features on the layer
        for feature in pressed_features:
            layer.select(feature.id())

        self.display_attrs(layer.selectedFeatures())

        if not self.parent.isVisible():
            self.parent.show()

    def on_select_feat_btn_clicked(self) -> Callable:
        """Возвращает обратный вызов для кнопки, нажатой в диалоге выбора объекта.
        Сам обратный вызов возвращает нажатый объект типа QgsFeature"""

        def closure(item):
            feature = item.data(QtCore.Qt.UserRole)
            self.display_attrs([feature])
            self.iface.activeLayer().select(feature.id())
            self.feat_select_dlg.reject()
            if not self.parent.isVisible():
                if self.mode == 'switch':
                    list_length = len(self.mult_press_data['pressed_list'])
                    label_text = f"{1}/{list_length}"
                    self.parent.label.setText(label_text)
                self.parent.show()

        return closure

    def get_features_in_geometry(self, geometry) -> list:
        """Returns features in geometry"""

        # активный слой
        layer = self.iface.activeLayer()

        # если для этого слоя есть индекс и разрешено использование индекса
        if (self.indexes.get(layer.id()) is not None and
                self.parent.use_index_chb.isChecked()):
            index = self.indexes[layer.id()]
            candidates = index.intersects(geometry.boundingBox())
            req = QgsFeatureRequest().setFilterFids(candidates)
        else:
            req = QgsFeatureRequest().setFilterRect(geometry.boundingBox())

        result = []
        for feature in layer.getFeatures(req):
            if feature.geometry().intersects(geometry):
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

    def display_attrs(self, features: list) -> None:
        """Takes feature list and display their attributes"""

        # задаем заголовок диалога соответственно названию слоя
        layer_name = self.iface.activeLayer().name()
        self.parent.setWindowTitle(f"{layer_name} — Слой")

        # создаем словарь {атрибут: [список значений данного атрибута из всех features]}
        data = {}
        for feature in features:
            attr_map = feature.attributeMap()
            for attr, value in attr_map.items():
                data.setdefault(attr, []).append(value)

        """
        атрибут одинаковый для всех выбранных features -> значение показывается;
        атрибуты разные для всех выбранных features -> выводится "***";
        атрибут пустой -> выводится "-"
        """
        for key in data:
            unique_attrs = set(data[key])
            if len(unique_attrs) > 1:
                data[key] = '***'
            elif list(unique_attrs)[0] == '':
                data[key] = '-'
            else:
                data[key] = str(list(unique_attrs)[0])

        # если слой отсутствует в системе требований
        if self.classifier.get_layer_ref(layer_name) is None:

            self.parent.table.setRowCount(len(data))

            self.combo_box_list = []
            self.input_widget_list = []
            for i, item in enumerate(data.items()):
                # распаковываем item для читаемости кода
                attribute_name, display_value = item

                label = CustomTableItem(attribute_name)

                input_widget = CustomLineEdit()
                if item[1] in ['-', '***']:
                    input_widget.setPlaceholderText(str(display_value))
                    self.old_attr_values.append('')
                    input_widget.old_text = ''
                else:
                    input_widget.setText(display_value)
                    self.old_attr_values.append(str(display_value))
                    input_widget.old_text = display_value

                input_widget.label = label
                input_widget.layer = self.iface.activeLayer()
                self.input_widget_list.append(input_widget)

                self.parent.table.addRow(i, label, input_widget)
                self.parent.save_btn.setEnabled(True)

            if hasattr(self.parent, 'selected_object_count'):
                self.parent.selected_object_count.setText(f"Выбрано объектов: {len(features)}")

            return

        readable_values = self.classifier.get_readable_names()
        meta: dict[str] = self.classifier.get_fields_meta(layer_name)

        self.parent.table.setRowCount(len(data))

        # show attributes
        self.combo_box_list = []
        self.input_widget_list = []
        self.no_field_list = []
        for i, item in enumerate(data.items()):
            label = CustomTableItem()
            label.setText(item[0])
            label.setBackground(Qt.lightGray)

            field_data = meta.get(item[0])
            if field_data is not None:
                field_type = field_data['type']
            else:
                self.no_field_list.append(item[0])
                continue

            if field_type in ['Char', 'Int', 'Decimal', 'Date']:
                input_widget = CustomLineEdit()

                # если тип атрибута 'Int', устанавливаем Int валидатор
                if field_type == 'Int':
                    input_widget.setValidator(QIntValidator())

                if item[1] in ['-', '***']:
                    input_widget.setPlaceholderText(str(item[1]))
                    self.old_attr_values.append('')
                    input_widget.old_text = ''
                else:
                    input_widget.setText(item[1])
                    self.old_attr_values.append(str(item[1]))
                    input_widget.old_text = item[1]
                input_widget.textChanged.connect(self.on_textChanged(input_widget))

            elif field_type == 'Dir':
                input_widget = CustomComboBox()
                input_widget.setEditable(True)

                attribute = item[0]

                variants = ['']
                input_widget.addItems([''])
                for code in meta[attribute]['choice_fullcode']:
                    rv = readable_values[code]['code']
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

                input_widget.currentTextChanged.connect(
                    self.show_invalid_inputs_callback(input_widget.lineEdit(), variants)
                )

            elif field_type == 'DirValue':
                input_widget = CustomComboBox()
                input_widget.setEditable(True)

                attribute = meta[item[0]]['fieldRef']

                variants = ['']
                input_widget.addItem('')
                for code in meta[attribute]['choice_fullcode']:
                    rv = readable_values[code]['text']
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

                # задаем обработчики событий
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

            self.parent.table.addRow(i, label, input_widget)

        if hasattr(self.parent, 'selected_object_count'):
            self.parent.selected_object_count.setText(
                f"Выбрано объектов: {len(features)}"
            )
        self.parent.save_btn.setEnabled(False)
        if self.no_field_list:
            widget = self.iface.messageBar().createMessage(
                "Следующие атрибуты не показаны,"
                "т.к. отсутствуют в системе требований",
                str(tuple(self.no_field_list))
            )
            self.iface.messageBar().pushWidget(widget, Qgis.Warning)

    def on_gotoRight_click(self):
        index = self.mult_press_data['current_index'] + 1
        pressed_list = self.mult_press_data['pressed_list']
        if index > len(pressed_list) - 1:
            return
        self.parent.label.setText(f"{index + 1}/{len(pressed_list)}")
        feature = pressed_list[index]
        self.mult_press_data['current_index'] += 1

        # select feature
        self.iface.activeLayer().removeSelection()
        layer = self.iface.activeLayer()
        layer.select(feature.id())

        self.display_attrs([feature])

    def on_gotoLeft_click(self):
        index = self.mult_press_data['current_index'] - 1
        if index < 0:
            return
        list_length = len(self.mult_press_data['pressed_list'])
        self.parent.label.setText(f"{index + 1}/{list_length}")
        feature = self.mult_press_data['pressed_list'][index]
        self.mult_press_data['current_index'] -= 1

        # select feature
        self.iface.activeLayer().removeSelection()
        layer = self.iface.activeLayer()
        layer.select(feature.id())

        self.display_attrs([feature])

    def on_textChanged(self, lineEdit: QLineEdit) -> Callable:
        def closure():
            if lineEdit.old_text != lineEdit.text():
                lineEdit.label.setChanged(True)
                self.parent.save_btn.setEnabled(True)
                if lineEdit not in self.changed_inputs:
                    self.changed_inputs.append(lineEdit)
            else:
                lineEdit.label.setChanged(False)
                if lineEdit in self.changed_inputs:
                    self.changed_inputs.remove(lineEdit)
                if len(self.changed_inputs) == 0:
                    self.parent.save_btn.setEnabled(False)

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

    def on_save_btn_clicked(self) -> None:
        """Saves changed attributes"""

        if not self.input_widget_list:
            return

        # получаем значения из виджетов
        current_attr_values = []
        for widget in self.input_widget_list:
            if isinstance(widget, QLineEdit):
                current_attr_values.append(widget.text())
            elif isinstance(widget, QComboBox):
                current_attr_values.append(widget.currentText())
            else:
                raise Exception(
                    "Тип виджета не соответствует ни одному из:"
                    "QLineEdit, QComboBox"
                )

        # получаем новые значения атрибутов
        new_attr_values = self.get_changed_attrs(self.old_attr_values,
                                                 current_attr_values)

        """слой, которому принадлежат изменяемые атрибуты;
        это не обязательно должен быть текущий слой"""
        layer = self.input_widget_list[0].layer

        # current_attr_values = dict(zip(
        #     [i for i in range(len(current_attr_values))], current_attr_values
        # ))
        # edit_mode_was_active = layer.isEditable()
        # if not edit_mode_was_active:
        #     layer.startEditing()
        #
        # for feature in layer.selectedFeatures():
        #     layer.changeAttributeValues(feature.id(), new_attr_values)
        # if self.mode == 'switch':
        #     index = self.mult_press_data['current_index']
        #     self.mult_press_data['pressed_list'].remove(self.mult_press_data['pressed_list'][index])
        #     self.mult_press_data['pressed_list'].insert(index, layer.selectedFeatures()[0])
        #
        # if not edit_mode_was_active:
        #     layer.commitChanges()

        # ---
        self.save(layer, new_attr_values)
        # ---

        self.parent.save_btn.setEnabled(False)

    @staticmethod
    def save(layer, attributes: dict):
        """Принимает слой и новые значения атрибутов и сохраняет их в слой"""

        # запоминаем, был ли режим редактирования включён
        edit_mode_was_active = layer.isEditable()

        layer.startEditing()

        for feature in layer.selectedFeatures():
            layer.changeAttributeValues(feature.id(), attributes)

        """это условие нужно для того,
        чтобы оставить режим редактирования включённым,
        если он был включён до сохранения"""
        if not edit_mode_was_active:
            layer.commitChanges()

    def on_currentIndexChanged(self, combo_box: QComboBox, other_combo_box: QComboBox) -> Callable:
        def closure(index: int) -> None:
            other_combo_box.setCurrentIndex(index)
            if combo_box.old_text != combo_box.currentText():
                print('current index changed -- old, current', combo_box.old_text, combo_box.currentText())
                combo_box.label.setChanged(True)
                self.parent.save_btn.setEnabled(True)
                # self.parent.resetChangesBtn.setEnabled(True)
                if combo_box not in self.changed_inputs:
                    self.changed_inputs.append(combo_box)
            else:
                combo_box.label.setChanged(False)
                if combo_box in self.changed_inputs:
                    self.changed_inputs.remove(combo_box)
                if len(self.changed_inputs) == 0:
                    self.parent.save_btn.setEnabled(False)
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
        self.parent.save_btn.setEnabled(False)

    @staticmethod
    def is_correct(item: str, choice: List) -> bool:
        if item not in choice:
            return False
        return True

    def show_invalid_inputs(self, lineEdit: QLineEdit, choice: List) -> None:
        text = lineEdit.text()
        if not self.is_correct(text, choice):
            lineEdit.setWarnStyle()
        else:
            lineEdit.setNormalStyle()

    def show_invalid_inputs_callback(self, lineEdit: QLineEdit, choice: List) -> Callable:
        def closure():
            self.show_invalid_inputs(lineEdit, choice)

        return closure
