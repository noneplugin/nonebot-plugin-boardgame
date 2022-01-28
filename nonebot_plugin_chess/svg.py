from dataclasses import dataclass
from typing import List, Dict, Union

Attributes = Dict[str, Union[str, int, bool]]


def escape_html(source: str) -> str:
    return (
        source.replace('&', '&amp;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


class Tag:
    def __init__(self, tag: str):
        self.tag = tag
        self.parent: Tag = None
        self.children: List[Tag] = []
        self.attributes: Attributes = {}
        self.inner_text: str = ''

    def child(self, tag: str) -> "Tag":
        child = Tag(tag)
        child.parent = self
        self.children.append(child)
        return child

    def attr(self, attributes: Attributes) -> "Tag":
        self.attributes.update(attributes)
        return self

    def data(self, inner_text: str) -> "Tag":
        self.inner_text = inner_text
        return self

    def line(self, x1: int, y1: int, x2: int, y2: int, attr: Attributes = {}) -> "Tag":
        self.child('line').attr({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, **attr})
        return self

    def circle(self, cx: int, cy: int, r: int, attr: Attributes = {}) -> "Tag":
        self.child('circle').attr({'cx': cx, 'cy': cy, 'r': r, **attr})
        return self

    def rect(self, x1: int, y1: int, x2: int, y2: int, attr: Attributes = {}) -> "Tag":
        self.child('rect').attr(
            {'x': x1, 'y': y1, 'width': y2 - y1, 'height': x2 - x1, **attr}
        )
        return self

    def text(self, text: str, x: int, y: int, attr: Attributes = {}) -> "Tag":
        self.child('text').attr({'x': x, 'y': y, **attr}).data(text)
        return self

    def g(self, attr: Attributes = {}) -> "Tag":
        return self.child('g').attr(attr)

    def outer(self) -> str:
        attr_text = ' '.join(
            [
                f'{key}="{escape_html(str(value))}"'
                for key, value in self.attributes.items()
            ]
        )
        return f'<{self.tag} {attr_text} >{self.inner()}</{self.tag}>'

    def inner(self) -> str:
        if self.children:
            return ''.join([child.outer() for child in self.children])
        else:
            return self.inner_text


@dataclass
class ViewBox:
    left: int = 0
    right: int = 0
    top: int = 0
    bottom: int = 0


@dataclass
class SvgOptions:
    size: int = 0
    width: int = 0
    height: int = 0
    magnif: int = 0
    view_box: ViewBox = None
    view_size: int = 0


class Svg(Tag):
    def __init__(self, options: SvgOptions = SvgOptions()):
        super().__init__('svg')
        size = options.size or 200
        view_size = options.view_size or size
        width = options.width or size
        height = options.height or size

        self.width: int = width
        self.height: int = height
        ratio = view_size / size
        self.view: ViewBox = options.view_box or ViewBox(
            0, height * ratio, 0, width * ratio
        )
        self.attr(
            {
                'width': width,
                'height': height,
                'viewBox': f'{self.view.left} {self.view.top} {self.view.right} {self.view.bottom}',
                'xmlns': 'http://www.w3.org/2000/svg',
                'version': '1.1',
            }
        )

    def fill(self, color: str):
        self.rect(
            self.view.top,
            self.view.left,
            self.view.bottom,
            self.view.right,
            {'style': f'fill: {color}'},
        )
        return self
