# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AttributeEditorDialog
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

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'attribute_editor_dialog_base.ui'))


class AttributeEditorDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(AttributeEditorDialog, self).__init__(parent)
        # self.setupUi(self)

        self.setGeometry(0, 0, 500, 600)

        self.vbox = QtWidgets.QVBoxLayout()

        self.table = CustomTableWidget()
        self.saveBtn = QtWidgets.QPushButton("Сохранить")
        self.saveBtn.setEnabled(False)
        self.vbox.insertWidget(-1, self.table)
        self.vbox.insertWidget(-1, self.saveBtn)

        hbox = QtWidgets.QHBoxLayout()
        self.goto_left = QtWidgets.QPushButton("<-")
        self.goto_left.setEnabled(False)
        self.goto_right = QtWidgets.QPushButton("->")
        self.goto_right.setEnabled(False)
        hbox.insertWidget(-1, self.goto_left)
        hbox.insertWidget(-1, self.goto_right)

        self.vbox.insertLayout(1, hbox)

        self.setLayout(self.vbox)


FEATURE_SELECT_FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'feature_selector_dialog_base.ui'))


class FeatureSelectDialog(QtWidgets.QDialog, FEATURE_SELECT_FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(FeatureSelectDialog, self).__init__(parent)
        self.setupUi(self)


class CustomLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        """Constructor"""
        super(CustomLineEdit, self).__init__(parent)
        self.setTextMargins(2, 0, 2, 0)
        self.setStyleSheet("border: 0px")
        self.setMinimumWidth(100)

    def setDangerStyle(self):
        self.setStyleSheet("color: white; background-color: rgb(237, 82, 73)")

    def setNormalStyle(self):
        self.setStyleSheet("")

    # def decideWhatToDisplay(self, value):
    #     if value in ['-', '***']:
    #         self.lineEdit().setPlaceholderText(str(value))
    #     else:
    #         self.lineEdit().setText(str(value))


class CustomComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        """Constructor"""
        super(CustomComboBox, self).__init__(parent)
        lineEdit = CustomLineEdit()
        self.setLineEdit(lineEdit)
        self.setMinimumWidth(100)
        self.setEditable(True)
        self.setSizeAdjustPolicy(self.AdjustToMinimumContentsLength)
        self.setStyleSheet("border: 0px")

    def setDangerStyle(self):
        self.setStyleSheet("color: white; background-color: rgb(237, 82, 73)")

    def setNormalStyle(self):
        self.setStyleSheet("")


class CustomTableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(CustomTableWidget, self).__init__(parent)
        # self.resizeEvent = self.onResize
        self.setColumnCount(2)
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalHeaderLabels(["Атрибут", "Значение"])
        # self.setColumnWidth(1, self.geometry().width() - 2 * self.columnWidth(0))
        # self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet("background-color: rgb(248, 248, 255)")


class CustomLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super(CustomLabel, self).__init__(parent)
        self.setStyleSheet("padding-left: 10px")

    def setChanged(self, changed):
        if changed:
            self.setStyleSheet("padding-left: 10px; font-weight: bold;")
        else:
            self.setStyleSheet("padding-left: 10px; font-weight: normal;")


class CustomTableWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, parent=None):
        super(CustomTableWidgetItem, self).__init__(parent)

    def setChanged(self, changed):
        # if changed:
        #     self.setStyleSheet("padding-left: 10px; font-weight: bold;")
        # else:
        #     self.setStyleSheet("padding-left: 10px; font-weight: normal;")
        pass