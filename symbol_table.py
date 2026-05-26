from utils.types import Type
from utils.errors import UndeclaredVariableError, RedeclaredVariableError


class Symbol:
    def __init__(self, name: str, var_type: Type, address: int):
        self.name = name
        self.var_type = var_type
        self.address = address

    def __repr__(self):
        return f"Symbol(name={self.name!r}, type={self.var_type.value}, addr={self.address})"


class SymbolTable:
    """
    Flat symbol table.
    """

    def __init__(self, memory):
        self._table: dict[str, Symbol] = {}
        self.memory = memory

    # ------------------------------------------------------------------
    # Registration & lookup
    # ------------------------------------------------------------------

    def declare(self, name: str, var_type: Type, lineno: int = None) -> Symbol:
        if name in self._table:
            raise RedeclaredVariableError(name, lineno)
        address = self.memory.alloc("global", var_type)
        symbol = Symbol(name, var_type, address)
        self._table[name] = symbol
        return symbol

    def lookup(self, name: str, lineno: int = None) -> Symbol:
        if name not in self._table:
            raise UndeclaredVariableError(name, lineno)
        return self._table[name]

    def exists(self, name: str) -> bool:
        return name in self._table

    def get_type(self, name: str, lineno: int = None) -> Type:
        return self.lookup(name, lineno).var_type

    def get_address(self, name: str, lineno: int = None) -> int:
        return self.lookup(name, lineno).address

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def __repr__(self):
        rows = [f"  {s}" for s in self._table.values()]
        return "SymbolTable(\n" + "\n".join(rows) + "\n)"
