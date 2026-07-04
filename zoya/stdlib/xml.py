from __future__ import annotations

from typing import Any


def load_module(interpreter: Any) -> Any:
    import xml.etree.ElementTree as _ET

    from zoya.interpreter import ZoyaModule

    def parse(text: str) -> Any:
        try:
            return _ET.fromstring(text)
        except Exception as e:
            return f"Error: {e}"

    def load(path: str) -> Any:
        try:
            tree = _ET.parse(path)
            return tree.getroot()
        except Exception as e:
            return f"Error: {e}"

    def save(data: Any, path: str) -> str:
        try:
            tree = _ET.ElementTree(data)
            tree.write(path, encoding="utf-8", xml_declaration=True)
            return f"Saved to {path}"
        except Exception as e:
            return f"Error: {e}"

    def get(element: Any, tag: str) -> Any:
        try:
            return element.find(tag)
        except Exception as e:
            return f"Error: {e}"

    def text(element: Any) -> str:
        try:
            return element.text or ""
        except Exception as e:
            return f"Error: {e}"

    def attr(element: Any, name: str) -> str:
        try:
            return element.get(name) or ""
        except Exception as e:
            return f"Error: {e}"

    def children(element: Any) -> list[Any]:
        try:
            return list(element)
        except Exception as e:
            return [f"Error: {e}"]

    def create(tag: str) -> Any:
        return _ET.Element(tag)

    funcs = {
        "parse": parse,
        "load": load,
        "save": save,
        "get": get,
        "text": text,
        "attr": attr,
        "children": children,
        "create": create,
    }

    return ZoyaModule("xml", funcs)
