# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'attribute_editor_dialog_base.ui'))


class AttributeEditorBaseDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(AttributeEditorBaseDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setGeometry(0, 0, 500, 600)
        self.vbox = QtWidgets.QVBoxLayout()

        self.table = CustomTableWidget()
        self.save_btn = QtWidgets.QPushButton("Сохранить")
        self.save_btn.setStyleSheet('padding: 5px')
        self.save_btn.setEnabled(False)
        self.vbox.insertWidget(-1, self.table)
        self.vbox.insertWidget(-1, self.save_btn)

        self.setLayout(self.vbox)


class AttributeEditorDialog(AttributeEditorBaseDialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(AttributeEditorDialog, self).__init__(parent)
        self.selected_object_count = QtWidgets.QLabel("")
        self.update_btn = QtWidgets.QPushButton("Обновить")
        self.update_btn.setStyleSheet('padding: 5px; padding-left: 15px; padding-right: 15px')
        self.hspacer = QtWidgets.QSpacerItem(
            0, 0,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.up_hbox = QtWidgets.QHBoxLayout()
        self.up_hbox.insertWidget(-1, self.selected_object_count)

        self.up_hbox.addItem(self.hspacer)

        # кнопка обновить
        self.up_hbox.insertWidget(-1, self.update_btn)

        self.vbox.insertLayout(0, self.up_hbox)


class AttributeEditorSwitchDialog(AttributeEditorBaseDialog):
    def __init__(self, parent=None):
        super(AttributeEditorSwitchDialog, self).__init__(parent)

        self.hbox = QtWidgets.QHBoxLayout()

        self.gotoLeft = QtWidgets.QPushButton("<-")
        self.gotoRight = QtWidgets.QPushButton("->")
        self.label = QtWidgets.QLabel("")
        self.label.setAlignment(Qt.AlignCenter)

        self.hbox.insertWidget(-1, self.gotoLeft)
        self.hbox.insertWidget(-1, self.gotoRight)
        self.hbox.insertWidget(-1, self.label)

        self.vbox.insertLayout(2, self.hbox)


FEATURE_SELECT_FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'feature_selector_dialog_base.ui'))


class FeatureSelectDialog(QtWidgets.QDialog, FEATURE_SELECT_FORM_CLASS):
    def __init__(self, parent=None) -> None:
        """Constructor."""
        super(FeatureSelectDialog, self).__init__(parent)
        self.setupUi(self)


class CustomLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None) -> None:
        """Constructor"""
        super(CustomLineEdit, self).__init__(parent)
        self.setTextMargins(2, 0, 2, 0)
        self.setStyleSheet("border: 0px")
        # self.setMinimumWidth(100)

    def setDangerStyle(self) -> None:
        self.setStyleSheet("background-color: #ffcc00")

    def setNormalStyle(self) -> None:
        self.setStyleSheet("")

    # def decideWhatToDisplay(self, value):
    #     if value in ['-', '***']:
    #         self.lineEdit().setPlaceholderText(str(value))
    #     else:
    #         self.lineEdit().setText(str(value))


class CustomComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None) -> None:
        """Constructor"""
        super(CustomComboBox, self).__init__(parent)
        lineEdit = CustomLineEdit()
        self.setLineEdit(lineEdit)
        self.setEditable(True)
        self.setSizeAdjustPolicy(self.AdjustToMinimumContentsLength)
        self.setStyleSheet("QComboBox { border: 0px }")

    # def setDangerStyle(self) -> None:
    #     self.setStyleSheet("color: white; background-color: #ffcc00")
    #
    # def setNormalStyle(self) -> None:
    #     self.setStyleSheet("")


class CustomTableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None) -> None:
        super(CustomTableWidget, self).__init__(parent)

        self.setFocusPolicy(Qt.NoFocus)

        # цвета зебры и индекс последнего цвета
        self._colors = ('#ffffff', '#f7f7f7')
        self._color_index = 1

        self._combo_counter = 0

        # флаг
        self.next_has_same_color = False

        self.setColumnCount(2)
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalHeaderLabels(["Атрибут", "Значение"])
        self.verticalHeader().setVisible(False)

    def appendRow(self, row_index, label, input_widget):
        color = QColor()

        if isinstance(input_widget, QtWidgets.QComboBox):
            if self._combo_counter == 0:
                # индекс следующего цвета
                next_color_index = int(not self._color_index)
                # запоминаем этот индекс
                self._color_index = next_color_index
                # создаем QColor
                color.setNamedColor(self._colors[next_color_index])

                self._combo_counter = 1
            elif self._combo_counter == 1:
                # создаем QColor
                color.setNamedColor(self._colors[self._color_index])

                self._combo_counter = 0
        else:
            # индекс следующего цвета
            next_color_index = int(not self._color_index)
            # запоминаем этот индекс
            self._color_index = next_color_index
            # создаем QColor
            color.setNamedColor(self._colors[next_color_index])

        label.setBackground(color)

        input_widget.setProperty('background', self._colors[self._color_index])

        self.setRowHeight(row_index, 4)
        self.setItem(row_index, 0, label)
        self.setCellWidget(row_index, 1, input_widget)


class CustomTableItem(QtWidgets.QTableWidgetItem):
    def __init__(self, parent=None) -> None:
        super(CustomTableItem, self).__init__(parent)
        # self.setStyleSheet("padding-left: 10px")

    def setChanged(self, changed) -> None:
        font = QFont()
        font.setBold(True) if changed else font.setBold(False)
        self.setFont(font)

        # if changed:
        #     self.setStyleSheet("padding-left: 10px; font-weight: bold;")
        # else:
        #     self.setStyleSheet("padding-left: 10px; font-weight: normal;")




class CustomTableWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, parent=None) -> None:
        super(CustomTableWidgetItem, self).__init__(parent)

    def setChanged(self, changed) -> None:
        # if changed:
        #     self.setStyleSheet("padding-left: 10px; font-weight: bold;")
        # else:
        #     self.setStyleSheet("padding-left: 10px; font-weight: normal;")
        pass
