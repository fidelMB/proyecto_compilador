class CompilerError(Exception):
    """Base class for all compiler errors."""

    def __init__(self, message: str, lineno: int = None):
        self.lineno = lineno
        location = f" (line {lineno})" if lineno else ""
        super().__init__(f"[Compiler Error]{location} {message}")


class TypeError(CompilerError):
    """Raised when operand types are incompatible."""

    def __init__(self, left, operator, right, lineno=None):
        super().__init__(
            f"Type mismatch: cannot apply '{operator}' to '{left.value}' and '{right.value}'",
            lineno,
        )


class UndeclaredVariableError(CompilerError):
    """Raised when a variable is used before being declared."""

    def __init__(self, name: str, lineno=None):
        super().__init__(f"Variable '{name}' used before declaration", lineno)


class RedeclaredVariableError(CompilerError):
    """Raised when a variable is declared more than once."""

    def __init__(self, name: str, lineno=None):
        super().__init__(f"Variable '{name}' already declared", lineno)


class AssignmentTypeError(CompilerError):
    """Raised when assigned value type doesn't match variable type."""

    def __init__(self, var: str, expected, got, lineno=None):
        super().__init__(
            f"Cannot assign '{got.value}' to variable '{var}' of type '{expected.value}'",
            lineno,
        )
