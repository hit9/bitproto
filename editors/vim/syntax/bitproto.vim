if version < 600
    syntax clear
elseif exists("b:current_syntax")
    finish
endif

syn case match

syn keyword bitprotoInCommentMarks contained TODO FIXME NOTE BUG XXX
syn cluster bitprotoCommentGroup contains=bitprotoInCommentMarks

syn keyword bitprotoProtoName    proto
syn keyword bitprotoImport       import
syn keyword bitprotoEnum         enum
syn keyword bitprotoMessage      message
syn keyword bitprotoOption       option
syn keyword bitprotoAlias        type
syn keyword bitprotoConstant     const
syn keyword bitprotoBoolType     bool
syn keyword bitprotoByteType     byte
syn match bitprotoUintType       /\<uint[0-9]\+\>/
syn match bitprotoIntType        /\<int[0-9]\+\>/
syn keyword bitprotoBoolConstant true false yes no
syn match bitprotoIntHexConstant /\<0x[0-9A-Fa-f]\+\>/
syn match bitprotoIntConstant    /\<[0-9]\+\>/
syn match bitprotoAliasName       /\<\(type\s\+\)\@<=\(\w\+\)\s*\>/
syn match bitprotoEnumName       /\<\(enum\s\+\)\@<=\(\w\+\)\s*\>/
syn match bitprotoMessageName    /\<\(message\s\+\)\@<=\(\w\+\)\s*\>/
syn match bitprotoConstantName   /\<\(const\s\+\)\@<=\(\w\+\)\s*\>/
syn match bitprotoOptionName     /\<\(option\s\+\)\@<=\(\w\+[\.]\w*\)\s*\>/
syn match bitprotoOperator       '\V=\|+\|-\|*\|/\|\'\|:'
syn match bitprotoSemicolon      ';'
syn region bitprotoComment start="//" skip="\\$" end="$" keepend contains=@bitprotoCommentGroup
syn region bitprotoStringConstant  start=/"/ skip=/\\./ end=/"/

command -nargs=+ HiLink hi def link <args>
HiLink bitprotoInCommentMarks Todo
HiLink bitprotoImport         Include
HiLink bitprotoProtoName      Keyword
HiLink bitprotoEnum           Keyword
HiLink bitprotoMessage        Keyword
HiLink bitprotoOption         Keyword
HiLink bitprotoAlias          Keyword
HiLink bitprotoConstant       Keyword
HiLink bitprotoBoolType       Type
HiLink bitprotoByteType       Type
HiLink bitprotoUintType       Type
HiLink bitprotoIntType        Type
HiLink bitprotoIntConstant    Number
HiLink bitprotoIntHexConstant Number
HiLink bitprotoStringConstant String
HiLink bitprotoComment        Comment
HiLink bitprotoBoolConstant   Boolean
HiLink bitprotoAliasName      Identifier
HiLink bitprotoEnumName       Identifier
HiLink bitprotoMessageName    Identifier
HiLink bitprotoConstantName   Identifier
HiLink bitprotoOptionName     Identifier
HiLink bitprotoOperator       Operator
HiLink bitprotoSemicolon      Comment
delcommand HiLink

let b:current_syntax = "bitproto"
