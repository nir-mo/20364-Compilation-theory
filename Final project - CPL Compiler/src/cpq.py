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

    with open(input_filename) as input_fd:
        with open(input_filename_no_ext + ".qud", "w") as output_fd:
            output_file = logging.getLogger("file_output")
            output_file.addHandler(logging.StreamHandler(output_fd))
            output_file.setLevel(logging.INFO)
            stderr = logging.getLogger("stderr")
            stderr.addHandler(logging.StreamHandler(sys.stderr))
            stderr.setLevel(logging.INFO)
            compiler(
                cpl_string=input_fd.read(),
                output_stream=output_file,
                error_stream=stderr,
                signature="Nir Moshe, 300307824. Compilation Theory."
            )

    input_filename = sys.argv[1]
    with open(input_filename) as inf:
        ast = build_ast(CPLTokenizer(inf.read()))
        sym = SymbolTable.build_form_ast(ast)
        for i in get_quad(get_ir(ast, sym)):
            print(i.code)


def compiler(cpl_string, signature):
    """
    The function simulates a CPL compiler.

    :param cpl_string: String which represent the CPL program.
    :param output_stream: Tokens will be written to this stream.
    :param error_stream: Errors will be written to this stream.
    :param signature:
        File signature. The signature will be written at the end of the `output_stream` and at the end of
        `error_stream`.
    """
    errors, ast = build_ast(CPLTokenizer(cpl_string))
    if errors:
        # TODO: handle errors.
        return

    try:
        symbol_table = SymbolTable.build_form_ast(ast)
    except CPLCompoundException as exceptions:
        pass

    try:
        quad = get_quad(get_ir(ast, symbol_table))
        quad.append(signature)
    except CPLCompoundException:
        pass

    error_stream.info(signature)
    output_stream.info(signature)


if __name__ == "__main__":
    main()
