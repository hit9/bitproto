"""
Renderer implementations.
"""

from typing import Dict, Type as T, Tuple
from bitproto.renderer.renderer import Renderer

from .c import RendererCHeader, RendererC
from .go import RendererGo
from .py import RendererPy

renderer_registry: Dict[str, Tuple[T[Renderer], ...]] = {
    "c": (RendererC, RendererCHeader),
    "go": (RendererGo,),
    "py": (RendererPy,),
}
