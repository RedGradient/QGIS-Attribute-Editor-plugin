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
        self.setupUi(self)


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

    def setDangerStyle(self):
        self.setStyleSheet("color: white; background-color: rgb(237, 82, 73)")

    def setNormalStyle(self):
        self.setStyleSheet("")
