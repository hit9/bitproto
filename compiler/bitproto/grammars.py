"""
bitproto.grammars
~~~~~~~~~~~~~~~~~

Grammar rules.
"""

# fmt: off

r_optional_semicolon = """
optional_semicolon : ';'
                   |
"""

r_start = """
start : open_global_scope global_scope close_global_scope
"""

r_open_global_scope = """
open_global_scope :
"""

r_close_global_scope = """
close_global_scope :
"""

r_global_scope = """
global_scope : global_scope_definitions
"""

r_global_scope_definitions = """
global_scope_definitions : global_scope_definition_unit global_scope_definitions
                         | global_scope_definition_unit
                         |
"""

r_global_scope_definition_unit = """
global_scope_definition_unit : import
                             | option
                             | alias
                             | const
                             | enum
                             | message
                             | proto
                             | comment
                             | newline
"""

r_proto = """
proto : PROTO IDENTIFIER optional_semicolon
"""

r_comment = """
comment : COMMENT NEWLINE
"""

r_newline = """
newline : NEWLINE
"""

r_import = """
import : IMPORT STRING_LITERAL optional_semicolon
       | IMPORT IDENTIFIER STRING_LITERAL optional_semicolon
"""

r_option = """
option : OPTION dotted_identifier '=' option_value optional_semicolon
"""

r_option_value = """
option_value : boolean_literal
             | integer_literal
             | string_literal
"""

r_alias = """
alias : TYPE IDENTIFIER '=' type optional_semicolon
      | TYPEDEF type IDENTIFIER optional_semicolon
"""

r_const = """
const : CONST IDENTIFIER '=' const_value optional_semicolon
"""

r_const_value = """
const_value : boolean_literal
            | string_literal
            | constant_reference
            | calculation_expression
"""

r_calculation_expression = """
calculation_expression : calculation_expression_plus
                       | calculation_expression_minus
                       | calculation_expression_times
                       | calculation_expression_divide
                       | calculation_expression_group
                       | integer_literal
                       | constant_reference_for_calculation
"""

r_calculation_expression_plus = """
calculation_expression_plus : calculation_expression PLUS calculation_expression
"""
r_calculation_expression_minus = """
calculation_expression_minus : calculation_expression MINUS calculation_expression
"""
r_calculation_expression_times = """
calculation_expression_times : calculation_expression TIMES calculation_expression
"""
r_calculation_expression_divide = """
calculation_expression_divide : calculation_expression DIVIDE calculation_expression
"""

r_calculation_expression_group = """
calculation_expression_group : '(' calculation_expression ')'
"""

r_constant_reference_for_calculation = """
constant_reference_for_calculation : constant_reference
"""

r_constant_reference = """
constant_reference : dotted_identifier
"""

r_type = """
type : single_type
     | array_type
"""

r_single_type = """
single_type : base_type
            | type_reference
"""

r_base_type = """
base_type : BOOL_TYPE
          | UINT_TYPE
          | INT_TYPE
          | BYTE_TYPE
"""

r_type_reference = """
type_reference : dotted_identifier
"""

r_optional_extensible_flag = """
optional_extensible_flag : "'"
                         |
"""

r_array_type = """
array_type : single_type '[' array_capacity ']' optional_extensible_flag
"""

r_array_capacity = """
array_capacity : INT_LITERAL
               | constant_reference_for_array_capacity
"""

r_constant_reference_for_array_capacity = """
constant_reference_for_array_capacity : constant_reference
"""

r_enum = """
enum : open_enum_scope enum_scope close_enum_scope
"""
r_open_enum_scope = """
open_enum_scope : ENUM IDENTIFIER ':' UINT_TYPE '{'
"""
r_enum_scope = """
enum_scope : enum_items
"""

r_close_enum_scope = """
close_enum_scope : '}'
"""

r_enum_items = """
enum_items : enum_item enum_items
           | enum_item
           |
"""

r_enum_item = """
enum_item : enum_field
          | enum_item_unsupported
          | comment
          | newline
"""

r_enum_item_unsupported = """
enum_item_unsupported : alias
                      | const
                      | proto
                      | import
                      | option
                      | enum
                      | message
                      | message_field
"""

r_enum_field = """
enum_field : IDENTIFIER '=' integer_literal optional_semicolon
"""

r_message = """
message : open_message_scope message_scope close_message_scope
"""

r_open_message_scope = """
open_message_scope : MESSAGE IDENTIFIER optional_extensible_flag '{'
"""

r_close_message_scope = """
close_message_scope : '}'
"""

r_message_scope = """
message_scope : message_items
"""

r_message_items = """
message_items : message_item message_items
              | message_item
              |
"""

r_message_item = """
message_item : option
             | enum
             | message_field
             | message
             | message_item_unsupported
             | comment
             | newline
"""

r_message_item_unsupported = """
message_item_unsupported : alias
                         | const
                         | proto
                         | import
"""

r_message_field = """
message_field : type message_field_name '=' INT_LITERAL optional_semicolon
"""

# https://github.com/hit9/bitproto/issues/39
# Allow some keywords to be message names.
r_message_field_name = """
message_field_name : IDENTIFIER
                   | TYPE
"""

r_boolean_literal = """
boolean_literal : BOOL_LITERAL
"""

r_integer_literal = """
integer_literal : INT_LITERAL
                | HEX_LITERAL
"""

r_string_literal = """
string_literal : STRING_LITERAL
"""

r_dotted_identifier = """
dotted_identifier : IDENTIFIER '.' dotted_identifier
                  | IDENTIFIER
"""
# fmt: on
