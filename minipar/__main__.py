import argparse
import pprint
import os

from minipar.executor import Executor
from minipar.lexer import Lexer
from minipar.parser import Parser
from minipar.semantic import SemanticAnalyzer
from minipar.preprocessor import preprocess


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
    
    # Preprocess the code to standardize syntax
    processed_data = preprocess(data)
    
    # Always show the processed code for debugging
    print("==== Original Code ====")
    print(data)
    print("\n==== Processed Code ====")
    print(processed_data)
    
    # Save processed code to a temp file for debugging
    temp_file = f"{args.name}.temp"
    with open(temp_file, "w") as f:
        f.write(processed_data)
    print(f"\nSaved processed code to {temp_file}")

    lexer = Lexer(processed_data)
    
    if args.tok:
        print("\n==== Tokenization ====")
        for token in lexer.scan():
            print(f"{token} | line: {lexer.line}")
    elif args.ast:
        parser = Parser(lexer)
        semantic = SemanticAnalyzer()
        ast = parser.parse()
        semantic.visit(ast)
        pprint.pprint(ast)
    else:
        try:
            # Frontend
            parser = Parser(lexer)
            semantic = SemanticAnalyzer()
            ast = parser.parse()
            semantic.visit(ast)
            # Execução
            executor = Executor()
            executor.run(ast)
        except Exception as e:
            print(f"Error: {e}")
            print("Check the processed file for syntax issues.")


if __name__ == "__main__":
    main()
