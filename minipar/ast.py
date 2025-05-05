"""
Módulo da Árvore Sintática Abstrata (AST)

O módulo da AST conta com uma estrutura de classes responsável
por representar o conjunto de declarações e expressões da linguagem.
"""

from dataclasses import dataclass
from typing import List, Union
from minipar.token import Token


class Node:
    """
    Classe base que representa um Nó na AST.
    """
    pass


@dataclass
class Statement(Node):
    """
    Classe base que representa uma declaração.
    """
    pass


@dataclass
class Expression(Node):
    """
    Classe base que representa uma expressão.

    Attributes:
        type (str): Tipo de retorno da expressão.
        token (Token): Token capturado pela expressão.
    """
    type: str
    token: Token

    @property
    def name(self) -> Union[str, None]:
        return self.token.value if self.token else None


# Tipos auxiliares
Body = List[Union[Statement, Expression]]  # Corpo de blocos
Arguments = List[Expression]  # Argumentos de funções
Parameters = List[tuple[str, str]]  # Lista de parâmetros (tipo, nome)


##### EXPRESSIONS #####

@dataclass
class Constant(Expression):
    pass


@dataclass
class ID(Expression):
    decl: bool = False


@dataclass
class Logical(Expression):
    left: Expression
    right: Expression


@dataclass
class Relational(Expression):
    left: Expression
    right: Expression


@dataclass
class Arithmetic(Expression):
    left: Expression
    right: Expression


@dataclass
class Unary(Expression):
    expr: Expression


@dataclass
class Call(Expression):
    args: Arguments


@dataclass
class Access(Expression):
    """
    Representa o acesso a um elemento (ex.: array ou estrutura).

    Attributes:
        base (Expression): A expressão base (ex.: nome do array).
        index (Expression): O índice ou chave de acesso.
    """
    base: Expression
    index: Expression


##### STATEMENTS #####

@dataclass
class Module(Statement):
    stmts: Body


@dataclass
class Assign(Statement):
    left: Expression
    right: Expression


@dataclass
class If(Statement):
    condition: Expression
    body: Body
    else_stmt: Union[Body, None]


@dataclass
class While(Statement):
    condition: Expression
    body: Body


@dataclass
class FuncDef(Statement):
    name: str
    return_type: str
    params: Parameters
    body: Body


@dataclass
class Seq(Statement):
    body: Body


@dataclass
class Par(Statement):
    body: Body


@dataclass
class CChannel(Statement):
    name: str
    localhost: Expression
    port: Expression


@dataclass
class SChannel(Statement):
    """
    Representa um canal de servidor.

    Attributes:
        name (str): Nome do canal.
        localhost (str): Endereço do servidor.
        port (int): Porta do servidor.
        description (Expression): Descrição opcional enviada ao cliente.
        func_name (str): Nome da função a ser executada ao receber dados.
    """
    name: str
    localhost: str
    port: int
    description: Expression
    func_name: str


@dataclass
class Break(Statement):
    pass

@dataclass
class Continue(Statement):
    pass
