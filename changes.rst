.. currentmodule:: bitproto

Version 1.1.0
-------------

.. _version-1.1.0

- Performance improvements for C bitprotolib, 30~40us improvement on stm32. PR #48.
- Fix Python nested message `__post_init___` function code generation. PR #48, commit 73f4b01.

Version 1.0.1
-------------

.. _version-1.0.1

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

- Add support for ``message`` and ``enum`` extensiblity for protocol backward compatibility.
- Cut down the code size of generated language-specific files.
- Refactor the bitproto compiler.
- Refactor the bitproto serialization mechanism, using language-specific libraries instead of pure compiler-generated files.
