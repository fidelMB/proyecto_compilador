from lexer import lexer
from parser import parser
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


def run_parser(data):
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


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("python run_compiler.py <input_file.txt>")
        return

    filename = sys.argv[1]

    try:
        with open(filename, "r") as file:
            data = file.read()

        run_lexer(data)
        run_parser(data)

    except FileNotFoundError:
        print(f"ERROR: File '{filename}' not found")


if __name__ == "__main__":
    main()
