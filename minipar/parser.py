"""
Módulo de Análise Sintática

O módulo de Análise Sintática conta com classes que possibilitam a
geração da Árvore Sintática Abstrada através da análise da sequência
de tokens identificados na linguagem.
"""

from abc import ABC, abstractmethod
from copy import deepcopy

from minipar import ast
from minipar import error as err
from minipar.lexer import Lexer, NextToken
from minipar.token import Token


class IParser(ABC):
    """
    Interface para a Análise Sintática
    """

    @abstractmethod
    def parse(self) -> ast.Node:
        pass


class Parser(IParser):
    """
    Classe que implementa os métodos da interface de Análise Sintática

    Args:
        lexer (Lexer): Instância da classe de Análise Léxica

    Attributes:
        lexer (NextToken): Gerador de tokens
        lookahead (Token): Token atual da análise
        lineno (int): Linha atual da análise
    """

    def __init__(self, lexer: Lexer):
        """
        Initialize the parser with a lexer.
        
        Args:
            lexer (Lexer): An instance of the lexical analyzer
        """
        self.original_lexer = lexer  # Keep reference to the original lexer
        self.lexer_generator = lexer.scan()  # Get the token generator
        self.lookahead, self.lineno = next(self.lexer_generator)  # Get first token

    def match(self, tag: str) -> bool:
        if tag == self.lookahead.tag:
            try:
                self.lookahead, self.lineno = next(self.lexer_generator)
            except StopIteration:
                self.lookahead = Token("EOF", "EOF")
            return True
        return False

    def parse(self) -> ast.Node:
        """
        Inicia a análise sintática e retorna a AST ao final.

        Returns:
            Node: Árvore Sintática Abstrada identificada
        """
        stmts = self.top_level_stmts()
        return ast.Module(stmts=stmts)

    def top_level_stmts(self) -> list[ast.Node]:
        """
        Permite múltiplos statements no topo do arquivo, incluindo funções, canais, variáveis, blocos SEQ/PAR, etc.
        """
        stmts = []
        while self.lookahead.tag != "EOF":
            # Process any standalone semicolons
            if self.lookahead.tag == "SEMICOLON":
                self.match("SEMICOLON")
                continue
                
            # Handle SEQ and PAR blocks as top-level statements
            if self.lookahead.tag in {"SEQ", "PAR"}:
                stmts.append(self.bloco_stmt())
            # Only these statements are allowed at the top level
            elif self.lookahead.tag in {"ID", "FUNC", "OUTPUT", "C_CHANNEL", "S_CHANNEL", 
                           "STRING_TYPE", "INT_TYPE", "BOOL_TYPE"}:
                try:
                    # Try to parse as a variable assignment first
                    if self.lookahead.tag == "ID":
                        stmts.append(self.atrib_or_func_call())
                    else:
                        stmts.append(self.stmt())
                except Exception:
                    # Skip to the next line/statement
                    while self.lookahead.tag != "SEMICOLON" and self.lookahead.tag != "EOF":
                        self.match(self.lookahead.tag)
                    if self.lookahead.tag == "SEMICOLON":
                        self.match("SEMICOLON")
            else:
                # Skip to the next line/statement
                while self.lookahead.tag != "SEMICOLON" and self.lookahead.tag != "EOF":
                    self.match(self.lookahead.tag)
                if self.lookahead.tag == "SEMICOLON":
                    self.match("SEMICOLON")
                    
        return stmts

    def program(self) -> ast.Node:
        """
        <programa> ::= <bloco_stmt>
        """
        # Removido: return self.bloco_stmt()
        # Agora não é mais usado, mas mantido para compatibilidade
        return self.top_level_stmts()

    def bloco_stmt(self) -> ast.Node:
        """
        <bloco_stmt> ::= <bloco_SEQ> | <bloco_PAR>
        """
        if self.lookahead.tag == "SEQ":
            return self.bloco_SEQ()
        elif self.lookahead.tag == "PAR":
            return self.bloco_PAR()
        else:
            raise err.SyntaxError(
                self.lineno, f"Esperado 'SEQ' ou 'PAR', encontrado {self.lookahead.value}"
            )

    def bloco_SEQ(self) -> ast.Node:
        """
        <bloco_SEQ> ::= "SEQ" ["{" <stmts> "}"] | "SEQ" <stmts>
        """
        self.match("SEQ")
        stmts = []
        
        # If there are explicit braces
        if self.lookahead.tag == "LBRACE":
            self.match("LBRACE")
            stmts = self.stmts()
            self.match("RBRACE")
        else:
            # Process statements until end of file or another block
            while self.lookahead.tag not in {"SEQ", "PAR", "EOF", "RBRACE"}:
                # Skip standalone semicolons
                if self.lookahead.tag == "SEMICOLON":
                    self.match("SEMICOLON")
                    continue
                    
                try:
                    # Handle variable assignments directly
                    if self.lookahead.tag == "ID":
                        node = self.atrib_or_func_call()
                        stmts.append(node)
                    # Handle floating decimal numbers (like 0.5)
                    elif self.lookahead.tag == "NUMBER" and self.lookahead.value == "0" and self.lookahead.tag == "DIV":
                        # Decimal number as a standalone expression
                        # - Create a placeholder for now
                        value = self.lookahead.value  # "0"
                        self.match("NUMBER")
                        self.match("DIV")
                        if self.lookahead.tag == "NUMBER":
                            value += "." + self.lookahead.value
                            self.match("NUMBER")
                        node = ast.Constant(type="NUMBER", token=Token("NUMBER", value))
                        stmts.append(node)
                    # Handle other statement types
                    else:
                        stmts.append(self.stmt())
                except Exception:
                    # Skip to the next line/statement
                    while self.lookahead.tag not in {"SEMICOLON", "EOF", "SEQ", "PAR", "RBRACE"}:
                        self.match(self.lookahead.tag)
                    if self.lookahead.tag == "SEMICOLON":
                        self.match("SEMICOLON")
                    
        return ast.Seq(body=stmts)

    def bloco_PAR(self) -> ast.Node:
        self.match("PAR")
        stmts = []
        if self.lookahead.tag == "LBRACE":
            self.match("LBRACE")
            stmts = self.stmts()
            self.match("RBRACE")
        else:
            # Permite múltiplas instruções até encontrar um bloco ou EOF
            while self.lookahead.tag not in {"SEQ", "PAR", "EOF", "RBRACE"}:
                if self.lookahead.tag == "SEMICOLON":
                    self.match("SEMICOLON")
                    continue
                stmts.append(self.stmt())
        return ast.Par(body=stmts)

    def stmts(self) -> list[ast.Node]:
        """
        <stmts> ::= <stmt> <stmts> | ε
        """
        stmts = []
        # Parar em EOF, }, SEQ ou PAR para delimitar blocos corretamente
        while self.lookahead.tag not in {"EOF", "RBRACE", "SEQ", "PAR"}:
            # Ignora pontos e vírgula isolados (linhas vazias)
            if self.lookahead.tag == "SEMICOLON":
                self.match("SEMICOLON")
                continue
            # Não consome NUMBER isolado aqui!
            stmts.append(self.stmt())
        return stmts

    def stmt(self) -> ast.Node:
        """
        <stmt> ::= <var_decl>
                | <atrib_or_func_call>
                | <if_stmt>
                | <while_stmt>
                | <send_stmt>
                | <receive_stmt>
                | <output_stmt>
                | <func_decl>
                | <bloco_stmt>
                | <return_stmt>
        """
        if self.lookahead.tag in {"STRING_TYPE", "INT_TYPE", "BOOL_TYPE", "C_CHANNEL"}:
            return self.var_decl()
        elif self.lookahead.tag == "ID":
            return self.atrib_or_func_call()
        elif self.lookahead.tag == "IF":
            return self.if_stmt()
        elif self.lookahead.tag == "WHILE":
            return self.while_stmt()
        elif self.lookahead.tag == "SEND":
            return self.send_stmt()
        elif self.lookahead.tag == "RECEIVE":
            return self.receive_stmt()
        elif self.lookahead.tag == "OUTPUT":
            stmt = self.output_stmt()
            if self.lookahead.tag == "SEMICOLON":
                self.match("SEMICOLON")
            return stmt
        elif self.lookahead.tag == "FUNC":
            # Changed from "function" to "FUNC" since the token tag is FUNC
            return self.func_decl()
        elif self.lookahead.tag == "SEQ":
            return self.bloco_SEQ()  # Não exige ponto e vírgula após bloco
        elif self.lookahead.tag == "PAR":
            return self.bloco_PAR()  # Não exige ponto e vírgula após bloco
        elif self.lookahead.tag == "INPUT":
            # Permite instrução input(); como expressão isolada
            name = self.lookahead.value
            self.match("INPUT")
            if self.lookahead.tag == "LPAREN":
                args = self.arg_list()
                node = ast.Call(type=None, token=Token("INPUT", name), args=args)
            else:
                node = ast.ID(type=None, token=Token("INPUT", name))
            if self.lookahead.tag == "SEMICOLON":
                self.match("SEMICOLON")
            return node
        elif self.lookahead.tag == "RETURN":
            return self.return_stmt()
        elif self.lookahead.tag == "ELSE":
            # Special handling for ELSE to help with error recovery
            self.match("ELSE")
            if self.lookahead.tag in {"SEQ", "PAR"}:
                return self.stmt()
            else:
                # Handle single statement
                stmt = self.stmt()
                if self.lookahead.tag == "SEMICOLON":
                    self.match("SEMICOLON")
                return stmt
        elif self.lookahead.tag == "NUMBER":
            # Handle isolated numbers as constant expressions
            value = self.lookahead.value
            self.match("NUMBER")
            if self.lookahead.tag == "SEMICOLON":
                self.match("SEMICOLON")
            return ast.Constant(type="NUMBER", token=Token("NUMBER", value))
        else:
            raise err.SyntaxError(
                self.lineno, f"Instrução inválida: {self.lookahead.value}"
            )

    def var_decl(self) -> ast.Node:
        """
        <var_decl> ::= <type> IDENT
                     | IDENT ':' <type>
                     | <type> IDENT '=' <expr>
                     | IDENT ':' <type> '=' <expr>
                     | "C_CHANNEL" <IDENT> <VAL> <VAL>
        """
        if self.lookahead.tag == "C_CHANNEL":
            self.match("C_CHANNEL")
            name = self.lookahead.value
            self.match("ID")
            # Aceita STRING, NUMBER ou ID para localhost e port
            if self.lookahead.tag in {"STRING", "NUMBER", "ID"}:
                localhost = self.lookahead.value
                self.match(self.lookahead.tag)
            else:
                raise err.SyntaxError(self.lineno, "Esperado STRING, NUMBER ou ID para localhost")
            if self.lookahead.tag in {"STRING", "NUMBER", "ID"}:
                port = self.lookahead.value
                self.match(self.lookahead.tag)
            else:
                raise err.SyntaxError(self.lineno, "Esperado STRING, NUMBER ou ID para port")
            return ast.CChannel(name=name, localhost=localhost, port=port)
        # tipo ID [= expr]
        elif self.lookahead.tag in {"STRING_TYPE", "INT_TYPE", "BOOL_TYPE"}:
            var_type = self.lookahead.value
            self.match(self.lookahead.tag)
            if self.lookahead.tag == "ID":
                name = self.lookahead.value
                self.match("ID")
                if self.lookahead.tag == "ASSIGN":
                    self.match("ASSIGN")
                    expr = self.expr()
                    return ast.Assign(left=ast.ID(type=var_type, token=Token("ID", name), decl=True), right=expr)
                return ast.ID(type=var_type, token=Token("ID", name), decl=True)
            else:
                raise err.SyntaxError(self.lineno, "Esperado identificador após tipo na declaração de variável")
        # ID : tipo [= expr]
        elif self.lookahead.tag == "ID":
            name = self.lookahead.value
            self.match("ID")
            if self.lookahead.tag == ":":
                self.match(":")
                var_type = self.lookahead.value
                self.match(self.lookahead.tag)
                if self.lookahead.tag == "ASSIGN":
                    self.match("ASSIGN")
                    expr = self.expr()
                    return ast.Assign(left=ast.ID(type=var_type, token=Token("ID", name), decl=True), right=expr)
                return ast.ID(type=var_type, token=Token("ID", name), decl=True)
            else:
                raise err.SyntaxError(self.lineno, "Esperado ':' após identificador na declaração de variável")
        else:
            raise err.SyntaxError(self.lineno, "Declaração de variável inválida")

    def s_channel_decl(self) -> ast.Node:
        """
        <s_channel_decl> ::= "S_CHANNEL" <ID> '{' <ID> ',' <ID> ',' <STRING> ',' <NUMBER> '}'
        Exemplo: s_channel server {calc, description, "localhost", 8585}
        """
        self.match("S_CHANNEL")
        name = self.lookahead.value
        self.match("ID")
        self.match("LBRACE")
        func_name = self.lookahead.value
        self.match("ID")
        self.match("COMMA")
        description = self.lookahead.value
        self.match("ID")
        self.match("COMMA")
        localhost = self.lookahead.value
        if self.lookahead.tag == "STRING":
            self.match("STRING")
        else:
            self.match("ID")
        self.match("COMMA")
        port = self.lookahead.value
        self.match("NUMBER")
        self.match("RBRACE")
        return ast.SChannel(name=name, func_name=func_name, description=ast.ID(type=None, token=Token("ID", description)), localhost=localhost, port=int(port))

    def atrib_or_func_call(self) -> ast.Node:
        """
        Decide entre atribuição, chamada de função ou apenas referência a variável.
        """
        name = self.lookahead.value
        self.match("ID")
        
        # Assignment handling
        if self.lookahead.tag == "ASSIGN":
            self.match("ASSIGN")
            # Handle input() in assignment
            if self.lookahead.tag == "INPUT":
                self.match("INPUT")
                if self.lookahead.tag == "LPAREN":
                    args = self.arg_list()
                    expr = ast.Call(type=None, token=Token("INPUT", "input"), args=args)
                else:
                    expr = ast.ID(type=None, token=Token("INPUT", "input"))
            else:
                # Parse the right side expression
                try:
                    expr = self.expr()
                except Exception:
                    # Skip to the next statement on error
                    while self.lookahead.tag not in {"SEMICOLON", "EOF"}:
                        self.match(self.lookahead.tag)
                    # Create a default expression (0) on error
                    expr = ast.Constant(type="NUMBER", token=Token("NUMBER", "0"))
            
            # Consume optional semicolon
            if self.lookahead.tag == "SEMICOLON":
                self.match("SEMICOLON")
                
            return ast.Assign(left=ast.ID(type=None, token=Token("ID", name)), right=expr)
        
        # Function call handling
        elif self.lookahead.tag == "LPAREN":
            try:
                args = self.arg_list()
                if self.lookahead.tag == "SEMICOLON":
                    self.match("SEMICOLON")
                return ast.Call(type=None, token=Token("ID", name), args=args)
            except Exception:
                # Skip to the next statement on error
                while self.lookahead.tag not in {"SEMICOLON", "EOF"}:
                    self.match(self.lookahead.tag)
                # Create a default function call with no args on error
                return ast.Call(type=None, token=Token("ID", name), args=[])
        
        # Variable reference
        else:
            # Consume optional semicolon
            if self.lookahead.tag == "SEMICOLON":
                self.match("SEMICOLON")
            return ast.ID(type=None, token=Token("ID", name))

    def if_stmt(self) -> ast.Node:
        """
        <if_stmt> ::= "if" "(" <expr_bool> ")" <stmt> [ "else" <stmt> ]
        """
        self.match("IF")
        
        # Handle condition in parentheses
        if self.lookahead.tag == "LPAREN":
            self.match("LPAREN")
            condition = self.expr_bool()
            if self.lookahead.tag == "RPAREN":
                self.match("RPAREN")
        else:
            condition = self.expr_bool()
        
        # Parse the if body
        try:
            # Handle blocks (SEQ, PAR)
            if self.lookahead.tag in {"SEQ", "PAR"}:
                body = [self.stmt()]
            # Handle block with braces
            elif self.lookahead.tag == "LBRACE":
                self.match("LBRACE")
                body = self.stmts()
                if self.lookahead.tag == "RBRACE":
                    self.match("RBRACE")
            # Handle single statement
            else:
                body = [self.stmt()]
        except Exception:
            # Create an empty body on error
            body = []
            # Skip to else or semicolon
            while self.lookahead.tag not in {"ELSE", "SEMICOLON", "EOF", "RBRACE"}:
                self.match(self.lookahead.tag)
            
        # Check for optional else clause
        else_body = []
        if self.lookahead.tag == "ELSE":
            self.match("ELSE")
            try:
                # Handle blocks (SEQ, PAR)
                if self.lookahead.tag in {"SEQ", "PAR"}:
                    else_body = [self.stmt()]
                # Handle block with braces
                elif self.lookahead.tag == "LBRACE":
                    self.match("LBRACE")
                    else_body = self.stmts()
                    if self.lookahead.tag == "RBRACE":
                        self.match("RBRACE")
                # Handle single statement
                else:
                    else_body = [self.stmt()]
            except Exception:
                # Create an empty else body on error
                else_body = []
                # Skip to semicolon
                while self.lookahead.tag not in {"SEMICOLON", "EOF", "RBRACE"}:
                    self.match(self.lookahead.tag)
                
        return ast.If(condition=condition, body=body, else_stmt=else_body)

    def while_stmt(self) -> ast.Node:
        """
        <while_stmt> ::= "while" "(" <expr_bool> ")" <stmt>
        """
        self.match("WHILE")
        
        # Handle condition in parentheses
        if self.lookahead.tag == "LPAREN":
            self.match("LPAREN")
            condition = self.expr_bool()
            if self.lookahead.tag == "RPAREN":
                self.match("RPAREN")
        else:
            condition = self.expr_bool()
        
        # Parse the while body
        try:
            # Handle blocks (SEQ, PAR)
            if self.lookahead.tag in {"SEQ", "PAR"}:
                body = [self.stmt()]
            # Handle block with braces
            elif self.lookahead.tag == "LBRACE":
                self.match("LBRACE")
                body = self.stmts()
                if self.lookahead.tag == "RBRACE":
                    self.match("RBRACE")
            # Handle single statement
            else:
                body = [self.stmt()]
        except Exception:
            # Create an empty body on error
            body = []
            # Skip to semicolon
            while self.lookahead.tag not in {"SEMICOLON", "EOF", "RBRACE"}:
                self.match(self.lookahead.tag)
            if self.lookahead.tag == "SEMICOLON":
                self.match("SEMICOLON")
                
        return ast.While(condition=condition, body=body)

    def send_stmt(self) -> ast.Node:
        """
        <send_stmt> ::= "send" "(" <expr> "," IDENT ")"
        """
        self.match("SEND")
        self.match("LPAREN")
        expr = self.expr()
        self.match("COMMA")
        ident = self.lookahead.value
        self.match("ID")
        self.match("RPAREN")
        return ast.Call(type=None, token=Token("send", "send"), args=[expr, ident])

    def receive_stmt(self) -> ast.Node:
        """
        <receive_stmt> ::= IDENT "=" "receive" "(" IDENT ")"
        """
        name = self.lookahead.value
        self.match("ID")
        self.match("ASSIGN")
        self.match("RECEIVE")
        self.match("LPAREN")
        ident = self.lookahead.value
        self.match("ID")
        self.match("RPAREN")
        return ast.Assign(left=ast.ID(type=None, token=Token("ID", name)), right=ident)

    def output_stmt(self) -> ast.Node:
        """
        <output_stmt> ::= "output" "(" <expr> ")"
        """
        self.match("OUTPUT")
        self.match("LPAREN")
        expr = self.expr()
        self.match("RPAREN")
        # Make semicolon optional to support both styles: output(x) and output(x);
        if self.lookahead.tag == "SEMICOLON":
            self.match("SEMICOLON")
        return ast.Call(type=None, token=Token("output", "output"), args=[expr])

    def func_decl(self) -> ast.Node:
        """
        <func_decl> ::= "function" IDENT "(" [ <param_list> ] ")" <stmt>
        """
        self.match("FUNC")  # Handle the "function" keyword
        name = self.lookahead.value
        self.match("ID")
        self.match("LPAREN")
        
        # Parse parameter list
        params = []
        if self.lookahead.tag != "RPAREN":
            param_name = self.lookahead.value
            self.match("ID")
            params.append(ast.ID(type=None, token=Token("ID", param_name), decl=True))
            
            while self.lookahead.tag == "COMMA":
                self.match("COMMA")
                param_name = self.lookahead.value
                self.match("ID")
                params.append(ast.ID(type=None, token=Token("ID", param_name), decl=True))
                
        self.match("RPAREN")
        
        # Function body - we need to handle both explicit braces and implicit blocks
        body = []
        
        # Handle block with braces
        if self.lookahead.tag == "LBRACE":
            self.match("LBRACE")
            
            # Process statements until we reach closing brace
            while self.lookahead.tag != "RBRACE" and self.lookahead.tag != "EOF":
                try:
                    if self.lookahead.tag == "SEMICOLON":
                        self.match("SEMICOLON")
                        continue
                        
                    # Handle variable assignments directly
                    if self.lookahead.tag == "ID":
                        body.append(self.atrib_or_func_call())
                    # Handle other statement types
                    else:
                        body.append(self.stmt())
                except Exception:
                    # Skip to the next statement
                    while self.lookahead.tag not in {"SEMICOLON", "RBRACE", "EOF"}:
                        self.match(self.lookahead.tag)
                    if self.lookahead.tag == "SEMICOLON":
                        self.match("SEMICOLON")
            
            # Match closing brace
            if self.lookahead.tag == "RBRACE":
                self.match("RBRACE")
                
        # Handle block statement (SEQ/PAR)
        elif self.lookahead.tag in {"SEQ", "PAR"}:
            body_stmt = self.bloco_stmt()
            body.append(body_stmt)
            
        # Handle single statement
        else:
            body_stmt = self.stmt()
            body.append(body_stmt)
            
        return ast.FuncDef(name=name, return_type=None, params=params, body=body)

    def param_list(self) -> list[ast.Node]:
        """
        <param_list> ::= <param> { "," <param> }
        """
        params = [self.param()]
        while self.lookahead.tag == "COMMA":
            self.match("COMMA")
            params.append(self.param())
        return params

    def param(self) -> ast.Node:
        """
        <param> ::= <type> IDENT
        """
        param_type = self.lookahead.value
        self.match(self.lookahead.tag)
        name = self.lookahead.value
        self.match("ID")
        return ast.ID(type=param_type, token=Token("ID", name), decl=True)

    def arg_list(self) -> list[ast.Node]:
        """
        <arg_list> ::= <expr> { "," <expr> }
        """
        args = []
        self.match("LPAREN")
        if self.lookahead.tag != "RPAREN":
            args.append(self.expr())
            while self.lookahead.tag == "COMMA":
                self.match("COMMA")
                args.append(self.expr())
        self.match("RPAREN")
        return args

    def expr(self) -> ast.Node:
        """
        <expr> ::= <expr> "+" <term>
                 | <expr> "–" <term>
                 | <term>
        """
        left = self.term()
        while self.lookahead.tag in {"PLUS", "MINUS"}:
            op = self.lookahead
            self.match(op.tag)
            right = self.term()
            left = ast.Arithmetic(type=None, token=op, left=left, right=right)
        return left

    def term(self) -> ast.Node:
        """
        <term> ::= <term> "*" <factor>
                 | <term> "/" <factor>
                 | <factor>
        """
        left = self.factor()
        while self.lookahead.tag in {"MULT", "DIV"}:
            op = self.lookahead
            self.match(op.tag)
            right = self.factor()
            left = ast.Arithmetic(type=None, token=op, left=left, right=right)
        return left

    def factor(self) -> ast.Node:
        """
        <factor> ::= "(" <expr> ")"
                   | IDENT
                   | NUM
                   | STRING
                   | BOOL
                   | "input" "(" ")"
                   | "receive" "(" IDENT ")"
                   | "!" <factor>
                   | "-" <factor>
        """
        # Handle unary operators
        if self.lookahead.tag == "NOT":
            op = self.lookahead
            self.match("NOT")
            expr = self.factor()
            return ast.Unary(type="BOOL", token=op, expr=expr)
        elif self.lookahead.tag == "MINUS":
            op = self.lookahead
            self.match("MINUS")
            expr = self.factor()
            return ast.Unary(type="NUMBER", token=op, expr=expr)
        
        # Handle parenthesized expressions
        elif self.lookahead.tag == "LPAREN":
            self.match("LPAREN")
            try:
                expr = self.expr()
                if self.lookahead.tag == "RPAREN":
                    self.match("RPAREN")
                return expr
            except Exception:
                # Skip to closing parenthesis or end of expression
                while self.lookahead.tag not in {"RPAREN", "SEMICOLON", "EOF"}:
                    self.match(self.lookahead.tag)
                if self.lookahead.tag == "RPAREN":
                    self.match("RPAREN")
                # Return a default value on error
                return ast.Constant(type="NUMBER", token=Token("NUMBER", "0"))
        
        # Handle identifiers and function calls
        elif self.lookahead.tag in {"ID", "RECEIVE", "SEND", "OUTPUT", "INPUT"}:
            name = self.lookahead.value
            tag = self.lookahead.tag
            self.match(tag)
            if self.lookahead.tag == "LPAREN":
                try:
                    args = self.arg_list()
                    return ast.Call(type=None, token=Token(tag, name), args=args)
                except Exception:
                    # Skip to the end of statement
                    while self.lookahead.tag not in {"SEMICOLON", "EOF"}:
                        self.match(self.lookahead.tag)
                    # Return a default call with no args
                    return ast.Call(type=None, token=Token(tag, name), args=[])
            return ast.ID(type=None, token=Token(tag, name))
        
        # Handle constants
        elif self.lookahead.tag == "NUMBER":
            value = self.lookahead.value
            self.match("NUMBER")
            
            # Check if this might be a decimal number
            if self.lookahead.tag == "DIV":
                # This could be a decimal point
                self.match("DIV")
                
                # If there's a number after the dot
                if self.lookahead.tag == "NUMBER":
                    decimal_part = self.lookahead.value
                    self.match("NUMBER")
                    
                    # Combine integer and decimal parts
                    value = value + "." + decimal_part
            
            return ast.Constant(type="NUMBER", token=Token("NUMBER", value))
        elif self.lookahead.tag == "STRING":
            value = self.lookahead.value
            self.match("STRING")
            return ast.Constant(type="STRING", token=Token("STRING", value))
        elif self.lookahead.tag == "BOOL":
            value = self.lookahead.value
            self.match("BOOL")
            return ast.Constant(type="BOOL", token=Token("BOOL", value))
        else:
            # Skip past this token and try to continue
            self.match(self.lookahead.tag)
            return ast.Constant(type="NUMBER", token=Token("NUMBER", "0"))

    def expr_bool(self) -> ast.Node:
        """
        <expr_bool> ::= <expr> <rel_op> <expr>
                      | <expr_bool> "&&" <expr_bool>
                      | <expr_bool> "||" <expr_bool>
                      | "!" <expr_bool>
                      | <expr>  # Allow expression without relational operator
        """
        if self.lookahead.tag == "NOT":
            op = self.lookahead
            self.match("NOT")
            right = self.expr_bool()
            return ast.Not(token=op, expr=right, type="BOOL")
        else:
            left = self.expr()
            
            # If we have a relational operator, parse as a relational expression
            if self.lookahead.tag in {"EQ", "NEQ", "LT", "GT", "LTE", "GTE"}:
                op = self.lookahead
                self.match(op.tag)
                right = self.expr()
                node = ast.Relational(token=op, left=left, right=right, type="BOOL")
                
                # Check for logical operators
                while self.lookahead.tag in {"AND", "OR"}:
                    op = self.lookahead
                    self.match(op.tag)
                    right = self.expr_bool()
                    node = ast.Logical(token=op, left=node, right=right, type="BOOL")
                
                return node
            # Check for logical operators without a preceding relational operator
            elif self.lookahead.tag in {"AND", "OR"}:
                node = left
                while self.lookahead.tag in {"AND", "OR"}:
                    op = self.lookahead
                    self.match(op.tag)
                    right = self.expr_bool()
                    node = ast.Logical(token=op, left=node, right=right, type="BOOL")
                return node
            else:
                # Just return the expression if no operator follows
                return left

    def return_stmt(self) -> ast.Node:
        """
        <return_stmt> ::= "return" <expr> ";"
        """
        self.match("RETURN")
        expr = self.expr() if self.lookahead.tag != "SEMICOLON" else None
        if self.lookahead.tag == "SEMICOLON":
            self.match("SEMICOLON")
        return ast.Return(expr=expr)
