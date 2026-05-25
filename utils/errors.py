_source_lines = []
_source_name = None


def set_error_source(source: str, source_name: str = None):
    """Register source text so compiler errors can show line context."""
    global _source_lines, _source_name
    _source_lines = source.splitlines()
    _source_name = source_name


def clear_error_source():
    """Remove source context used for compiler error messages."""
    global _source_lines, _source_name
    _source_lines = []
    _source_name = None


def _format_source_context(lineno: int, column: int = None) -> str:
    if not lineno or lineno < 1 or lineno > len(_source_lines):
        return ""

    line = _source_lines[lineno - 1]
    context = f"\n    {lineno:>4} | {line}"

    if column is not None and column > 0:
        context += f"\n         | {' ' * (column - 1)}^"

    return context


class CompilerError(Exception):
    """Base class for all compiler errors."""

    category = "Compiler Error"

    def __init__(self, message: str, lineno: int = None, column: int = None):
        self.message = message
        self.lineno = lineno
        self.column = column

        location_parts = []
        if _source_name:
            location_parts.append(str(_source_name))
        if lineno:
            location_parts.append(f"line {lineno}")
        if column:
            location_parts.append(f"col {column}")

        location = f" ({', '.join(location_parts)})" if location_parts else ""
        context = _format_source_context(lineno, column)

        super().__init__(f"[{self.category}]{location} {message}{context}")


class LexicalError(CompilerError):
    """Raised when the lexer finds an invalid character."""

    category = "Lexical Error"


class SyntaxCompilerError(CompilerError):
    """Raised when the parser finds invalid syntax."""

    category = "Syntax Error"


class SemanticError(CompilerError):
    """Raised when semantic validation fails."""

    category = "Semantic Error"


class TypeError(CompilerError):
    """Raised when operand types are incompatible."""

    category = "Semantic Error"

    def __init__(self, left, operator, right, lineno=None, column=None):
        super().__init__(
            f"Type mismatch: cannot apply '{operator}' to '{left.value}' and '{right.value}'",
            lineno,
            column,
        )


class UndeclaredVariableError(CompilerError):
    """Raised when a variable is used before being declared."""

    category = "Semantic Error"

    def __init__(self, name: str, lineno=None, column=None):
        super().__init__(f"Variable '{name}' used before declaration", lineno, column)


class RedeclaredVariableError(CompilerError):
    """Raised when a variable is declared more than once."""

    category = "Semantic Error"

    def __init__(self, name: str, lineno=None, column=None):
        super().__init__(f"Variable '{name}' already declared", lineno, column)


class AssignmentTypeError(CompilerError):
    """Raised when assigned value type doesn't match variable type."""

    category = "Semantic Error"

    def __init__(self, var: str, expected, got, lineno=None, column=None):
        super().__init__(
            f"Cannot assign '{got.value}' to variable '{var}' of type '{expected.value}'",
            lineno,
            column,
        )
