__version__ = "0.1.0"

import json
import math
from typing import Any, Dict, List, Optional, Tuple, Union


__all__ = [
    "ComponentDefinition",
    "VisualBuilder",
    "ComponentLibrary",
    "LayoutEngine",
    "Theme",
    "VisualBuilderError",
]


class VisualBuilderError(Exception):
    pass


class ComponentDefinition:
    def __init__(
        self,
        type: str,
        props: Optional[Dict[str, Any]] = None,
        children: Optional[List["ComponentDefinition"]] = None,
        events: Optional[Dict[str, str]] = None,
        style: Optional[Dict[str, Any]] = None,
        comp_id: str = "",
    ) -> None:
        self.type = type
        self.props = props or {}
        self.children = children or []
        self.events = events or {}
        self.style = style or {}
        self.id = comp_id or f"{type}_{id(self)}"


class ComponentLibrary:
    def __init__(self) -> None:
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        builtins: Dict[str, Dict[str, Any]] = {
            "button": {
                "props": {
                    "text": {"type": "string", "default": "Button"},
                    "enabled": {"type": "boolean", "default": True},
                },
                "events": ["on_click", "on_focus"],
            },
            "label": {
                "props": {
                    "text": {"type": "string", "default": ""},
                    "align": {"type": "string", "default": "left"},
                },
                "events": [],
            },
            "textfield": {
                "props": {
                    "placeholder": {"type": "string", "default": ""},
                    "value": {"type": "string", "default": ""},
                    "multiline": {"type": "boolean", "default": False},
                },
                "events": ["on_change", "on_focus", "on_blur"],
            },
            "image": {
                "props": {
                    "src": {"type": "string", "default": ""},
                    "alt": {"type": "string", "default": ""},
                    "width": {"type": "number", "default": 100},
                    "height": {"type": "number", "default": 100},
                },
                "events": ["on_load", "on_error"],
            },
            "list": {
                "props": {
                    "items": {"type": "array", "default": []},
                    "item_template": {"type": "string", "default": "{item}"},
                },
                "events": ["on_select"],
            },
            "card": {
                "props": {
                    "title": {"type": "string", "default": ""},
                    "subtitle": {"type": "string", "default": ""},
                    "elevation": {"type": "number", "default": 2},
                },
                "events": ["on_click"],
            },
            "column": {
                "props": {
                    "spacing": {"type": "number", "default": 8},
                    "alignment": {"type": "string", "default": "start"},
                },
                "events": [],
            },
            "row": {
                "props": {
                    "spacing": {"type": "number", "default": 8},
                    "alignment": {"type": "string", "default": "center"},
                },
                "events": [],
            },
            "switch": {
                "props": {
                    "checked": {"type": "boolean", "default": False},
                    "label": {"type": "string", "default": ""},
                },
                "events": ["on_toggle"],
            },
            "slider": {
                "props": {
                    "min": {"type": "number", "default": 0},
                    "max": {"type": "number", "default": 100},
                    "value": {"type": "number", "default": 50},
                    "step": {"type": "number", "default": 1},
                },
                "events": ["on_change"],
            },
            "progress": {
                "props": {
                    "value": {"type": "number", "default": 0},
                    "max": {"type": "number", "default": 100},
                    "indeterminate": {"type": "boolean", "default": False},
                },
                "events": [],
            },
            "spacer": {
                "props": {
                    "width": {"type": "number", "default": 0},
                    "height": {"type": "number", "default": 0},
                },
                "events": [],
            },
            "divider": {
                "props": {
                    "orientation": {"type": "string", "default": "horizontal"},
                    "thickness": {"type": "number", "default": 1},
                },
                "events": [],
            },
        }
        for comp_type, schema in builtins.items():
            self._schemas[comp_type] = schema

    def register(self, component_type: str, schema: Dict[str, Any]) -> None:
        self._schemas[component_type] = schema

    def get_schema(self, component_type: str) -> Optional[Dict[str, Any]]:
        return self._schemas.get(component_type)

    def list_types(self) -> List[str]:
        return list(self._schemas.keys())


class Theme:
    def __init__(
        self,
        colors: Optional[Dict[str, str]] = None,
        spacing: Optional[Dict[str, int]] = None,
        fonts: Optional[Dict[str, Any]] = None,
        border_radius: int = 4,
    ) -> None:
        self.colors = colors or {
            "primary": "#007aff",
            "secondary": "#5856d6",
            "background": "#ffffff",
            "surface": "#f2f2f7",
            "text": "#000000",
            "text_secondary": "#8e8e93",
            "border": "#c6c6c8",
            "error": "#ff3b30",
            "success": "#34c759",
        }
        self.spacing = spacing or {
            "xs": 4,
            "sm": 8,
            "md": 16,
            "lg": 24,
            "xl": 32,
        }
        self.fonts = fonts or {
            "family": "system-ui",
            "size_sm": 12,
            "size_md": 14,
            "size_lg": 18,
            "size_xl": 24,
            "weight_normal": "400",
            "weight_bold": "700",
        }
        self.border_radius = border_radius

    def to_css(self) -> str:
        lines: List[str] = [":root {"]
        for key, val in self.colors.items():
            css_key = key.replace("_", "-")
            lines.append(f"  --color-{css_key}: {val};")
        for key, val in self.spacing.items():
            lines.append(f"  --spacing-{key}: {val}px;")
        lines.append(f"  --font-family: {self.fonts.get('family', 'system-ui')};")
        for key, val in self.fonts.items():
            if key == "family":
                continue
            css_key = key.replace("_", "-")
            lines.append(f"  --font-{css_key}: {val};")
        lines.append(f"  --border-radius: {self.border_radius}px;")
        lines.append("}")
        return "\n".join(lines)


class LayoutEngine:
    def calculate(
        self,
        components: List[ComponentDefinition],
        container_width: int,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        x = 0
        y = 0
        row_height = 0
        for comp in components:
            style = comp.style
            mode = style.get("layout", "flex-row")
            if mode == "absolute":
                results.append({
                    "id": comp.id,
                    "x": style.get("left", 0),
                    "y": style.get("top", 0),
                    "width": style.get("width", 100),
                    "height": style.get("height", 50),
                })
                continue
            width = style.get("width", 100)
            height = style.get("height", 50)
            if mode == "flex-column":
                x = 0
                y += row_height
                row_height = 0
            elif mode == "flex-row":
                if x + width > container_width:
                    x = 0
                    y += row_height
                    row_height = 0
            results.append({
                "id": comp.id,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            })
            x += width + style.get("margin", 0)
            row_height = max(row_height, height)
        return results


class VisualBuilder:
    def __init__(self) -> None:
        self.library = ComponentLibrary()

    def build(self, spec: Union[Dict, str]) -> List[ComponentDefinition]:
        if isinstance(spec, str):
            parsed = json.loads(spec)
        else:
            parsed = spec
        if isinstance(parsed, list):
            return [self._parse_component(item) for item in parsed]
        if isinstance(parsed, dict):
            if "components" in parsed:
                return [self._parse_component(c) for c in parsed["components"]]
            return [self._parse_component(parsed)]
        raise VisualBuilderError("Invalid spec format")

    def _parse_component(self, item: Dict) -> ComponentDefinition:
        if "type" not in item:
            raise VisualBuilderError("Component missing 'type' field")
        children_raw = item.get("children", [])
        if isinstance(children_raw, list):
            children = [self._parse_component(c) for c in children_raw]
        else:
            children = []
        return ComponentDefinition(
            type=item["type"],
            props=item.get("props", {}),
            children=children,
            events=item.get("events", {}),
            style=item.get("style", {}),
            comp_id=item.get("id", ""),
        )

    def to_json(self, components: List[ComponentDefinition]) -> str:
        return json.dumps(
            [self._component_to_dict(c) for c in components],
            indent=2,
        )

    def _component_to_dict(self, comp: ComponentDefinition) -> Dict:
        return {
            "id": comp.id,
            "type": comp.type,
            "props": comp.props,
            "children": [self._component_to_dict(c) for c in comp.children],
            "events": comp.events,
            "style": comp.style,
        }

    def to_zoya_code(self, components: List[ComponentDefinition]) -> str:
        lines: List[str] = []
        for comp in components:
            lines.extend(self._component_to_code(comp, 0))
        return "\n".join(lines)

    def _component_to_code(self, comp: ComponentDefinition, depth: int) -> List[str]:
        indent = "  " * depth
        lines: List[str] = []
        props_str = ", ".join(
            f"{k}={repr(v)}" for k, v in comp.props.items()
        )
        style_str = ""
        if comp.style:
            style_str = ", style=" + json.dumps(comp.style)
        events_str = ""
        if comp.events:
            events_str = ", events=" + json.dumps(comp.events)
        header = f"{indent}{comp.type}({props_str}{style_str}{events_str})"
        if comp.children:
            lines.append(header + " {")
            for child in comp.children:
                lines.extend(self._component_to_code(child, depth + 1))
            lines.append(indent + "}")
        else:
            lines.append(header)
        return lines

    def render_preview(self, components: List[ComponentDefinition]) -> str:
        lines: List[str] = []
        for comp in components:
            lines.extend(self._preview_component(comp, 0))
        return "\n".join(lines)

    def _preview_component(self, comp: ComponentDefinition, depth: int) -> List[str]:
        indent = "  " * depth
        prefix = f"[{comp.type}]"
        title = comp.props.get("text", comp.props.get("title", comp.id))
        lines: List[str] = [f"{indent}{prefix} {title}"]
        for child in comp.children:
            lines.extend(self._preview_component(child, depth + 1))
        return lines

    def validate_spec(self, spec: Dict) -> List[str]:
        errors: List[str] = []
        if not isinstance(spec, dict):
            return ["Spec must be a dictionary"]
        components = spec.get("components", [spec])
        if isinstance(components, dict):
            components = [components]
        for i, comp in enumerate(components):
            if "type" not in comp:
                errors.append(f"Component at index {i}: missing 'type' field")
                continue
            comp_type = comp["type"]
            schema = self.library.get_schema(comp_type)
            if schema is None:
                errors.append(f"Component at index {i}: unknown type '{comp_type}'")
                continue
            known_props = set(schema.get("props", {}).keys())
            for prop in comp.get("props", {}):
                if prop not in known_props:
                    errors.append(
                        f"Component at index {i}: unknown prop '{prop}' for type '{comp_type}'"
                    )
            known_events = set(schema.get("events", []))
            for event in comp.get("events", {}):
                if event not in known_events:
                    errors.append(
                        f"Component at index {i}: unknown event '{event}' for type '{comp_type}'"
                    )
        return errors

    def merge_styles(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(base)
        for key, val in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
                merged[key] = self.merge_styles(merged[key], val)
            else:
                merged[key] = val
        return merged
