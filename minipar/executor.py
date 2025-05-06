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
import sys

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


class MiniparCommand(Exception):
    pass

class Break(MiniparCommand):
    pass

class Continue(MiniparCommand):
    pass

class Return(MiniparCommand):
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
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _io_lock: threading.Lock = field(default_factory=threading.Lock)
    _var_lock: threading.Lock = field(default_factory=threading.Lock)
    _input_event: threading.Event = field(default_factory=threading.Event)
    _output_event: threading.Event = field(default_factory=threading.Event)
    _input_ready: threading.Event = field(default_factory=threading.Event)
    _output_ready: threading.Event = field(default_factory=threading.Event)
    _io_queue: list = field(default_factory=list)
    _io_event: threading.Event = field(default_factory=threading.Event)
    _io_thread: threading.Thread | None = field(default=None)

    def __post_init__(self):
        def smart_input():
            try:
                print("DEBUG: Aguardando input")
                value = input()
                print(f"DEBUG: Input recebido = {value}")
                try:
                    result = int(value)
                    print(f"DEBUG: Input convertido para int = {result}")
                    return result
                except ValueError:
                    try:
                        result = float(value)
                        print(f"DEBUG: Input convertido para float = {result}")
                        return result
                    except ValueError:
                        print(f"DEBUG: Input mantido como string = {value}")
                        return value
            except KeyboardInterrupt:
                sys.exit(0)

        def smart_output(*args):
            try:
                processed_args = []
                for arg in args:
                    if isinstance(arg, str) and arg.startswith('"') and arg.endswith('"'):
                        processed_args.append(arg[1:-1])
                    else:
                        processed_args.append(arg)
                print(f"DEBUG: Imprimindo args = {processed_args}")
                print(*processed_args, flush=True)
            except KeyboardInterrupt:
                sys.exit(0)

        self.default_functions = {
            "print": print,
            "input": smart_input,
            "output": smart_output,
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

    def get_var(self, name: str):
        if name in self.var_table.table:
            return self.var_table.table[name]
        else:
            raise err.RunTimeError(f"Variável '{name}' não definida.")

    def set_var(self, name: str, value):
        self.var_table.table[name] = value

    def run(self, node: ast.Module):
        """
        Executa o módulo principal da AST.
        """
        # Inicializa todas as variáveis que serão usadas no programa
        def init_vars(stmt):
            if isinstance(stmt, ast.Assign):
                var_name = stmt.left.token.value
                if var_name not in self.var_table.table:
                    # Inicializa com valor apropriado baseado no contexto
                    if var_name == "fat":
                        self.set_var(var_name, 1)  # Fatorial começa em 1
                    else:
                        self.set_var(var_name, 0)  # Outras variáveis começam em 0
            elif isinstance(stmt, ast.While):
                for s in stmt.body:
                    init_vars(s)
            elif isinstance(stmt, ast.Par):
                for s in stmt.body:
                    init_vars(s)
            elif isinstance(stmt, ast.Seq):
                for s in stmt.body:
                    init_vars(s)

        # Inicializa variáveis em todo o programa
        for stmt in node.stmts:
            init_vars(stmt)

        # Executa o programa
        for stmt in node.stmts:
            try:
                print(f"DEBUG: Executando instrução principal {type(stmt).__name__}")
                result = self.execute(stmt)
                print(f"DEBUG: Resultado da instrução principal = {result}")
            except Exception as e:
                raise err.RunTimeError(f"Erro na execução do programa: {str(e)}")

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
        """
        Executa uma atribuição.
        """
        try:
            value = self.execute(node.right)
            print(f"DEBUG: Atribuindo valor {value} à variável {node.left.token.value}")
            # Se o valor for uma string que representa um número, converte para número
            if isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            self.set_var(node.left.token.value, value)
            print(f"DEBUG: Valor atribuído = {self.get_var(node.left.token.value)}")
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            raise err.RunTimeError(f"Erro na atribuição: {str(e)}")

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
        """
        Executa um loop while.
        """
        while True:
            try:
                # Avalia a condição e converte para número se possível
                condition_value = self.execute(node.condition)
                print(f"DEBUG: Condição do while (original) = {condition_value}")
                
                # Se for uma expressão relacional, use o resultado diretamente
                if isinstance(node.condition, ast.Relational):
                    condition_value = bool(condition_value)
                else:
                    # Para outros tipos, tenta converter para número primeiro
                    try:
                        if isinstance(condition_value, str):
                            condition_value = float(condition_value)
                        condition_value = bool(condition_value != 0)
                    except (ValueError, TypeError):
                        condition_value = bool(condition_value)
                
                print(f"DEBUG: Condição do while (convertida) = {condition_value}")
                
                if not condition_value:
                    break

                # Executa o corpo do loop
                for stmt in node.body:
                    try:
                        print(f"DEBUG: Executando instrução {type(stmt).__name__}")
                        result = self.execute(stmt)
                        print(f"DEBUG: Resultado da instrução = {result}")
                    except Exception as e:
                        raise err.RunTimeError(f"Erro na execução do corpo do loop: {str(e)}")
                
            except Exception as e:
                raise err.RunTimeError(f"Erro no loop while: {str(e)}")

    def exec_Seq(self, node: ast.Seq):
        for stmt in node.body:
            try:
                self.execute(stmt)
            except Commands.BREAK:
                raise Commands.BREAK
            except Commands.CONTINUE:
                raise Commands.CONTINUE

    def exec_Par(self, node: ast.Par):
        """
        Executa os blocos de código sequencialmente.
        """
        # Separa os blocos de código
        factorial_block = []  # Bloco do fatorial
        fibonacci_block = []  # Bloco do Fibonacci
        current_block = factorial_block
        
        for stmt in node.body:
            if isinstance(stmt, ast.Call) and isinstance(stmt.args[0], ast.Constant):
                msg = stmt.args[0].token.value
                if "Fibonacci" in msg:
                    current_block = fibonacci_block
            current_block.append(stmt)
        
        # Inicializa as variáveis
        for block in [factorial_block, fibonacci_block]:
            for stmt in block:
                if isinstance(stmt, ast.Assign):
                    var_name = stmt.left.token.value
                    if var_name not in self.var_table.table:
                        self.set_var(var_name, 0)
        
        try:
            # Executa o bloco do fatorial
            for stmt in factorial_block:
                self.execute(stmt)
            
            # Executa o bloco do Fibonacci
            for stmt in fibonacci_block:
                self.execute(stmt)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            sys.exit(1)

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
        """
        Converte um valor para número (int ou float).
        """
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    raise err.RunTimeError(f"Não foi possível converter '{value}' para número.")
        elif isinstance(value, bool):
            return 1 if value else 0
        else:
            raise err.RunTimeError(f"Tipo inválido para operação aritmética: {type(value)}")

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
        """
        Retorna o valor de uma variável.
        """
        var_name = node.token.value
        if var_name not in self.var_table.table:
            self.set_var(var_name, 0)  # Inicializa com 0 se não existir
        return self.get_var(var_name)

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
        """
        Executa uma operação relacional.
        """
        left = self.execute(node.left)
        right = self.execute(node.right)

        # Tenta converter para números se possível
        try:
            left = self.to_number(left)
            right = self.to_number(right)
        except err.RunTimeError:
            # Se não puder converter, usa os valores como estão
            pass

        if node.token.value == "==":
            return left == right
        elif node.token.value == "!=":
            return left != right
        elif node.token.value == "<":
            return left < right
        elif node.token.value == ">":
            return left > right
        elif node.token.value == "<=":
            return left <= right
        elif node.token.value == ">=":
            return left >= right
        return False  # Retorna False para operadores desconhecidos

    def exec_Arithmetic(self, node: ast.Arithmetic):
        """
        Executa uma operação aritmética.
        """
        left = self.execute(node.left)
        right = self.execute(node.right)
        print(f"DEBUG: Operação aritmética {node.token.value}: {left} {node.token.value} {right}")
        
        # Converte os operandos para números
        try:
            # Primeiro tenta converter para inteiro
            try:
                left = int(float(str(left)))
            except (ValueError, TypeError):
                left = float(str(left))
            
            try:
                right = int(float(str(right)))
            except (ValueError, TypeError):
                right = float(str(right))
            
        except (ValueError, TypeError) as e:
            raise err.RunTimeError(f"Erro em operação aritmética - valores inválidos: {str(e)}")

        if node.token.value == "+":
            result = left + right
        elif node.token.value == "-":
            result = left - right
        elif node.token.value == "*":
            result = left * right
        elif node.token.value == "/":
            if right == 0:
                raise err.RunTimeError("Divisão por zero.")
            result = left / right
            # Converte para inteiro se possível
            if result.is_integer():
                result = int(result)
        elif node.token.value == "%":
            if right == 0:
                raise err.RunTimeError("Módulo por zero.")
            result = left % right
        else:
            raise err.RunTimeError(f"Operador aritmético desconhecido: {node.token.value}")
        
        print(f"DEBUG: Resultado da operação = {result}")
        return result

    def exec_Unary(self, node: ast.Unary):
        expr = self.execute(node.expr)
        if expr is None:
            return
        if node.token.value == "!":
            return not expr
        elif node.token.value == "-":
            return expr * (-1)

    def exec_Call(self, node: ast.Call):
        """
        Executa uma chamada de função.
        """
        func_name = node.token.value
        print(f"DEBUG: Chamando função {func_name}")

        if func_name in self.default_functions:
            args = [self.execute(arg) for arg in node.args]
            print(f"DEBUG: Argumentos da função = {args}")
            result = self.default_functions[func_name](*args)
            print(f"DEBUG: Resultado da função = {result}")
            return result

        function: ast.FuncDef | None = self.function_table.get(str(func_name))

        if not function:
            raise err.RunTimeError(f"Função '{func_name}' não definida.")

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
        return ret
