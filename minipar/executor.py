"""
Módulo de execução do interpretador Minipar.

Define a lógica para executar a AST gerada pelo parser.
"""

import socket
import threading
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from time import sleep

from minipar import ast
from minipar import error as err
from minipar.symtable import VarTable
from minipar.token import Token


class Commands(Enum):
    BREAK = "BREAK"
    CONTINUE = "CONTINUE"
    RETURN = "RETURN"


class IExecutor(ABC):
    """
    Interface para o executor da AST.
    """

    @abstractmethod
    def run(self, node: ast.Module):
        pass

    @abstractmethod
    def execute(self, node: ast.Node):
        pass

    @abstractmethod
    def enter_scope(self):
        pass

    @abstractmethod
    def exit_scope(self):
        pass


@dataclass
class Executor(IExecutor):
    """
    Executor responsável por interpretar e executar a AST.

    Attributes:
        var_table (VarTable): Tabela de variáveis.
        function_table (dict): Tabela de funções declaradas.
        connection_table (dict): Tabela de conexões de canais.
    """
    var_table: VarTable = field(default_factory=VarTable)
    function_table: dict[str, ast.FuncDef] = field(default_factory=dict)
    connection_table: dict[str, socket.socket] = field(default_factory=dict)

    def __post_init__(self):
        self.default_functions = {
            "print": print,
            "input": input,
            "to_number": self.to_number,
            "to_string": str,
            "to_bool": bool,
            "sleep": sleep,
            "send": self.send,
            "close": self.close,
            "len": len,
            "isalpha": self.isalpha,
            "isnum": self.isnum,
        }

    def run(self, node: ast.Module):
        """
        Executa o módulo principal da AST.
        """
        for stmt in node.stmts:
            self.execute(stmt)

    def execute(self, node: ast.Node):
        """
        Executa um nó da AST.
        """
        method_name = f"exec_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method:
            return method(node)
        else:
            raise err.RunTimeError(f"Nó não suportado: {type(node).__name__}")

    def enter_scope(self):
        """
        Entra em um novo escopo.
        """
        self.var_table = VarTable(prev=self.var_table)

    def exit_scope(self):
        """
        Sai do escopo atual.
        """
        if self.var_table.prev:
            self.var_table = self.var_table.prev

    ###### EXECUÇÃO DE DECLARAÇÕES ######

    def exec_Assign(self, node: ast.Assign):
        value = self.execute(node.right)
        var_name = node.left.token.value
        self.var_table.table[var_name] = value

    def exec_If(self, node: ast.If):
        condition = self.execute(node.condition)
        if condition:
            self.enter_scope()
            try:
                for stmt in node.body:
                    self.execute(stmt)
            except Commands.BREAK:
                self.exit_scope()
                raise Commands.BREAK
            except Commands.CONTINUE:
                self.exit_scope()
                raise Commands.CONTINUE
            self.exit_scope()
        elif node.else_stmt:
            self.enter_scope()
            try:
                for stmt in node.else_stmt:
                    self.execute(stmt)
            except Commands.BREAK:
                self.exit_scope()
                raise Commands.BREAK
            except Commands.CONTINUE:
                self.exit_scope()
                raise Commands.CONTINUE
            self.exit_scope()

    def exec_While(self, node: ast.While):
        while self.execute(node.condition):
            self.enter_scope()
            try:
                for stmt in node.body:
                    self.execute(stmt)
            except Commands.BREAK:
                self.exit_scope()
                break
            except Commands.CONTINUE:
                self.exit_scope()
                continue
            self.exit_scope()

    def exec_Seq(self, node: ast.Seq):
        for stmt in node.body:
            try:
                self.execute(stmt)
            except Commands.BREAK:
                raise Commands.BREAK
            except Commands.CONTINUE:
                raise Commands.CONTINUE

    def exec_Par(self, node: ast.Par):
        threads = []
        for stmt in node.body:
            thread_executor = Executor(
                var_table=deepcopy(self.var_table),
                function_table=deepcopy(self.function_table),
            )
            thread = threading.Thread(target=thread_executor.execute, args=(stmt,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def exec_CChannel(self, node: ast.CChannel):
        def resolve(val):
            if isinstance(val, ast.Node):
                return self.execute(val)
            return val
        localhost = resolve(node.localhost)
        port = resolve(node.port)
        # Remove aspas duplas se presentes
        if isinstance(localhost, str) and localhost.startswith('"') and localhost.endswith('"'):
            localhost = localhost[1:-1]
        if not isinstance(localhost, str):
            localhost = str(localhost)
        if not isinstance(port, int):
            try:
                port = int(port)
            except Exception:
                raise err.RunTimeError(f"Porta inválida: {port}")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((localhost, port))
        self.connection_table[node.name] = client

    def exec_SChannel(self, node: ast.SChannel):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((node.localhost, int(node.port)))
        server.listen(10)
        conn, _ = server.accept()
        description = self.execute(node.description)
        if description:
            conn.send(description.encode("utf-8"))

        function: ast.FuncDef = self.function_table[node.func_name]
        while True:
            data = conn.recv(2048).decode()
            print(f"received: {data}")
            if not data:
                conn.close()
                break

            call = ast.Call(
                type=function.return_type,
                token=Token("ID", function.name),
                args=[
                    ast.Constant(type="STRING", token=Token("STRING", data))
                ],
                id=None,
                oper=None,
            )

            ret = self.exec_Call(call)

            conn.send(str(ret).encode("utf-8"))

    ######  PERSONALIZED FUNCTIONS ######

    def to_number(self, value):
        try:
            return int(value)
        except ValueError:
            return float(value)

    def isalpha(self, value):
        return str(value).isalpha()

    def isnum(self, value):
        return str(value).isnumeric()

    def send(self, conn_name: str, data: str):
        client = self.connection_table[conn_name]

        client.send(data.encode("utf-8"))

        return client.recv(2048).decode("utf-8")

    def close(self, conn_name: str):
        client = self.connection_table[conn_name]

        client.close()

    ###### EXECUÇÃO DE EXPRESSÕES ######

    def exec_Constant(self, node: ast.Constant):
        return node.token.value

    def exec_ID(self, node: ast.ID):
        var_name = node.token.value
        if var_name in self.var_table.table:
            return self.var_table.table[var_name]
        else:
            raise err.RunTimeError(f"Variável '{var_name}' não definida.")

    def exec_Access(self, node: ast.Access):
        """
        Executa o acesso a um elemento (ex.: array ou estrutura).

        Args:
            node (ast.Access): Nó da AST representando o acesso.

        Returns:
            O valor do elemento acessado.
        """
        base = self.execute(node.base)
        index = self.execute(node.index)

        if isinstance(base, list):
            try:
                return base[index]
            except IndexError:
                raise err.RunTimeError(f"Índice fora do intervalo: {index}")
        elif isinstance(base, dict):
            if index in base:
                return base[index]
            else:
                raise err.RunTimeError(f"Chave '{index}' não encontrada.")
        else:
            raise err.RunTimeError(f"Tipo inválido para acesso: {type(base).__name__}")

    def exec_Logical(self, node: ast.Logical):
        left = self.execute(node.left)
        right = self.execute(node.right)
        if node.token.value == "&&":
            return left and right
        elif node.token.value == "||":
            return left or right

    def exec_Relational(self, node: ast.Relational):
        left = self.execute(node.left)
        right = self.execute(node.right)
        if node.token.value == "==":
            return left == right
        elif node.token.value == "!=":
            return left != right
        elif node.token.value == "<":
            return left < right
        elif node.token.value == ">":
            return left > right
        elif node.token.value == "<=" :
            return left <= right
        elif node.token.value == ">=":
            return left >= right

    def exec_Arithmetic(self, node: ast.Arithmetic):
        left = self.execute(node.left)
        right = self.execute(node.right)
        if node.token.value == "+":
            return left + right
        elif node.token.value == "-":
            return left - right
        elif node.token.value == "*":
            return left * right
        elif node.token.value == "/":
            return left / right
        elif node.token.value == "%":
            return left % right

    def exec_Unary(self, node: ast.Unary):
        expr = self.execute(node.expr)
        if expr is None:
            return
        if node.token.value == "!":
            return not expr
        elif node.token.value == "-":
            return expr * (-1)

    def exec_Call(self, node: ast.Call):

        func_name = node.oper if node.oper else node.token.value

        if func_name not in {"close", "send"}:
            if self.default_functions.get(func_name):
                args = [self.execute(arg) for arg in node.args]
                return self.default_functions[func_name](*args)
        else:
            conn_name = node.token.value
            if func_name == "send":
                args = [self.execute(arg) for arg in node.args]
                return self.default_functions[func_name](conn_name, *args)
            else:
                return self.default_functions[func_name](conn_name)

        function: ast.FuncDef | None = self.function_table.get(str(func_name))

        if not function:
            return

        self.enter_scope()

        for param in function.params.items():
            name, (_, default) = param
            if default:
                self.var_table.table[name] = self.execute(default)

        for param, arg in zip(function.params.items(), node.args):
            name, _ = param
            value = self.execute(arg)
            self.var_table.table[name] = value

        ret = self.exec_block(function.body)
        self.exit_scope()
        return
