from ply import yacc
from lexer import tokens
from semantic import CompilerState
from utils.errors import SyntaxCompilerError

precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("nonassoc", "EQUALITY", "INEQUALITY"),
    ("nonassoc", "LESS_THAN", "LESS_EQUAL", "GREATER_THAN", "GREATER_EQUAL"),
    ("left", "PLUS", "MINUS"),
    ("left", "MULTIPLY", "DIVIDE"),
    ("right", "UMINUS"),
)

compiler = CompilerState()


def reset_compiler():
    global compiler
    compiler = CompilerState()
    return compiler


def p_program(p):
    """
    program : PROGRAM MAIN L_CURLY_BRACE declaration_list main_goto function_declaration_list main_start begin_block R_CURLY_BRACE
    """

    compiler.validate_function_calls()
    print("Program parsed successfully")


def p_declaration(p):
    """
    declaration : VAR id_list COLON type SEMICOLON
    """

    for var_name in p[2]:
        compiler.declare_variable(var_name, p[4], p.lineno(1))


def p_declaration_list(p):
    """
    declaration_list : declaration declaration_list
                     | empty
    """


def p_id_list_single(p):
    """
    id_list : ID
    """

    p[0] = [p[1]]


def p_id_list_multiple(p):
    """
    id_list : ID COMMA id_list
    """

    p[0] = [p[1]] + p[3]


def p_type(p):
    """
    type : INT_DECLARATION
         | FLOAT_DECLARATION
         | BOOL_DECLARATION
         | STRING_DECLARATION
         | CHAR_DECLARATION
    """

    from utils.types import token_to_type

    p[0] = token_to_type(p.slice[1].type)


def p_begin_block(p):
    """
    begin_block : BEGIN SEMICOLON statement_list END SEMICOLON
    """


def p_main_goto(p):
    """
    main_goto :
    """

    compiler.emit_main_goto()


def p_main_start(p):
    """
    main_start :
    """

    compiler.patch_main_start()


def p_function_declaration_list(p):
    """
    function_declaration_list : function_declaration function_declaration_list
                              | empty
    """


def p_function_declaration(p):
    """
    function_declaration : FUNCTION ID register_function L_PARENTHESIS R_PARENTHESIS L_CURLY_BRACE begin_block R_CURLY_BRACE
    """

    compiler.generate_function_end()


def p_register_function(p):
    """
    register_function :
    """

    compiler.register_function(p[-1], p.lineno(-1))


def p_statement_list(p):
    """
    statement_list : statement statement_list
                   | empty
    """


def p_statement(p):
    """
    statement : assignment
              | function_call
              | for
              | write
              | if
              | while
              | expression SEMICOLON
    """


def p_assignment(p):
    """
    assignment : ID ASSIGN expression SEMICOLON
    """

    compiler.generate_assignment(p[1], p.lineno(1))


def p_write(p):
    """
    write : WRITE L_PARENTHESIS expression R_PARENTHESIS SEMICOLON
    """

    compiler.generate_write()


def p_function_call(p):
    """
    function_call : ID L_PARENTHESIS R_PARENTHESIS SEMICOLON
    """

    compiler.generate_function_call(p[1], p.lineno(1))


def p_if(p):
    """
    if : IF L_PARENTHESIS expression R_PARENTHESIS if_condition THEN L_CURLY_BRACE statement_list R_CURLY_BRACE else_block
    """


def p_if_condition(p):
    """
    if_condition :
    """

    compiler.generate_gotof()


def p_else_block(p):
    """
    else_block : ELSE else_jump L_CURLY_BRACE statement_list R_CURLY_BRACE
               | empty
    """

    compiler.patch_jump()


def p_else_jump(p):
    """
    else_jump :
    """

    # Emit Goto (which will jump past the else block)
    idx = compiler.quads.emit("Goto", None, None, None)

    # Patch the GotoF from if_condition to jump to the start of else block
    # (which is the next instruction after Goto)
    gotof_idx = compiler.jumps.pop()
    compiler.quads.patch(gotof_idx, compiler.quads.current_index())

    # Push Goto index for patching at end of else_block
    compiler.jumps.push(idx)


def p_while(p):
    """
    while : WHILE while_start L_PARENTHESIS expression R_PARENTHESIS while_condition DO L_CURLY_BRACE statement_list R_CURLY_BRACE
    """
    compiler.generate_loop_end()


def p_while_start(p):
    """
    while_start :
    """

    compiler.save_jump_index()


def p_while_condition(p):
    """
    while_condition :
    """

    compiler.generate_gotof()


def p_for(p):
    """
    for : FOR L_PARENTHESIS assignment for_start expression for_condition SEMICOLON for_update_start expression for_update R_PARENTHESIS L_CURLY_BRACE statement_list R_CURLY_BRACE
    """

    compiler.generate_for_end()


def p_for_start(p):
    "for_start :"
    compiler.save_loop_start()


def p_for_condition(p):
    "for_condition :"
    compiler.generate_gotof()


def p_for_update_start(p):
    "for_update_start :"
    compiler.mark_for_update_start()


def p_for_update(p):
    "for_update :"
    compiler.save_for_update()


def p_expression(p):
    """
    expression : expression OR push_or relational_expression
               | expression AND push_and relational_expression
               | relational_expression
    """

    if len(p) > 2:
        compiler.check_and_generate(("and", "or"))


def p_relational_expression(p):
    """
    relational_expression : relational_expression LESS_THAN push_lt additive_expression
                          | relational_expression LESS_EQUAL push_le additive_expression
                          | relational_expression GREATER_THAN push_gt additive_expression
                          | relational_expression GREATER_EQUAL push_ge additive_expression
                          | relational_expression EQUALITY push_eq additive_expression
                          | relational_expression INEQUALITY push_ne additive_expression
                          | additive_expression
    """

    if len(p) > 2:
        compiler.check_and_generate(("<", "<=", ">", ">=", "==", "!="))


def p_additive_expression(p):
    """
    additive_expression : additive_expression PLUS push_plus term
                        | additive_expression MINUS push_minus term
                        | term
    """

    if len(p) > 2:
        compiler.check_and_generate(("+", "-"))


def p_term(p):
    """
    term : term MULTIPLY push_mult factor
         | term DIVIDE push_div factor
         | factor
    """

    if len(p) > 2:
        compiler.check_and_generate(("*", "/"))


def p_factor_expression(p):
    """
    factor : L_PARENTHESIS push_false_bottom expression R_PARENTHESIS pop_false_bottom
    """


def p_factor_operand(p):
    """
    factor : operand
    """


def p_factor_unary(p):
    """
    factor : unary_expression
    """


def p_operand_id(p):
    """
    operand : ID
    """

    compiler.push_variable(p[1], p.lineno(1))


def p_operand_cte(p):
    """
    operand : cte
    """


def p_cte_int(p):
    """
    cte : INT_CTE
    """

    compiler.push_constant(p[1], "INT_CTE", p.lineno(1))


def p_cte_float(p):
    """
    cte : FLOAT_CTE
    """

    compiler.push_constant(p[1], "FLOAT_CTE", p.lineno(1))


def p_cte_bool(p):
    """
    cte : BOOL_CTE
    """

    compiler.push_constant(p[1], "BOOL_CTE", p.lineno(1))


def p_cte_string(p):
    """
    cte : STRING_CTE
    """

    compiler.push_constant(p[1], "STRING_CTE", p.lineno(1))


def p_cte_char(p):
    """
    cte : CHAR_CTE
    """

    compiler.push_constant(p[1], "CHAR_CTE", p.lineno(1))


def p_unary_expression(p):
    """
    unary_expression : ID INCREMENT
                     | ID DECREMENT
    """

    op = p[2]
    compiler.emit_inc_dec(p[1], op, p.lineno(1), produce_value=True)


def p_factor_uminus(p):
    """
    factor : MINUS factor %prec UMINUS
    """

    compiler.generate_unary_minus(p.lineno(1))


def p_push_plus(p):
    "push_plus :"
    compiler.push_operator("+", p.lineno(-1))


def p_push_minus(p):
    "push_minus :"
    compiler.push_operator("-", p.lineno(-1))


def p_push_mult(p):
    "push_mult :"
    compiler.push_operator("*", p.lineno(-1))


def p_push_div(p):
    "push_div :"
    compiler.push_operator("/", p.lineno(-1))


def p_push_lt(p):
    "push_lt :"
    compiler.push_operator("<", p.lineno(-1))


def p_push_le(p):
    "push_le :"
    compiler.push_operator("<=", p.lineno(-1))


def p_push_gt(p):
    "push_gt :"
    compiler.push_operator(">", p.lineno(-1))


def p_push_ge(p):
    "push_ge :"
    compiler.push_operator(">=", p.lineno(-1))


def p_push_eq(p):
    "push_eq :"
    compiler.push_operator("==", p.lineno(-1))


def p_push_ne(p):
    "push_ne :"
    compiler.push_operator("!=", p.lineno(-1))


def p_push_and(p):
    "push_and :"
    compiler.push_operator("and", p.lineno(-1))


def p_push_or(p):
    "push_or :"
    compiler.push_operator("or", p.lineno(-1))


def p_push_false_bottom(p):
    """
    push_false_bottom :
    """

    compiler.push_false_bottom()


def p_pop_false_bottom(p):
    """
    pop_false_bottom :
    """

    compiler.pop_false_bottom()


def p_empty(p):
    """
    empty :
    """


def _find_column(source: str, lexpos: int) -> int:
    line_start = source.rfind("\n", 0, lexpos) + 1
    return lexpos - line_start + 1


TOKEN_DISPLAY_NAMES = {
    "PROGRAM": "'program'",
    "MAIN": "'main'",
    "VAR": "'var'",
    "BEGIN": "'begin'",
    "END": "'end'",
    "WRITE": "'write'",
    "IF": "'if'",
    "THEN": "'then'",
    "AND": "'and'",
    "OR": "'or'",
    "ELSE": "'else'",
    "FOR": "'for'",
    "WHILE": "'while'",
    "DO": "'do'",
    "FUNCTION": "'function'",
    "INT_DECLARATION": "'int'",
    "FLOAT_DECLARATION": "'float'",
    "BOOL_DECLARATION": "'bool'",
    "STRING_DECLARATION": "'string'",
    "CHAR_DECLARATION": "'char'",
    "ID": "identifier",
    "INT_CTE": "integer literal",
    "FLOAT_CTE": "float literal",
    "BOOL_CTE": "boolean literal",
    "STRING_CTE": "string literal",
    "CHAR_CTE": "char literal",
    "INCREMENT": "'++'",
    "DECREMENT": "'--'",
    "PLUS": "'+'",
    "MINUS": "'-'",
    "MULTIPLY": "'*'",
    "DIVIDE": "'/'",
    "SEMICOLON": "';'",
    "COLON": "':'",
    "COMMA": "','",
    "L_PARENTHESIS": "'('",
    "R_PARENTHESIS": "')'",
    "L_CURLY_BRACE": "'{'",
    "R_CURLY_BRACE": "'}'",
    "EQUALITY": "'=='",
    "ASSIGN": "':='",
    "INEQUALITY": "'!='",
    "LESS_EQUAL": "'<='",
    "GREATER_EQUAL": "'>='",
    "LESS_THAN": "'<'",
    "GREATER_THAN": "'>'",
    "$end": "end of file",
}


def _expected_tokens():
    try:
        state = parser.statestack[-1]
        actions = parser.action.get(state, {})
    except (AttributeError, IndexError, NameError):
        return []

    expected = []
    for token_name, action in actions.items():
        if action:
            expected.append(token_name)

    priority = {
        "SEMICOLON": 0,
        "R_PARENTHESIS": 1,
        "R_CURLY_BRACE": 2,
        "L_CURLY_BRACE": 3,
        "THEN": 4,
        "DO": 5,
        "$end": 6,
    }

    return sorted(set(expected), key=lambda token: (priority.get(token, 100), token))


def _format_expected_tokens(expected):
    if not expected:
        return ""

    displayed = [TOKEN_DISPLAY_NAMES.get(token, token) for token in expected]
    hint = ""
    if "SEMICOLON" in expected:
        hint = " A semicolon may be missing before this token."

    if len(expected) == 1:
        return f" Expected {displayed[0]}.{hint}"

    if len(expected) <= 14:
        return f" Expected one of: {', '.join(displayed)}.{hint}"

    shown = ", ".join(displayed[:14])
    return f" Expected one of: {shown}, ... ({len(expected)} possible tokens).{hint}"


def p_error(p):
    if p:
        column = _find_column(p.lexer.lexdata, p.lexpos)
        expected = _format_expected_tokens(_expected_tokens())
        raise SyntaxCompilerError(
            f"Unexpected token '{p.value}'.{expected}", p.lineno, column
        )
    else:
        expected = _format_expected_tokens(_expected_tokens())
        raise SyntaxCompilerError(f"Unexpected end of file.{expected}")


parser = yacc.yacc()
