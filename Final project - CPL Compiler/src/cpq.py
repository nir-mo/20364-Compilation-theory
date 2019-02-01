# Compiles CPL code into QUAD code using Lark parser.
# Author: Nir Moshe.
"""
apq.py usage:
    python cpq.py <cpl_file>.cpl

This script produces a new file <cpl_file>.qud which contains list of QUAD instructions.
On errors the script will not create *.qud file and will write the errors to the STDERR.

Author: Nir Moshe.
"""
import logging
import os
import sys

from cla import CPLTokenizer, build_ast
from exceptions import CPLCompoundException
from ir import get_quad, get_ir
from symbol_table import SymbolTable

__author__ = "Nir Moshe"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    input_filename = sys.argv[1]
    input_filename_no_ext, _ = os.path.splitext(input_filename)
    stderr = logging.getLogger("stderr")
    stderr.addHandler(logging.StreamHandler(sys.stderr))
    stderr.setLevel(logging.INFO)
    with open(input_filename) as input_fd:
        errors, quad = compiler(input_fd.read())
        if not errors:
            with open(input_filename_no_ext + ".qud", "w") as output_fd:
                output_file = logging.getLogger("file_output")
                output_file.addHandler(logging.StreamHandler(output_fd))
                output_file.setLevel(logging.INFO)
                for i in quad:
                    output_file.info(i.code)

                output_file.info("Nir Moshe, 300307824. Compilation Theory.")
        else:
            for error in errors:
                stderr.error("Error in line: %d: %s." % (error.line, error.message))

            stderr.info("Nir Moshe, 300307824. Compilation Theory.")


def compiler(cpl_string):
    """
    The function simulates a CPL compiler.

    :param cpl_string: String which represent the CPL program.
    :return pair of two lists (errors, quad).
    """
    quad = []
    errors, ast = build_ast(CPLTokenizer(cpl_string))
    if errors and not ast:
        return errors, []

    try:
        _errors, symbol_table = SymbolTable.build_form_ast(ast)
        errors.extend(_errors)
        quad = get_quad(get_ir(ast, symbol_table))
    except CPLCompoundException as exception:
        errors.extend(exception.exceptions)

    return errors, quad


if __name__ == "__main__":
    main()
