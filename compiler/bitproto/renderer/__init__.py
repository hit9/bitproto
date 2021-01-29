"""
bitproto.renderer
~~~~~~~~~~~~~~~~~

Renderer on target language.
"""

from typing import List, Optional

from bitproto._ast import Proto
from bitproto.errors import UnsupportedLanguageToRender
from bitproto.renderer.impls import renderer_registry
from bitproto.renderer.renderer import Renderer


def render(
    proto: Proto,
    lang: str,
    outdir: Optional[str] = None,
    optimization_mode: bool = False,
    optimization_mode_filter_messages: Optional[List[str]] = None,
) -> List[str]:
    """Render given `proto` to directory `outdir`.
    Returns the filepath list generated.
    """
    clss = renderer_registry.get(lang, None)
    if clss is None:
        raise UnsupportedLanguageToRender()

    outs = []
    for renderer_cls in clss:
        renderer = renderer_cls(
            proto,
            outdir=outdir,
            optimization_mode=optimization_mode,
            optimization_mode_filter_messages=optimization_mode_filter_messages,
        )
        outs.append(renderer.render())
    return outs
