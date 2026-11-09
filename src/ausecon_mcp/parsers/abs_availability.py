from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from ausecon_mcp.parsers.abs_structure import _NS, _extract_codelist_id, _text


def parse_abs_availability(xml_text: str) -> dict[str, Any]:
    """Parse an ABS ``availableconstraint`` response (``mode=available``, ``references=all``).

    For each dimension the ABS returns the codes that still have data when every other
    dimension of the requested key is held fixed, plus the time range those data cover.
    """
    root = ET.fromstring(xml_text)
    constraint = root.find(".//structure:ContentConstraint", _NS)
    if constraint is None:
        raise ValueError("ABS availability payload did not contain a ContentConstraint node")

    obs_count = None
    for annotation in constraint.findall("./common:Annotations/common:Annotation", _NS):
        if annotation.attrib.get("id") == "obs_count":
            title = _text(annotation.find("./common:AnnotationTitle", _NS))
            obs_count = int(title) if title and title.isdigit() else None

    labels = _codelist_labels(root)
    codelist_by_dimension, positions = _dimension_metadata(root)

    available: dict[str, list[dict[str, str]]] = {}
    time_range: tuple[str, str] | None = None
    region = constraint.find("./structure:CubeRegion", _NS)
    if region is not None:
        for key_value in region.findall("./common:KeyValue", _NS):
            dimension_id = key_value.attrib["id"]
            time_node = key_value.find("./common:TimeRange", _NS)
            if time_node is not None:
                start = _text(time_node.find("./common:StartPeriod", _NS))
                end = _text(time_node.find("./common:EndPeriod", _NS))
                if start and end and start[:10] <= end[:10]:
                    time_range = (start[:10], end[:10])
                continue
            codelist_labels = labels.get(codelist_by_dimension.get(dimension_id, ""), {})
            available[dimension_id] = [
                {"code": code, "label": codelist_labels.get(code, code)}
                for value in key_value.findall("./common:Value", _NS)
                if (code := _text(value))
            ]

    dimensions = [
        {"id": dimension_id, "available": available.get(dimension_id, [])}
        for dimension_id, _ in sorted(positions.items(), key=lambda item: item[1])
    ]
    return {"obs_count": obs_count, "dimensions": dimensions, "time_range": time_range}


def _codelist_labels(root: ET.Element) -> dict[str, dict[str, str]]:
    return {
        codelist.attrib["id"]: {
            code.attrib["id"]: _text(code.find("./common:Name", _NS)) or code.attrib["id"]
            for code in codelist.findall("./structure:Code", _NS)
        }
        for codelist in root.findall(".//structure:Codelist", _NS)
    }


def _dimension_metadata(root: ET.Element) -> tuple[dict[str, str], dict[str, int]]:
    codelists: dict[str, str] = {}
    positions: dict[str, int] = {}
    for dimension in root.findall(
        ".//structure:DataStructure/structure:DataStructureComponents/"
        "structure:DimensionList/structure:Dimension",
        _NS,
    ):
        dimension_id = dimension.attrib["id"]
        positions[dimension_id] = int(dimension.attrib.get("position", "0"))
        codelist_id = _extract_codelist_id(dimension)
        if codelist_id:
            codelists[dimension_id] = codelist_id
    return codelists, positions
