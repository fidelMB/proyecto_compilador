from lexer import lexer
from parser import parser, compiler
from vm import VirtualMachine
from utils.errors import CompilerError
import sys


def run_lexer(data):
    lexer.input(data)

    print("===== LEXICAL ANALYSIS =====")

    while True:
        tok = lexer.token()

        if not tok:
            break

        print(tok)


def run_parser(data, debug=True):
    print("\n===== SYNTAX ANALYSIS =====")
    try:
        result = parser.parse(data)
        print("Parsing completed successfully.")

    except CompilerError as ce:
        # This catches TypeError, AssignmentTypeError, UndeclaredVariableError, etc.
        print(f"\n[SEMANTIC ERROR] {ce}")
        sys.exit(1)

    except Exception as e:
        # This catches standard Python panics (like an unexpected IndexError on an empty stack)
        print(
            f"\n[COMPILER FATAL ERROR] Execution stopped due to parsing panic or unhandled crash."
        )
        print(f"Details: {e}")
        sys.exit(1)

    # After successful parsing, run the VM
    run_vm(debug)


def run_vm(debug):
    """Execute generated quadruples using the Virtual Machine."""
    print("\n===== SEMANTIC ANALYSIS & QUADRUPLE GENERATION =====")

    try:
        # Create and run the VM
        vm = VirtualMachine(
            quadruples=compiler.quads,
            symbols=compiler.symbols,
            memory=compiler.memory,
            debug=debug,
        )

        vm.run()

        # Print final state info if debug mode
        if debug:
            vm.dump_memory()
            print(f"\nProgram output captured: {repr(vm.get_output())}")

    except Exception as e:
        print(f"\n[VM ERROR] {e}")
        sys.exit(1)


def main():
    debug = "--debug" in sys.argv

    # Remove --debug flag from argv for cleaner file argument handling
    argv = [arg for arg in sys.argv if arg != "--debug"]

    if len(argv) != 2:
        print("Usage:")
        print("python run_compiler.py [--debug] <input_file.txt>")
        return

    filename = argv[1]

    try:
        with open(filename, "r") as file:
            data = file.read()

        run_lexer(data)
        run_parser(data, debug=debug)

    except FileNotFoundError:
        print(f"ERROR: File '{filename}' not found")


if __name__ == "__main__":
    main()
