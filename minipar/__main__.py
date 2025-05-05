import argparse
import pprint

from minipar.executor import Executor
from minipar.lexer import Lexer
from minipar.parser import Parser
from minipar.semantic import SemanticAnalyzer


def main():
    parser = argparse.ArgumentParser(
        prog="minipar", description="MiniPar Interpreter"
    )

    parser.add_argument("-tok", action="store_true", help="tokenize the code")
    parser.add_argument(
        "-ast", action="store_true", help="get Abstract Syntax Tree (AST)"
    )
    parser.add_argument("name", type=str, help="program read from script file")

    args = parser.parse_args()

    with open(args.name, "r") as f:
        data = f.read()

    lexer = Lexer(data)
    if args.tok:
        for token in lexer.scan():
            print(f"{token} | line: {lexer.line}")
    elif args.ast:
        parser = Parser(lexer)
        semantic = SemanticAnalyzer()
        ast = parser.parse()
        semantic.visit(ast)
        pprint.pprint(ast)
    else:
        # Frontend
        parser = Parser(lexer)
        semantic = SemanticAnalyzer()
        ast = parser.parse()
        semantic.visit(ast)
        # Execução
        executor = Executor()
        executor.run(ast)


if __name__ == "__main__":
    main()
