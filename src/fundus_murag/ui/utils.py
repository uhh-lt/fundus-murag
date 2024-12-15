import re
from re import Pattern

from fundus_murag.assistant.prompt import (
    FUNDUS_COLLECTION_RENDER_TAG_OPEN,
    FUNDUS_RECORD_RENDER_TAG_OPEN,
    RENDER_TAG_CLOSE,
    RENDER_TAG_MURAG_ID_ATTRIBUTE,
)


def contains_fundus_record_render_tag(string: str) -> bool:
    pattern = _get_render_tag_pattern(FUNDUS_RECORD_RENDER_TAG_OPEN)
    return re.search(pattern, string) is not None


def contains_fundus_collection_render_tag(string: str) -> bool:
    pattern = _get_render_tag_pattern(FUNDUS_COLLECTION_RENDER_TAG_OPEN)
    return re.search(pattern, string) is not None


def extract_murag_id_from_fundus_record_render_tags(string: str) -> list[str] | None:
    pattern = _get_render_tag_pattern(FUNDUS_RECORD_RENDER_TAG_OPEN)
    matches = re.findall(pattern, string)
    if matches is not None and len(matches) > 0:
        return [m[1] for m in matches]
    return None


def extract_murag_id_from_fundus_collection_render_tags(
    string: str,
) -> list[str] | None:
    pattern = _get_render_tag_pattern(FUNDUS_COLLECTION_RENDER_TAG_OPEN)
    matches = re.findall(pattern, string)
    if matches is not None and len(matches) > 0:
        return [m[1] for m in matches]
    return None


def replace_fundus_record_render_tag(string: str, replace: str = "") -> str:
    pattern = _get_render_tag_pattern(FUNDUS_RECORD_RENDER_TAG_OPEN)
    return re.sub(pattern, replace, string)


def replace_fundus_collection_render_tag(string: str, replace: str = "") -> str:
    pattern = _get_render_tag_pattern(FUNDUS_COLLECTION_RENDER_TAG_OPEN)
    return re.sub(pattern, replace, string)


def _get_render_tag_pattern(render_tag_open: str) -> Pattern:
    pattern = re.compile(
        render_tag_open
        + r"\s+"
        + RENDER_TAG_MURAG_ID_ATTRIBUTE
        + r"\s*=\s*(['\"])"
        + r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12})"
        + r"\1\s*"
        + RENDER_TAG_CLOSE
    )
    return pattern
