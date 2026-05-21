from ply import yacc
from lexer import tokens

precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("nonassoc", "EQUALITY", "INEQUALITY"),
    ("nonassoc", "LESS_THAN", "LESS_EQUAL", "GREATER_THAN", "GREATER_EQUAL"),
    ("left", "PLUS", "MINUS"),
    ("left", "MULTIPLY", "DIVIDE"),
)


def p_program(p):
    """program: PROGRAM MAIN L_CURLY_BRACE declaration_list begin_block R_CURLY_BRACE"""


def p_declaration(p):
    """declaration: VAR id_list COLON type SEMICOLON"""


def p_declaration_list(p):
    """declaration_list: declaration
    | declaration declaration_list
    | empty"""


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
    """begin_block: BEGIN SEMICOLON statement_list END SEMICOLON
    | empty"""


def p_statement(p):
    """statement: expression SEMICOLON
    | assignment
    | for
    | while
    | if
    | write"""


def p_statement_list(p):
    """statement_list: statement
    | statement statement_list"""


def p_expression(p):
    """expression : expression PLUS expression
    | expression MINUS expression
    | expression MULTIPLY expression
    | expression DIVIDE expression
    | expression EQUALITY expression
    | expression INEQUALITY expression
    | expression LESS_THAN expression
    | expression LESS_EQUAL expression
    | expression GREATER_THAN expression
    | expression GREATER_EQUAL expression
    | expression AND expression
    | expression OR expression
    | unary_expression
    | operand"""


def p_unary_expression(p):
    """unary_expression: ID INCREMENT
    | ID DECREMENT"""


def p_operand(p):
    """operand: ID
    | cte
    | L_PARENTHESIS expression R_PARENTHESIS"""


def p_cte(p):
    """cte: FLOAT_CTE
    | INT_CTE
    | BOOL_CTE
    | STRING_CTE
    | CHAR_CTE"""


def p_assignment(p):
    """assignment: ID ASSIGN expression SEMICOLON"""


def p_write(p):
    """write: WRITE L_PARENTHESIS expression R_PARENTHESIS SEMICOLON"""


def p_while(p):
    """while: WHILE L_PARENTHESIS expression R_PARENTHESIS DO L_CURLY_BRACE statement_list R_CURLY_BRACE"""


def p_for(p):
    """for: FOR L_PARENTHESIS assignment expression SEMICOLON expression R_PARENTHESIS L_CURLY_BRACE statement_list R_CURLY_BRACE"""


def p_if(p):
    """if: IF L_PARENTHESIS expression R_PARENTHESIS THEN L_CURLY_BRACE statement_list R_CURLY_BRACE else_block"""


def p_else_block(p):
    """else_block: ELSE L_CURLY_BRACE statement_list R_CURLY_BRACE
    | empty"""


def p_empty(p):
    """empty:"""
    pass


parser = yacc.yacc()
