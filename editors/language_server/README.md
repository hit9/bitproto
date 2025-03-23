bitproto-language-server
========================

### Install

Requires: `Python >= 3.9`

```
pip install bitproto-language-server
```

### Install for Neovim

```lua
-- bitproto
local lspconfig_configs = require("lspconfig.configs")

-- Bind bitproto_language_server to lspconfig
if not lspconfig_configs.bitproto_language_server then
  lspconfig_configs.bitproto_language_server = {
    default_config = {
      name = "bitproto_language_server",
      cmd = {"bitproto-language-server"},
      filetypes = { 'bitproto' },
      root_dir = function(fname)
        return require('lspconfig').util.find_git_ancestor(fname) or vim.fn.getcwd()
      end,
    },
  }
end

-- setup bitproto
require('lspconfig').bitproto_language_server.setup{}
```

### Supported LSP Features:

- Goto Definition
- Hover to show comments.
- Completion for Enum/Message/Constant/Alias definitions.
- Simple Diagnostic (Push).
- DocumentSymbol (tree).
- Find References.

Currently Un-Supported, but may in plan:

- Inlay Hint
- Formatting
