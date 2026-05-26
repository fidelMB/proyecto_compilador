from enum import Enum


class Type(Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    CHAR = "char"
    ERROR = "error"


_T = Type

_i = _T.INT
_f = _T.FLOAT
_b = _T.BOOL
_s = _T.STRING
_c = _T.CHAR
_e = _T.ERROR


ARITH_OPS = ("+", "-", "*", "/")

RELAT_OPS = (
    "<",
    "<=",
    ">",
    ">=",
    "==",
    "!=",
)

LOGIC_OPS = (
    "and",
    "or",
)

ALL_OPS = ARITH_OPS + RELAT_OPS + LOGIC_OPS


# cube[left_type][right_type][operator] -> result_type


def _build_cube() -> dict:

    cube = {}

    def set_op(left_type, right_type, operator, result):
        cube.setdefault(left_type, {}).setdefault(right_type, {})[operator] = result

    # ======================================================
    # INT x INT
    # ======================================================

    for op in ("+", "-", "*"):
        set_op(_i, _i, op, _i)

    # division produces float
    set_op(_i, _i, "/", _f)

    for op in RELAT_OPS:
        set_op(_i, _i, op, _b)

    # ======================================================
    # FLOAT x FLOAT
    # ======================================================

    for op in ARITH_OPS:
        set_op(_f, _f, op, _f)

    for op in RELAT_OPS:
        set_op(_f, _f, op, _b)

    # ======================================================
    # INT x FLOAT
    # FLOAT x INT
    # ======================================================

    for op in ARITH_OPS:
        set_op(_i, _f, op, _f)
        set_op(_f, _i, op, _f)

    for op in RELAT_OPS:
        set_op(_i, _f, op, _b)
        set_op(_f, _i, op, _b)

    # ======================================================
    # BOOL x BOOL
    # ======================================================

    for op in LOGIC_OPS:
        set_op(_b, _b, op, _b)

    for op in ("==", "!="):
        set_op(_b, _b, op, _b)

    # ======================================================
    # STRING x STRING
    # ======================================================

    # concatenation
    set_op(_s, _s, "+", _s)

    for op in ("==", "!="):
        set_op(_s, _s, op, _b)

    # ======================================================
    # CHAR x CHAR
    # ======================================================

    for op in ("==", "!="):
        set_op(_c, _c, op, _b)

    return cube


_CUBE = _build_cube()


# ==========================================================
# TYPE CHECK HELPERS
# ==========================================================


def result_type(left: Type, right: Type, operator: str) -> Type:
    """
    Returns the resulting type of:
        left operator right

    Returns Type.ERROR if invalid.
    """

    try:
        return _CUBE[left][right][operator]

    except KeyError:
        return _e


def is_numeric(t: Type) -> bool:
    return t in (_i, _f)


def is_compatible_assign(target: Type, value: Type) -> bool:
    if target == value:
        return True
    if is_numeric(target) and is_numeric(value):
        return True
    return False


# ==========================================================
# TOKEN -> TYPE
# ==========================================================


def token_to_type(token_type: str) -> Type:

    mapping = {
        "INT_DECLARATION": _i,
        "FLOAT_DECLARATION": _f,
        "BOOL_DECLARATION": _b,
        "STRING_DECLARATION": _s,
        "CHAR_DECLARATION": _c,
        "INT_CTE": _i,
        "FLOAT_CTE": _f,
        "BOOL_CTE": _b,
        "STRING_CTE": _s,
        "CHAR_CTE": _c,
    }

    return mapping.get(token_type, _e)
