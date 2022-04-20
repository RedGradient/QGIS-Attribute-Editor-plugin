# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'example@mail.com'
__date__ = '2022-02-17'
__copyright__ = 'Copyright 2022, Karo'

import unittest

from qgis.PyQt.QtWidgets import QDialogButtonBox, QDialog

from attribute_editor_dialog import AttributeEditorDialog

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()


class AttributeEditorDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        self.dialog = AttributeEditorDialog()

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    # def test_dialog_ok(self):
    #     """Test we can click OK."""
    #
    #     button = self.dialog.button_box.button(QDialogButtonBox.Ok)
    #     button.click()
    #     result = self.dialog.result()
    #     self.assertEqual(result, QDialog.Accepted)

    # def test_dialog_cancel(self):
    #     """Test we can click cancel."""
    #     button = self.dialog.button_box.button(QDialogButtonBox.Cancel)
    #     button.click()
    #     result = self.dialog.result()
    #     self.assertEqual(result, QDialog.Rejected)

    def test_abc(self):
        self.assertEqual(2 * 2, 4)


if __name__ == "__main__":
    # pass
    suite = unittest.makeSuite(AttributeEditorDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    # unittest.main()

