.. currentmodule:: bitproto

Version 1.3.1
-------------

.. _version-1.3.1:

- Bugfix: Extend ``BP_BIG_ENDIAN`` auto-detection to recognise ``__BIG_ENDIAN__``
  in addition to ``__BYTE_ORDER__``, covering the TI ARM CGT compiler (``--be32``
  on big-endian targets such as the TMS570). This applies to both the
  optimization-mode generated code and the standard-mode C library; previously
  these targets fell through to the little-endian path and produced incorrect
  results for multi-byte fields. PR #84.
- Packaging: Show the project README as the long description on the PyPI project
  page for the ``bitproto`` package.

Version 1.3.0
-------------

.. _version-1.3.0:

- Feature: Big-endian host support. bitproto's wire format is little-endian on
  every platform; the C library (standard mode) and the C optimization-mode
  generated code now also produce correct output when compiled for a big-endian
  host. Python and Go were already endian-neutral and unaffected.
- Feature: New compiler option ``--endian`` (``both`` | ``little`` | ``big``)
  controlling the host byte order targeted by optimization-mode C/C++ code.
  The default ``both`` emits both code paths guarded by ``#ifdef BP_BIG_ENDIAN``
  and auto-detects the host (overridable by defining ``BP_BIG_ENDIAN``);
  ``little`` keeps only the original, smaller and faster byte-pointer code (no
  big-endian support); ``big`` emits only the portable path.
- The little-endian generated code is unchanged from previous releases, so there
  is no performance regression on the common little-endian target.

Version 1.2.2
-------------

.. _version-1.2.2:

Warning: May break some existing projects's generated names:

- Improve `snake_case` function. #74, #75

Version 1.2.1
-------------

.. _version-1.2.1:

Warning: May break some existing projects's generated names:

- Bugfix: `pascal_case` formatter. ISSUE #68, PR #69.
- Bugfix: Fixed naming style of generated code such as IntegerConstant (style lookup supports inheritance). ISSUE #70 PR #70


Version 1.2.0
-------------

.. _version-1.2.0:

- Feature: Add a simple language-server, tested on neovim and vscode.
- Editor:  Upgrade vscode extenions to support the ``bitproto-language-server``.

Version 1.1.2
-------------

.. _version-1.1.2:

- Feature: Allow using constants as option values. ISSUE #61, PR #63

Version 1.1.1
-------------

.. _version-1.1.1:

- Fix bug: enum importing other bitproto's field name generation bug. #53 #52
- Fix bug: import statements of bitprotos should be placed ahead of other declarations. #53

Version 1.1.0
-------------

.. _version-1.1.0:

- Performance improvements for C bitprotolib, 40~60us improvement per call on stm32. PR #48.
- Fix Python nested message ``__post_init___`` function code generation. PR #48, commit 73f4b01.

Version 1.0.1
-------------

.. _version-1.0.1:

- Add support for Python 3.11

Version 1.0.0
-------------

.. _version-1.0.0:

- First fully release version

.. _version-0.4.6:

Version 0.4.6
-------------

- Support signed integers with arbitrary bits, e.g. int24 PR#45.

.. _version-0.4.5:

Version 0.4.5
-------------

- Use Python IntEnum for enum generation (respecting backward compatibility)  PR#41.

.. _version-0.4.4:

Version 0.4.4
-------------

- Minor fix compiler setup.py path issue.

.. _version-0.4.2:

Version 0.4.2
-------------

- Allow using ``type`` as message field name, fixes issue #39.

.. _version-0.4.0:

Version 0.4.0
-------------

- Add support for ``message`` and ``enum`` extensiblity for protocol forward compatibility.
- Cut down the code size of generated language-specific files.
- Refactor the bitproto compiler.
- Refactor the bitproto serialization mechanism, using language-specific libraries instead of pure compiler-generated files.
