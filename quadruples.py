from dataclasses import dataclass, field
from utils.types import Type
from typing import Any


@dataclass
class Quadruple:
    op: str
    left: Any  # operand address / value / None
    right: Any  # operand address / value / None
    result: Any  # result address / jump target / None

    def __repr__(self):
        return f"({self.op}, {self.left}, {self.right}, {self.result})"


class QuadrupleList:
    """
    Manages the list of generated quadruples and the temporary
    variable counter.
    """

    def __init__(self):
        self._quads: list[Quadruple] = []

    # ------------------------------------------------------------------
    # Quadruple emission
    # ------------------------------------------------------------------

    def emit(self, op: str, left: Any, right: Any, result: Any) -> int:
        """Append a new quadruple; returns its index."""

        q = Quadruple(op, left, right, result)

        self._quads.append(q)

        return len(self._quads) - 1

    # ------------------------------------------------------------------
    # Temporary variables (avail)
    # ------------------------------------------------------------------

    def new_temp(self) -> str:
        """Return a fresh temporary variable name: t1, t2, …"""

        return ""

    # ------------------------------------------------------------------
    # Jump patching
    # ------------------------------------------------------------------

    def current_index(self) -> int:
        """Index that the *next* quadruple will occupy."""
        return len(self._quads)

    def patch(self, index: int, target: int):
        """
        Fill in the jump target for a previously emitted quadruple.
        Used for GOTO / GotoF that are emitted before the target is known.
        """
        self._quads[index].result = target

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def get(self, index: int) -> Quadruple:
        return self._quads[index]

    def extract_from(self, start: int) -> list[Quadruple]:
        extracted = self._quads[start:]
        del self._quads[start:]
        return extracted

    def extend(self, quads: list[Quadruple]):
        self._quads.extend(quads)

    def all(self) -> list[Quadruple]:
        return list(self._quads)

    def __len__(self):
        return len(self._quads)

    def __repr__(self):
        lines = [f"{i:>4}: {q}" for i, q in enumerate(self._quads)]
        return "\n".join(lines)
