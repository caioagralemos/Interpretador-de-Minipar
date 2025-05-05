"""
Módulo de Análise Léxica

Responsável por dividir o código em tokens.
"""

import re
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field

from minipar.token import TOKEN_PATTERNS, Token

NextToken = Generator[tuple[Token, int], None, None]


class ILexer(ABC):
    """
    Interface para a Análise Léxica
    """

    @abstractmethod
    def scan(self) -> NextToken:
        pass


@dataclass
class Lexer(ILexer):
    """
    Classe para análise léxica.

    Attributes:
        data (str): Código fonte da linguagem Minipar.
    """
    data: str
    line: int = field(default=1, init=False)

    def scan(self):
        regex = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_PATTERNS), re.MULTILINE)
        for match in regex.finditer(self.data):
            kind = match.lastgroup
            value = match.group()
            if kind == "WHITESPACE" or kind == "COMMENT" or kind == "MLCOMMENT":
                self.line += value.count("\n")
                continue
            #print(f"[Lexer] Token encontrado: {kind} ({value}) na linha {self.line}")
            yield Token(kind, value), self.line
