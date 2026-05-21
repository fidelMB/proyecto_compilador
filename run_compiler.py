from lexer import lexer
from parser import parser
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

    result = parser.parse(data)

    print("Parsing completed successfully.")


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
