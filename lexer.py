from ply import lex

reserved = {
    "program": "PROGRAM",
    "main": "MAIN",
    "var": "VAR",
    "int": "INT_DECLARATION",
    "float": "FLOAT_DECLARATION",
    "bool": "BOOL_DECLARATION",
    "string": "STRING_DECLARATION",
    "char": "CHAR_DECLARATION",
    "begin": "BEGIN",
    "end": "END",
    "write": "WRITE",
    "if": "IF",
    "then": "THEN",
    "and": "AND",
    "or": "OR",
    "do": "DO",
    "else": "ELSE",
    "for": "FOR",
    "while": "WHILE",
    "true": "BOOL_CTE",
    "false": "BOOL_CTE",
}

tokens = [
    "ID",
    "FLOAT_CTE",
    "INT_CTE",
    "STRING_CTE",
    "CHAR_CTE",
    "INCREMENT",
    "DECREMENT",
    "PLUS",
    "MINUS",
    "MULTIPLY",
    "DIVIDE",
    "SEMICOLON",
    "COLON",
    "COMMA",
    "L_PARENTHESIS",
    "R_PARENTHESIS",
    "L_CURLY_BRACE",
    "R_CURLY_BRACE",
    "EQUALITY",
    "ASSIGN",
    "INEQUALITY",
    "LESS_EQUAL",
    "GREATER_EQUAL",
    "LESS_THAN",
    "GREATER_THAN",
]

tokens = tokens + list(set(reserved.values()))

t_INCREMENT = r"\+\+"
t_DECREMENT = r"--"
t_PLUS = r"\+"
t_MINUS = r"-"
t_MULTIPLY = r"\*"
t_DIVIDE = r"/"
t_SEMICOLON = r";"
t_ASSIGN = r":="
t_COLON = r":"
t_COMMA = r","
t_L_PARENTHESIS = r"\("
t_R_PARENTHESIS = r"\)"
t_L_CURLY_BRACE = r"\{"
t_R_CURLY_BRACE = r"\}"
t_EQUALITY = r"=="
t_INEQUALITY = r"!="
t_LESS_EQUAL = r"<="
t_GREATER_EQUAL = r">="
t_LESS_THAN = r"<"
t_GREATER_THAN = r">"


def t_ID(t):
    r"[a-zA-Z_][a-zA-Z_0-9]*"
    t.type = reserved.get(t.value, "ID")
    if t.type == "BOOL_CTE":
        t.value = True if t.value == "true" else False
    return t


def t_FLOAT_CTE(t):
    r"\d+\.\d+"
    t.value = float(t.value)
    return t


def t_INT_CTE(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_STRING_CTE(t):
    r'"[^"]*"'
    t.value = str(t.value)
    return t


def t_CHAR_CTE(t):
    r"\'.\'"
    t.value = str(t.value)
    return t


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


t_ignore = " \t"


def t_error(t):
    print(f"ERROR: Illegal character '{t.value[0]}' at line number {t.lineno}")
    t.lexer.skip(1)


lexer = lex.lex()
