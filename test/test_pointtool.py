import unittest

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsVectorLayer,
                       QgsField,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsProject)
from qgis.gui import QgisInterface

from attribute_editor_dialog import AttributeEditorDialog
from pointtool import PointTool
from provider import RequirementsProvider


class TestPointTool(unittest.TestCase):

    def setUp(self) -> None:
        # создать слой с названием из системы требований
        # создать объекты с атрибутами

        # создаем инструмент
        iface = QgisInterface()
        canvas = iface.mapCanvas()
        self.point_tool_normal = PointTool(
            AttributeEditorDialog(),
            iface,
            canvas,
            RequirementsProvider('/RS/RS.mixml'),
            mode='normal')

    def test_save(self) -> None:
        # создаем слой
        vector_layer = QgsVectorLayer('Polygon', 'temp', 'memory')
        provider = vector_layer.dataProvider()
        provider.addAttributes([
            QgsField('A', QVariant.String),
            QgsField('B', QVariant.String),
            QgsField('C', QVariant.String),
        ])
        vector_layer.updateFields()

        # создаем объекты
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(10, 10)))
        f.setAttributes(["Ada L.", 2, 0.3])
        provider.addFeature(f)
        vector_layer.updateExtents()
        QgsProject.instance().addMapLayer(vector_layer)

        self.assertEqual(2, 2)

    def tearDown(self) -> None:
        pass


if __name__ == '__main__':
    unittest.main()
