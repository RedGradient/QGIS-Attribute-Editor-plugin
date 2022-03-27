# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'attribute_editor_dialog_base.ui'))


class AttributeEditorBaseDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(AttributeEditorBaseDialog, self).__init__(parent)
        # self.setupUi(self)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setGeometry(0, 0, 500, 600)
        self.vbox = QtWidgets.QVBoxLayout()

        self.table = CustomTableWidget()
        self.saveBtn = QtWidgets.QPushButton("Сохранить")
        self.saveBtn.setEnabled(False)
        self.ctrl_status = QtWidgets.QLabel("CTRL не нажат")
        self.vbox.insertWidget(-1, self.ctrl_status)
        self.vbox.insertWidget(-1, self.table)
        self.vbox.insertWidget(-1, self.saveBtn)

        self.setLayout(self.vbox)


class AttributeEditorDialog(AttributeEditorBaseDialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(AttributeEditorDialog, self).__init__(parent)
        self.selected_object_count = QtWidgets.QLabel("")
        self.temp_tool = QtWidgets.QPushButton()
        self.temp_tool.setText("Показать атрибуты\nвыделенных объектов")
        self.up_hbox = QtWidgets.QHBoxLayout()
        self.up_hbox.insertWidget(-1, self.selected_object_count)

        # временное решение
        self.up_hbox.insertWidget(-1, self.temp_tool)

        # self.vbox.insertWidget(0, self.selected_object_count)
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
        self.setStyleSheet("color: white; background-color: rgb(237, 82, 73)")

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
        # "QComboBox QAbstractItemView { background-color: rgb(248, 248, 255) }"
        # self.setStyleSheet("border: 0px; QComboBox QAbstractItemView {border: 2px solid red;}")

    def setDangerStyle(self) -> None:
        self.setStyleSheet("color: white; background-color: rgb(237, 82, 73)")

    def setNormalStyle(self) -> None:
        self.setStyleSheet("")


class CustomTableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None) -> None:
        super(CustomTableWidget, self).__init__(parent)
        # self.resizeEvent = self.onResize

        self.setColumnCount(2)
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalHeaderLabels(["Атрибут", "Значение"])
        # self.setColumnWidth(1, self.geometry().width() - 2 * self.columnWidth(0))
        # self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        # self.setStyleSheet("background-color: rgb(248, 248, 255)")


class CustomLabel(QtWidgets.QLabel):
    def __init__(self, parent=None) -> None:
        super(CustomLabel, self).__init__(parent)
        self.setStyleSheet("padding-left: 10px")

    def setChanged(self, changed) -> None:
        if changed:
            self.setStyleSheet("padding-left: 10px; font-weight: bold;")
        else:
            self.setStyleSheet("padding-left: 10px; font-weight: normal;")


class CustomTableWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, parent=None) -> None:
        super(CustomTableWidgetItem, self).__init__(parent)

    def setChanged(self, changed) -> None:
        # if changed:
        #     self.setStyleSheet("padding-left: 10px; font-weight: bold;")
        # else:
        #     self.setStyleSheet("padding-left: 10px; font-weight: normal;")
        pass
