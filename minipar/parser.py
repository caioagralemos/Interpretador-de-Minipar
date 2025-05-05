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
        self.lexer: NextToken = lexer.scan()
        self.lookahead, self.lineno = next(self.lexer)

    def match(self, tag: str) -> bool:
        if tag == self.lookahead.tag:
            #print(f"[Parser] Correspondência encontrada: {tag} (lookahead: {self.lookahead})")
            try:
                self.lookahead, self.lineno = next(self.lexer)
            except StopIteration:
                self.lookahead = Token("EOF", "EOF")
            return True
        print(f"[Parser] Correspondência falhou: esperado {tag}, encontrado {self.lookahead.tag}")
        return False

    def parse(self) -> ast.Node:
        """
        Inicia a análise sintática e retorna a AST ao final.

        Returns:
            Node: Árvore Sintática Abstrata identificada
        """
        stmts = self.top_level_stmts()
        return ast.Module(stmts=stmts)

    def top_level_stmts(self) -> list[ast.Node]:
        """
        Permite múltiplos statements no topo do arquivo, incluindo funções, canais, variáveis, blocos SEQ/PAR, etc.
        """
        stmts = []
        while self.lookahead.tag != "EOF":
            # Permite SEQ, PAR, funções, canais, variáveis, atribuições, etc.
            if self.lookahead.tag in {"SEQ", "PAR"}:
                stmts.append(self.bloco_stmt())
            else:
                stmts.append(self.stmt())
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
        <bloco_SEQ> ::= "SEQ" '{' <stmts> '}' | "SEQ" <stmts>
        """
        self.match("SEQ")
        if self.lookahead.tag == "LBRACE":
            self.match("LBRACE")
            stmts = self.stmts()
            self.match("RBRACE")
        else:
            stmts = self.stmts()
        return ast.Seq(body=stmts)

    def bloco_PAR(self) -> ast.Node:
        """
        <bloco_PAR> ::= "PAR" '{' <stmts> '}' | "PAR" <stmts>
        """
        self.match("PAR")
        if self.lookahead.tag == "LBRACE":
            self.match("LBRACE")
            stmts = self.stmts()
            self.match("RBRACE")
        else:
            stmts = self.stmts()
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
            stmts.append(self.stmt())
        return stmts

    def stmt(self) -> ast.Node:
        """
        <stmt> ::= <var_decl> ";" 
                 | <atrib> ";" 
                 | <if_stmt> 
                 | <while_stmt> 
                 | <send_stmt> ";" 
                 | <receive_stmt> ";" 
                 | <output_stmt> ";" 
                 | <func_decl> 
                 | <func_call> ";"
                 | <c_channel_decl> ";"  # Adicionado suporte para c_channel
                 | <s_channel_decl> ";"  # Adicionado suporte para s_channel
                 | <bloco_SEQ>  # Adicionado suporte para blocos SEQ aninhados
                 | <bloco_PAR>  # Adicionado suporte para blocos PAR aninhados
                 | "break" ";"  # Adicionado suporte para break
                 | "continue" ";"  # Adicionado suporte para continue
        """
        # Aceitar tokens em caixa alta e baixa
        if self.lookahead.tag in {"STRING_TYPE", "INT_TYPE", "BOOL_TYPE", "C_CHANNEL"}:
            stmt = self.var_decl()
            self.match("SEMICOLON")
            return stmt
        elif self.lookahead.tag == "BREAK":
            self.match("BREAK")
            self.match("SEMICOLON")
            return ast.Break()
        elif self.lookahead.tag == "CONTINUE":
            self.match("CONTINUE")
            self.match("SEMICOLON")
            return ast.Continue()
        elif self.lookahead.tag == "S_CHANNEL":
            stmt = self.s_channel_decl()
            self.match("SEMICOLON")
            return stmt
        elif self.lookahead.tag == "ID":
            # Verifica se é declaração do tipo ID : tipo
            current_token = self.lookahead
            # Salva estado atual do lexer
            saved_lookahead = self.lookahead
            saved_lineno = self.lineno
            try:
                # Avança para ver se é ':'
                self.match("ID")
                if self.lookahead.tag == ":":
                    # Volta para o estado anterior e chama var_decl
                    self.lookahead = current_token
                    self.lineno = saved_lineno
                    stmt = self.var_decl()
                    self.match("SEMICOLON")
                    return stmt
                else:
                    # Volta para o estado anterior e faz atribuição/chamada
                    self.lookahead = current_token
                    self.lineno = saved_lineno
                    stmt = self.atrib_or_func_call()
                    self.match("SEMICOLON")
                    return stmt
            except Exception:
                # Em caso de erro, volta para o estado anterior
                self.lookahead = current_token
                self.lineno = saved_lineno
                raise
        elif self.lookahead.tag == "IF":
            return self.if_stmt()
        elif self.lookahead.tag == "WHILE":
            return self.while_stmt()
        elif self.lookahead.tag == "ELSE":
            raise err.SyntaxError(self.lineno, "'else' sem 'if' correspondente")
        elif self.lookahead.tag in {"send", "SEND"}:
            stmt = self.send_stmt()
            self.match("SEMICOLON")
            return stmt
        elif self.lookahead.tag in {"receive", "RECEIVE"}:
            stmt = self.receive_stmt()
            self.match("SEMICOLON")
            return stmt
        elif self.lookahead.tag in {"output", "OUTPUT"}:
            stmt = self.output_stmt()
            self.match("SEMICOLON")
            return stmt
        elif self.lookahead.tag in {"function", "FUNC"}:
            return self.func_decl()
        elif self.lookahead.tag == "SEQ":
            return self.bloco_SEQ()  # Não exige ponto e vírgula após bloco
        elif self.lookahead.tag == "PAR":
            return self.bloco_PAR()  # Não exige ponto e vírgula após bloco
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
        if self.lookahead.tag == "ASSIGN":
            self.match("ASSIGN")
            expr = self.expr()
            return ast.Assign(left=ast.ID(type=None, token=Token("ID", name)), right=expr)
        elif self.lookahead.tag == "LPAREN":
            args = self.arg_list()
            return ast.Call(type=None, token=Token("ID", name), args=args)
        else:
            # Permite instruções como apenas 'id;' (ex: declaração sem inicialização)
            return ast.ID(type=None, token=Token("ID", name))

    def if_stmt(self) -> ast.Node:
        self.match("IF")
        self.match("LPAREN")
        condition = self.expr_bool()
        self.match("RPAREN")
        # Permite bloco de instruções após if
        if self.lookahead.tag in {"SEQ", "PAR"}:
            body = self.stmt()
        else:
            body = self.stmt()
        else_body = None
        if self.lookahead.tag == "ELSE":
            self.match("ELSE")
            if self.lookahead.tag in {"SEQ", "PAR"}:
                else_body = self.stmt()
            else:
                else_body = self.stmt()
        return ast.If(condition=condition, body=[body], else_stmt=[else_body])

    def while_stmt(self) -> ast.Node:
        """
        <while_stmt> ::= "while" "(" <expr_bool> ")" <stmt>
        """
        self.match("WHILE")
        self.match("LPAREN")
        condition = self.expr_bool()
        self.match("RPAREN")
        body = self.stmt()
        return ast.While(condition=condition, body=[body])

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
        return ast.Call(type=None, token=Token("output", "output"), args=[expr])

    def func_decl(self) -> ast.Node:
        """
        <func_decl> ::= "function" IDENT "(" [ <param_list> ] ")" <block_stmt>
        """
        self.match("function")
        name = self.lookahead.value
        self.match("ID")
        self.match("LPAREN")
        params = self.param_list() if self.lookahead.tag != "RPAREN" else []
        self.match("RPAREN")
        body = self.bloco_stmt()
        return ast.FuncDef(name=name, return_type=None, params=params, body=[body])

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
        """
        if self.lookahead.tag == "LPAREN":
            self.match("LPAREN")
            expr = self.expr()
            self.match("RPAREN")
            return expr
        elif self.lookahead.tag in {"ID", "RECEIVE", "SEND", "OUTPUT", "INPUT"}:
            name = self.lookahead.value
            tag = self.lookahead.tag
            self.match(tag)
            if self.lookahead.tag == "LPAREN":
                args = self.arg_list()
                return ast.Call(type=None, token=Token(tag, name), args=args)
            return ast.ID(type=None, token=Token(tag, name))
        elif self.lookahead.tag == "NUMBER":
            value = self.lookahead.value
            self.match("NUMBER")
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
            raise err.SyntaxError(
                self.lineno, f"Fator inválido: {self.lookahead.value}"
            )

    def expr_bool(self) -> ast.Node:
        """
        <expr_bool> ::= <expr> <rel_op> <expr>
                      | <expr_bool> "&&" <expr_bool>
                      | <expr_bool> "||" <expr_bool>
                      | "!" <expr_bool>
        """
        if self.lookahead.tag == "NOT":
            self.match("NOT")
            expr = self.expr_bool()
            return ast.Unary(type="BOOL", token=Token("!", "!"), expr=expr)
        left = self.expr()
        if self.lookahead.tag in {"EQ", "NEQ", "LT", "GT", "LTE", "GTE"}:
            op = self.lookahead
            self.match(op.tag)
            right = self.expr()
            return ast.Relational(type="BOOL", token=op, left=left, right=right)
        while self.lookahead.tag in {"AND", "OR"}:
            op = self.lookahead
            self.match(op.tag)
            right = self.expr_bool()
            left = ast.Logical(type="BOOL", token=op, left=left, right=right)
        return left
