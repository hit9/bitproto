"""
bitproto.renderer_base
~~~~~~~~~~~~~~~~~~~~~~~

Renderer base class and utils.
"""

import os
from typing import Dict, Optional, Type as T

from bitproto.ast import Proto
from bitproto.errors import UnsupportedLanguageToRender

RendererClass = T["Renderer"]

registry: Dict[str, RendererClass] = {}


def get_renderer_cls(lang: str) -> Optional[RendererClass]:
    return registry.get(lang, None)


class Renderer:
    """Base renderer class."""

    lang: str = "__lang_missing__"

    def __init__(self, proto: Proto, out: str) -> None:
        self.proto = proto
        self.out = out

    def __init_subclass__(cls) -> None:
        registry[cls.lang] = cls

    def render(self) -> None:
        pass


def render(proto: Proto, lang: str, out: Optional[str] = None) -> None:
    """Render given `proto` to directory `out`.

    :param proto: The parsed bitproto instance.
    :param lang: The language in registry.
    :param out: The directory to generate to, defaults to the directory of source.
    """
    if out is None:
        if proto.filepath:
            out = os.path.dirname(os.path.abspath(proto.filepath))
        else:
            out = os.getcwd()

    renderer_cls = get_renderer_cls(lang)
    if renderer_cls is None:
        raise UnsupportedLanguageToRender()

    renderer = renderer_cls(proto, out)
    renderer.render()
