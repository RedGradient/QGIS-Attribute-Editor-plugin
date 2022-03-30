from unittest import TestCase

from qgis.core import *


class MyTest(TestCase):
    def setUp(self) -> None:
        layer = QgsVectorLayer("Polygon", "test_polygon_layer", "memory")
        provider = layer.dataProvider()
        layer.startEditing()
        provider.addAttributes([
            QgsField("attr_1", QVariant.String),
            QgsField("attr_2", QVariant.String),
            QgsField("attr_3", QVariant.String),
        ])
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPoint(QgsPoint(10, 10)))
        feature.setAttributeMap({
            0: QVariant("attr_value_1"),
            1: QVariant("attr_value_2"),
            2: QVariant("attr_value_3"),
        })
        provider.addFeatures([feature])
        layer.commitChanges()

    def test_attrs(self):
        # layer =
        assert layer['attr_1'] == layer['attr_value_1']
        print("OK")
