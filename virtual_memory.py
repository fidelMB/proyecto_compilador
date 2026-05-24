from utils.types import Type


class VirtualMemory:

    def __init__(self):
        self.constant_values = {}
        self.memory_division = {
            ("global", Type.INT): (1_000_000, 1_999_999),
            ("global", Type.FLOAT): (2_000_000, 2_999_999),
            ("global", Type.BOOL): (3_000_000, 3_999_999),
            ("global", Type.STRING): (4_000_000, 4_999_999),
            ("global", Type.CHAR): (5_000_000, 5_999_999),
            ("temp", Type.INT): (6_000_000, 6_999_999),
            ("temp", Type.FLOAT): (7_000_000, 7_999_999),
            ("temp", Type.BOOL): (8_000_000, 8_999_999),
            ("temp", Type.STRING): (9_000_000, 9_999_999),
            ("temp", Type.CHAR): (10_000_000, 10_999_999),
            ("const", Type.INT): (11_000_000, 11_999_999),
            ("const", Type.FLOAT): (12_000_000, 12_999_999),
            ("const", Type.BOOL): (13_000_000, 13_999_999),
            ("const", Type.STRING): (14_000_000, 14_999_999),
            ("const", Type.CHAR): (15_000_000, 15_999_999),
        }

        self.counters = {key: ranges[0] for key, ranges in self.memory_division.items()}

        self.constants = {}

    def alloc(self, segment: str, var_type: Type) -> int:

        key = (segment, var_type)

        if key not in self.counters:
            raise ValueError(f"Invalid memory segment/type: {segment} {var_type}")

        address = self.counters[key]

        if address > self.memory_division[key][1]:
            raise MemoryError(f"Out of memory for {segment} {var_type.value}")

        self.counters[key] += 1

        return address

    def alloc_const(self, value, var_type: Type) -> int:

        key = (value, var_type)

        if key in self.constants:
            return self.constants[key]

        address = self.alloc("const", var_type)

        self.constants[key] = address
        self.constant_values[address] = value

        return address

    def get_constants_map(self):
        return dict(self.constant_values)
