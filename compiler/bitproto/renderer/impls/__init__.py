"""
Renderer implementations.
"""

from typing import Dict, Tuple, Type as T

from bitproto.renderer.renderer import Renderer

from .c import RendererC, RendererCHeader
from .go import RendererGo
from .py import RendererPy

renderer_registry: Dict[str, Tuple[T[Renderer], ...]] = {
    "c": (RendererC, RendererCHeader),
    "go": (RendererGo,),
    "py": (RendererPy,),
}
