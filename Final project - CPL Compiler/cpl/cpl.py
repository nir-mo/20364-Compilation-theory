import sys


def main():
    input_filename = sys.argv[1]
    with open(input_filename) as inf:
        ast = build_ast(CPLTokenizer(inf.read()))
        sym = SymbolTable.build_form_ast(ast)
        for i in get_quad(get_ir(ast, sym)):
            print(i.code)


if __name__ == "__main__":
    main()
