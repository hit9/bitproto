import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from _pygments import *

project = "bitproto"
copyright = "2021, Chao Wang"
author = "Chao Wang"
version = "0.4.4"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "alabaster"
html_static_path = ["_static"]
source_suffix = ".rst"
html_theme_options = {
    "logo": "bitproto-logo.png",
    "logo_name": False,
    "github_user": "hit9",
    "github_repo": "bitproto",
    "github_banner": False,
    "github_type": "star",
    "github_count": True,
    "fixed_sidebar": True,
    "extra_nav_links": {
        "bitproto @ github": "https://github.com/hit9/bitproto",
        "bitproto @ pypi": "https://pypi.org/project/bitproto",
        "bitprotolib (c)": "https://github.com/hit9/bitproto/tree/master/lib/c",
        "bitprotolib (go)": "https://github.com/hit9/bitproto/tree/master/lib/go",
        "bitprotolib (python)": "https://pypi.org/project/bitprotolib",
        "editor plugins": "https://github.com/hit9/bitproto/tree/master/editors",
        "中文文档": "https://bitproto.readthedocs.io/zh/latest",
    },
}
pygments_style = "_pygments.BitprotoStyle"

locale_dirs = ["locales/"]
gettext_uuid = True
gettext_compact = False
