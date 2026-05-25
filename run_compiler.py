from lexer import lexer
import parser as parser_module
from vm import VirtualMachine
from utils.errors import CompilerError
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import io
import sys


TEST_ROOT = Path("casos") / "tests"


def reset_compiler_state():
    parser_module.reset_compiler()
    lexer.lineno = 1


def run_lexer(data, verbose=True):
    lexer.lineno = 1
    lexer.input(data)

    if verbose:
        print("===== LEXICAL ANALYSIS =====")

    while True:
        tok = lexer.token()

        if not tok:
            break

        if verbose:
            print(tok)


def compile_source(data, debug=False, show_lexer=False, execute=True, exit_on_error=True):
    reset_compiler_state()

    if show_lexer:
        run_lexer(data, verbose=True)

    lexer.lineno = 1
    parser_module.parser.parse(data, lexer=lexer)

    if execute:
        vm = VirtualMachine(
            quadruples=parser_module.compiler.quads,
            symbols=parser_module.compiler.symbols,
            memory=parser_module.compiler.memory,
            debug=debug,
            exit_on_error=exit_on_error,
        )
        vm.run()
        return vm

    return None


def run_parser(data, debug=True):
    print("\n===== SYNTAX ANALYSIS =====")
    try:
        lexer.lineno = 1
        parser_module.parser.parse(data, lexer=lexer)
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
            quadruples=parser_module.compiler.quads,
            symbols=parser_module.compiler.symbols,
            memory=parser_module.compiler.memory,
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


def run_test_file(path, expect_success, verbose=False):
    data = path.read_text(encoding="utf-8")
    captured = io.StringIO()
    actual_program_output = ""
    expected_program_output = None

    try:
        output_context = redirect_stdout(captured) if not verbose else redirect_stdout(sys.stdout)
        error_context = redirect_stderr(captured) if not verbose else redirect_stderr(sys.stderr)

        with output_context, error_context:
            vm = compile_source(
                data,
                debug=False,
                show_lexer=False,
                execute=True,
                exit_on_error=False,
            )
            actual_program_output = vm.get_output()

        succeeded = True
        error = ""

    except Exception as exc:
        succeeded = False
        error = str(exc)

    passed = succeeded == expect_success

    if passed and expect_success:
        expected_path = path.with_suffix(".out")

        if expected_path.exists():
            expected_program_output = expected_path.read_text(encoding="utf-8")
            expected_program_output = expected_program_output.replace("\r\n", "\n")
            actual_program_output = actual_program_output.replace("\r\n", "\n")
            passed = actual_program_output == expected_program_output
            if not passed:
                error = f"Output mismatch against {expected_path.name}"
        else:
            passed = False
            error = f"Missing expected output file: {expected_path}"

    return (
        passed,
        succeeded,
        error,
        captured.getvalue(),
        actual_program_output,
        expected_program_output,
    )


def run_all_tests(verbose=False):
    print("===== AUTOMATED TEST SUITE =====")

    test_specs = [
        ("positive", TEST_ROOT / "positivos", True),
        ("negative", TEST_ROOT / "negativos", False),
    ]

    total = 0
    passed = 0

    for label, root, expect_success in test_specs:
        files = sorted(root.rglob("*.txt"))

        if not files:
            print(f"[WARN] No {label} tests found under {root}")
            continue

        for path in files:
            total += 1
            ok, succeeded, error, output, actual_output, expected_output = run_test_file(
                path, expect_success, verbose
            )

            if ok:
                passed += 1
                status = "PASS"
            else:
                status = "FAIL"

            relative = path.relative_to(TEST_ROOT)
            expected = "success" if expect_success else "failure"
            actual = "success" if succeeded else "failure"
            print(f"[{status}] {relative} expected={expected} actual={actual}")

            if not ok:
                if error:
                    print(f"       error: {error}")
                if output.strip():
                    print("       output:")
                    for line in output.strip().splitlines()[-8:]:
                        print(f"         {line}")
                if expected_output is not None:
                    print(f"       expected program output: {expected_output!r}")
                    print(f"       actual program output:   {actual_output!r}")

    print(f"\nResult: {passed}/{total} tests passed")
    return passed == total


def main():
    debug = "--debug" in sys.argv
    run_tests = "--run-tests" in sys.argv
    verbose_tests = "--tests-verbose" in sys.argv

    if run_tests:
        ok = run_all_tests(verbose=verbose_tests)
        sys.exit(0 if ok else 1)

    # Remove --debug flag from argv for cleaner file argument handling
    argv = [
        arg
        for arg in sys.argv
        if arg not in ("--debug", "--run-tests", "--tests-verbose")
    ]

    if len(argv) != 2:
        print("Usage:")
        print("python run_compiler.py [--debug] <input_file.txt>")
        print("python run_compiler.py --run-tests [--tests-verbose]")
        return

    filename = argv[1]

    try:
        with open(filename, "r") as file:
            data = file.read()

        reset_compiler_state()
        run_lexer(data)
        run_parser(data, debug=debug)

    except FileNotFoundError:
        print(f"ERROR: File '{filename}' not found")


if __name__ == "__main__":
    main()
