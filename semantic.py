"""
CompilerState
=============
Central utility class for semantic actions inside parser rules.
Implements the stack-based quadruple generation, including the FALSE_BOTTOM marker for
parenthesized expressions.
"""

from utils.stack import Stack, FALSE_BOTTOM
from utils.types import Type, result_type, is_compatible_assign, token_to_type
from utils.errors import SemanticError as CompilerError, TypeError, AssignmentTypeError
from symbol_table import SymbolTable
from quadruples import QuadrupleList
from virtual_memory import VirtualMemory


class CompilerState:
    def __init__(self):
        self.memory = VirtualMemory()
        self.symbols = SymbolTable(self.memory)
        self.quads = QuadrupleList()
        self.pending_for_increments = Stack()
        self.for_update_starts = Stack()
        self.functions = {}
        self.pending_function_calls = {}
        self.main_goto = None

        # Semantic stacks
        self.operands = Stack()  # variable addresses or temp names
        self.types = Stack()  # Type enum values parallel to operands
        self.operand_lines = Stack()
        self.operators = Stack()  # operator strings
        self.operator_lines = Stack()
        self.jumps = Stack()  # quadruple indices for jump patching

    # --- For loop ---------------------------------------------------------

    def build_increment_quad(self, var_name, lineno=None):
        symbol = self.symbols.lookup(var_name, lineno)

        if symbol.var_type not in (Type.INT, Type.FLOAT):
            raise CompilerError(
                f"Cannot increment variable of type '{symbol.var_type.value}'",
                lineno,
            )

        one_address = self.memory.alloc_const(1, Type.INT)
        return ("+", symbol.address, one_address, symbol.address)

    def build_decrement_quad(self, var_name, lineno=None):
        symbol = self.symbols.lookup(var_name, lineno)

        if symbol.var_type not in (Type.INT, Type.FLOAT):
            raise CompilerError(
                f"Cannot decrement variable of type '{symbol.var_type.value}'",
                lineno,
            )

        one_address = self.memory.alloc_const(1, Type.INT)
        return ("-", symbol.address, one_address, symbol.address)

    def emit_inc_dec(self, var_name, op, lineno=None, produce_value=False):
        """
        op: "++" or "--"
        produce_value: whether expression result is needed (post-increment)
        """
        # This lookup is what triggers UndeclaredVariableError
        symbol = self.symbols.lookup(var_name, lineno)

        if symbol.var_type not in (Type.INT, Type.FLOAT):
            raise CompilerError(
                f"Cannot apply '{op}' to variable of type '{symbol.var_type.value}'",
                lineno,
            )

        one_address = self.memory.alloc_const(1, Type.INT)
        actual_op = "+" if op == "++" else "-"

        if produce_value:
            # Save original value into a temp before modifying (post-increment semantics)
            temp = self.memory.alloc("temp", symbol.var_type)
            self.quads.emit(":=", symbol.address, None, temp)
            self.quads.emit(actual_op, symbol.address, one_address, symbol.address)
            self.operands.push(temp)
            self.types.push(symbol.var_type)
            self.operand_lines.push(lineno)
        else:
            # No result needed — just mutate in place
            self.quads.emit(actual_op, symbol.address, one_address, symbol.address)

    def emit_quad_tuple(self, quad):
        op, left, right, result = quad
        self.quads.emit(op, left, right, result)

    # ------------------------------------------------------------------
    # Helpers called from parser rules
    # ------------------------------------------------------------------

    # --- Variables & constants ----------------------------------------

    def push_variable(self, name: str, lineno: int = None):
        """Step 1 in pseudocode: PUSH pila-operandos(dirección de variable)"""
        symbol = self.symbols.lookup(name, lineno)
        self.operands.push(symbol.address)
        self.types.push(symbol.var_type)
        self.operand_lines.push(lineno)

    def push_constant(self, value, token_type: str, lineno: int = None):
        """Step 2 / 3 – push a literal constant."""
        const_type = token_to_type(token_type)
        address = self.memory.alloc_const(value, const_type)
        self.operands.push(address)
        self.types.push(const_type)
        self.operand_lines.push(lineno)

    def push_operator(self, op: str, lineno: int = None):
        """Step 2 / 3: PUSH pila-operadores(operador)"""
        self.operators.push(op)
        self.operator_lines.push(lineno)

    # --- False bottom (parentheses) -----------------------------------

    def push_false_bottom(self):
        """Step 6: PUSH pila-operadores(marca de fondo falso)"""
        self.operators.push(FALSE_BOTTOM)
        self.operator_lines.push(None)

    def pop_false_bottom(self):
        """Step 7: POP pila-operadores ... se quita marca de fondo falso"""
        if self.operators.top() == FALSE_BOTTOM:
            self.operators.pop()
            self.operator_lines.pop()

    # --- Expression evaluation ----------------------------------------

    def check_and_generate(self, trigger_ops: tuple):
        """
        Steps 4 / 5 / 9 in pseudocode.
        If the top of the operator stack matches one of `trigger_ops`,
        pop two operands and one operator, validate types via semantic
        cube, emit a quadruple, and push the result back.
        """
        if self.operators.top() in trigger_ops:
            self._generate_quadruple()

    def _generate_quadruple(self):

        if len(self.operands) < 2:
            raise CompilerError("Insufficient operands")

        if len(self.types) < 2:
            raise CompilerError("Insufficient type information")

        if self.operators.is_empty():
            raise CompilerError("Missing operator")

        right_val = self.operands.pop()
        right_type = self.types.pop()
        self.operand_lines.pop()

        left_val = self.operands.pop()
        left_type = self.types.pop()
        left_line = self.operand_lines.pop()

        operator = self.operators.pop()
        operator_line = self.operator_lines.pop()

        res_type = result_type(left_type, right_type, operator)

        if res_type == Type.ERROR:
            raise TypeError(left_type, operator, right_type, operator_line or left_line)

        temp = self.memory.alloc("temp", res_type)

        self.quads.emit(operator, left_val, right_val, temp)

        self.operands.push(temp)
        self.types.push(res_type)
        self.operand_lines.push(operator_line or left_line)

    # --- Assignment ---------------------------------------------------

    def generate_assignment(self, var_name: str, lineno: int = None):
        """
        After the RHS expression has been fully evaluated, pop the result
        and emit an assignment quadruple.
        """
        symbol = self.symbols.lookup(var_name, lineno)

        value = self.operands.pop()
        val_type = self.types.pop()
        self.operand_lines.pop()

        if not is_compatible_assign(symbol.var_type, val_type):
            raise AssignmentTypeError(var_name, symbol.var_type, val_type, lineno)

        self.quads.emit(":=", value, None, symbol.address)

    def generate_increment(self, var_name: str, lineno=None):
        symbol = self.symbols.lookup(var_name, lineno)

        if symbol.var_type not in (Type.INT, Type.FLOAT):
            raise CompilerError(
                f"Cannot increment variable of type '{symbol.var_type.value}'",
                lineno,
            )

        temp = self.memory.alloc("temp", symbol.var_type)
        self.quads.emit(":=", symbol.address, None, temp)

        one_address = self.memory.alloc_const(1, Type.INT)
        self.quads.emit("+", symbol.address, one_address, symbol.address)

        self.operands.push(temp)
        self.types.push(symbol.var_type)
        self.operand_lines.push(lineno)

    def generate_decrement(self, var_name: str, lineno=None):
        symbol = self.symbols.lookup(var_name, lineno)

        if symbol.var_type not in (Type.INT, Type.FLOAT):
            raise CompilerError(
                f"Cannot decrement variable of type '{symbol.var_type.value}'",
                lineno,
            )

        temp = self.memory.alloc("temp", symbol.var_type)
        self.quads.emit(":=", symbol.address, None, temp)

        one_address = self.memory.alloc_const(1, Type.INT)
        self.quads.emit("-", symbol.address, one_address, symbol.address)

        self.operands.push(temp)
        self.types.push(symbol.var_type)
        self.operand_lines.push(lineno)

    def generate_unary_minus(self, lineno: int = None):

        value = self.operands.pop()
        value_type = self.types.pop()
        value_line = self.operand_lines.pop()

        if value_type not in (Type.INT, Type.FLOAT):
            raise CompilerError(
                f"Unary minus not supported for type '{value_type.value}'",
                lineno or value_line,
            )

        temp = self.memory.alloc("temp", value_type)

        self.quads.emit("NEG", value, None, temp)

        self.operands.push(temp)
        self.types.push(value_type)
        self.operand_lines.push(lineno or value_line)

    # --- Control flow -------------------------------------------------

    def generate_gotof(self, lineno: int = None):

        expr_type = self.types.pop()
        expr_line = self.operand_lines.pop()

        if expr_type != Type.BOOL:
            raise CompilerError(
                "Conditional expression must be boolean", lineno or expr_line
            )

        condition = self.operands.pop()

        idx = self.quads.emit("GotoF", condition, None, None)

        self.jumps.push(idx)

    def generate_goto(self):
        """Emit an unconditional Goto (for else / loop end) and push its index."""
        idx = self.quads.emit("Goto", None, None, None)
        self.jumps.push(idx)

    def patch_jump(self):
        """Patch the most recent pending jump to point to the current quad index."""
        idx = self.jumps.pop()
        self.quads.patch(idx, self.quads.current_index())

    def save_jump_index(self):
        """Save the current quad index as a loop-back target (for while/for)."""
        self.jumps.push(self.quads.current_index())

    def generate_loop_end(self):
        """
        Emit Goto back to the saved loop start, then patch the GotoF
        that was emitted at the loop condition.

        Jumps stack at this point (top -> bottom):
            GotoF index   <- pushed by generate_gotof
            loop_start    <- pushed by save_jump_index
        """
        gotof_idx = self.jumps.pop()
        loop_start = self.jumps.pop()
        self.quads.emit("Goto", None, None, loop_start)
        self.quads.patch(gotof_idx, self.quads.current_index())

    # --- Functions ----------------------------------------------------

    def emit_main_goto(self):
        self.main_goto = self.quads.emit("Goto", None, None, None)

    def patch_main_start(self):
        if self.main_goto is not None:
            self.quads.patch(self.main_goto, self.quads.current_index())

    def register_function(self, name: str, lineno: int = None):
        if name in self.functions:
            raise CompilerError(f"Function '{name}' already declared", lineno)

        if self.symbols.exists(name):
            raise CompilerError(
                f"Function '{name}' conflicts with an existing variable", lineno
            )

        start = self.quads.current_index()
        self.functions[name] = start

        for call_idx, _lineno in self.pending_function_calls.pop(name, []):
            self.quads.patch(call_idx, start)

    def generate_function_end(self):
        self.quads.emit("EndFunc", None, None, None)

    def generate_function_call(self, name: str, lineno: int = None):
        if name in self.functions:
            target = self.functions[name]
        else:
            target = None

        idx = self.quads.emit("Gosub", None, None, target)

        if target is None:
            self.pending_function_calls.setdefault(name, []).append((idx, lineno))

    def validate_function_calls(self):
        if self.pending_function_calls:
            name = next(iter(self.pending_function_calls))
            _call_idx, lineno = self.pending_function_calls[name][0]
            raise CompilerError(f"Function '{name}' called before declaration", lineno)

    # --- Write --------------------------------------------------------

    def generate_write(self):
        value = self.operands.pop()
        self.types.pop()
        self.operand_lines.pop()
        self.quads.emit("Write", value, None, None)

    # --- Variable declaration ----------------------------------------

    def declare_variable(self, name: str, var_type: Type, lineno: int = None):
        self.symbols.declare(name, var_type, lineno)

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def dump(self):
        print("=== Symbol Table ===")
        print(self.symbols)
        print("\n=== Quadruples ===")
        print(self.quads)

    def save_loop_start(self):
        self.jumps.push(self.quads.current_index())

    def mark_for_update_start(self):
        self.for_update_starts.push(self.quads.current_index())

    def save_for_update(self):
        if not self.operands.is_empty():
            self.operands.pop()
            self.types.pop()
            self.operand_lines.pop()

        update_start = self.for_update_starts.pop()
        update_quads = self.quads.extract_from(update_start)
        self.pending_for_increments.push(update_quads)

    def generate_for_end(self):
        """
        FOR loop finalization:
        - move the update expression after the body
        - jump back to loop start
        - patch GotoF
        """

        update_quads = self.pending_for_increments.pop()
        self.quads.extend(update_quads)

        gotof_idx = self.jumps.pop()
        loop_start = self.jumps.pop()
        self.quads.emit("Goto", None, None, loop_start)
        self.quads.patch(gotof_idx, self.quads.current_index())
