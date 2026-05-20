from ply import yacc
from lexer import tokens


def p_program(p):
    """program: PROGRAM MAIN L_CURLY_BRACE declaration_list begin_block R_CURLY_BRACE"""


def p_declaration_list(p):
    """declaration_list: declaration
    | declaration declaration_list
    | empty"""


def p_declaration(p):
    """declaration: VAR id_list COLON type SEMICOLON"""


def p_id_list(p):
    """id_list: ID
    | ID COMMA id_list"""


def p_type(p):
    """type: INT_DECLARATION
    | FLOAT_DECLARATION
    | BOOL_DECLARATION
    | STRING_DECLARATION
    | CHAR_DECLARATION"""


def p_begin_block(p):
    """begin_block: BEGIN SEMICOLON statements END SEMICOLON
    | empty"""


def p_statements(p):
    pass


def p_empty(p):
    """empty:"""
    pass
