from __future__ import annotations

from xml.etree import ElementTree as ET

_NS = {
    "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message",
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}


def parse_abs_structure(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    data_structure = root.find(".//structure:DataStructure", _NS)
    if data_structure is None:
        raise ValueError("ABS structure payload did not contain a DataStructure node")

    codelists = _build_codelist_index(root)
    dimensions = []
    for dimension in data_structure.findall(".//structure:Dimension", _NS):
        codelist_id = _extract_codelist_id(dimension)
        dimensions.append(
            {
                "id": dimension.attrib["id"],
                "position": int(dimension.attrib.get("position", "0")),
                "name": _text(dimension.find("./common:Name", _NS))
                or _text(dimension.find("./structure:ConceptIdentity/common:Name", _NS))
                or dimension.attrib["id"],
                "values": codelists.get(codelist_id, []),
            }
        )

    dimensions.sort(key=lambda item: item["position"])
    return {
        "id": data_structure.attrib["id"],
        "name": _text(data_structure.find("./common:Name", _NS)) or data_structure.attrib["id"],
        "dimensions": dimensions,
    }


def _build_codelist_index(root: ET.Element) -> dict[str, list[dict[str, str]]]:
    codelists: dict[str, list[dict[str, str]]] = {}
    for codelist in root.findall(".//structure:Codelist", _NS):
        codelists[codelist.attrib["id"]] = [
            {
                "code": code.attrib["id"],
                "label": _text(code.find("./common:Name", _NS)) or code.attrib["id"],
            }
            for code in codelist.findall("./structure:Code", _NS)
        ]
    return codelists


def _extract_codelist_id(dimension: ET.Element) -> str | None:
    for child in dimension.findall(".//*[@id]"):
        if child.attrib.get("id", "").startswith("CL_"):
            return child.attrib["id"]
    return None


def _text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    return element.text.strip()
