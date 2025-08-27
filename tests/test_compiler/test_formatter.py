from bitproto._ast import Constant, IntegerConstant, Alias, Enum, EnumField, Message
from bitproto.renderer.formatter import CaseStyleMapping
from bitproto.parser import parse_string
from bitproto.renderer.impls import renderer_registry


def test_case_style_mapping():
    d = CaseStyleMapping(
        {
            Constant: "upper",
            Alias: "pascal",
            Enum: "pascal",
            EnumField: ("snake", "upper"),
            Message: "pascal",
        }
    )

    assert d[Constant] == "upper"
    assert d[IntegerConstant] == "upper"
    assert d[Message] == "pascal"


def test_issue_70():
    proto_string = """
    proto example
    option c.name_prefix = "lowercase"
    const my_const = 42;
    """
    proto = parse_string(proto_string)

    for lang, expect in [
        ("c", "LOWERCASEMY_CONST"),
        ("go", "MY_CONST"),  # before this fix: my_const
        ("py", "MY_CONST"),  # before this fix: my_const
    ]:
        render_class_s = renderer_registry[lang]

        found = False
        for render_class in render_class_s:
            renderer = render_class(proto)
            out_string = renderer.render_string()
            if expect in out_string:
                found = True
                break

        assert found
