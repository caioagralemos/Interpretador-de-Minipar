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
    position: int = field(default=0, init=False)

    def scan(self):
        """
        Realiza a análise léxica do código fonte.
        
        Yields:
            tuple[Token, int]: Um token e o número da linha correspondente.
        """
        regex = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_PATTERNS), re.MULTILINE)
        
        # Reset position and line counters
        self.position = 0
        self.line = 1
        
        # Keep track of current position independently
        current_pos = 0
        
        for match in regex.finditer(self.data):
            kind = match.lastgroup
            value = match.group()
            
            # Update position
            match_start = match.start()
            match_end = match.end()
            
            # Count lines in skipped text
            if match_start > current_pos:
                self.line += self.data[current_pos:match_start].count('\n')
            
            # Update current position
            current_pos = match_end
            
            # Skip whitespace and comments
            if kind == "WHITESPACE" or kind == "COMMENT" or kind == "MLCOMMENT":
                self.line += value.count("\n")
                continue
                
            # Update the object's position
            self.position = match_end
            
            # Return the token and line number
            yield Token(kind, value), self.line
            
            # Count newlines in the token itself
            self.line += value.count("\n")
