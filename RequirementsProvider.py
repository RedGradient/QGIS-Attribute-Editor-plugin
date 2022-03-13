import os.path
import xml.etree.ElementTree as ET
from typing import *
from xml.etree.ElementTree import Element


class RequirementsProvider:
    def __init__(self, path: str):
        self.path = path
        self.classifier = ET.parse(os.path.dirname(__file__) + self.path)

    def get_readable_names(self) -> Dict:
        node = self.classifier.find("Classifier")
        return self._get_readable_names(node, {})

    def get_fields_meta(self, layer_name: str) -> Dict:
        layer_node = self.get_layer_node(layer_name)
        return self._get_fields_meta(layer_node, {})

    def _get_readable_names(self, node: Element, acc: Dict) -> Dict:
        """Takes xml node and returns all <name>.text from it"""
        for i in node:
            if i.tag == "Directory":
                self._get_readable_names(i, acc)
                continue
            if i.tag == "DirElement":
                self._get_readable_names(i, acc)
                continue
            if i.tag == "name":
                acc.update({node.attrib["FullCode"]: {"text": i.text, "code": node.attrib["code"]}})
                continue
        return acc

    def _get_fields_meta(self, node: Element, acc: Dict):
        """
        :node is tLayer node
        :accum is empty dict
        """
        for i in node:
            if i.tag == "field":
                is_required = i[0].attrib.get("Required")
                if is_required is not None:
                    acc[i.attrib["name"]] = {"Required": True}
                else:
                    acc[i.attrib["name"]] = {"Required": False}
                self._get_fields_meta(i[0], acc)
                continue
            if i.tag in ["Char", "Int", "Decimal", "Date"]:
                acc[list(acc.keys())[-1]].update({"type": i.tag})
                return None
            if i.tag == "Dir":
                values = []
                for val in i[0]:
                    values.append(val.text)
                acc[list(acc.keys())[-1]].update({"type": "Dir", "choice_fullcode": values})
                return None
            if i.tag == "DirValue":
                acc[list(acc.keys())[-1]].update({"type": "DirValue", "fieldRef": i[0].attrib.get("name")})
                return None
        return acc

    def get_layer_node(self, layer_name: str):
        """Searches for node corresponding to the given layer name"""
        layer_name = self.get_layer_ref(layer_name)
        for node in self.classifier.iter('tLayer'):
            if node.attrib.get('name') == layer_name:
                return node

    def get_layer_ref(self, layer_name: str):
        for physical_layer in self.classifier.iter("PhisicalLayer"):
            if physical_layer.attrib["name"] == layer_name:
                layer_ref = physical_layer[0].attrib["name"]
                return layer_ref

    # def get_field_type(self, layer_name: str, field_name: str) -> str:
    #     for tLayer in self.classifier.iter("tLayer"):
    #         if tLayer.attrib["name"] == layer_name:
    #             for field in tLayer:
    #                 if field.attrib["name"] == field_name:
    #                     field_type = field[0][0].tag
    #                     return field_type


if __name__ == '__main__':
    provider = RequirementsProvider("/RS/RS.mixml")

    assert provider.get_layer_ref("Такого слоя нет") is None
    assert provider.get_layer_ref("Внутригород_тер_города_ФЗ") == "Территория_МО"
    assert provider.get_layer_ref("Охранная_зона_трансп_коммун") == "Охранная_зона_трансп_коммун"
    assert provider.get_layer_ref("Тер_инвест_деятельности") == "Территории_инвест_деят"

    # assert provider.get_field_type("Зем_участки", "Идентификатор_объекта") == "Char"
    # assert provider.get_field_type("Зем_участки", "Код_объекта") == "DirValue"
    # assert provider.get_field_type("Зем_участки", "Порядковый_номер") == "Int"
    # assert provider.get_field_type("Зем_участки", "Вид_разрешенного_исп") == "DirValue"
    # assert provider.get_field_type("Зем_участки", "Площадь_кв_м") == "Decimal"
    # assert provider.get_field_type("Зем_участки", "Площадь_кв_м") == "Decimal"
    # assert provider.get_field_type("Зем_участки", "Площадь_кв_м") == "Decimal"
    # assert provider.get_field_type("Зем_участки", "Площадь_кв_м") == "Decimal"

    assert provider.get_layer_node("Внутригород_тер_города_ФЗ").attrib["name"] == "Территория_МО"
    assert provider.get_layer_node("Зем_участки").attrib["name"] == "Зем_участки"
    assert provider.get_layer_node("Такого слоя нет") is None
