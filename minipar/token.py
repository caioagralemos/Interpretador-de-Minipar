"""
Módulo de tokens

O módulo de tokens define a classe Token e os padrões necessários
para a análise léxica.
"""

from dataclasses import dataclass

# Padrões dos tokens
TOKEN_PATTERNS = [
    ("STRING_TYPE", r"\bstring\b"),
    ("INT_TYPE", r"\bint\b"),
    ("BOOL_TYPE", r"\bbool\b"),
    ("SEQ", r"SEQ"),
    ("PAR", r"PAR"),
    ("C_CHANNEL", r"c_channel"),
    ("S_CHANNEL", r"s_channel"),
    ("FUNC", r"function"),
    ("IF", r"if"),
    ("ELSE", r"else"),
    ("WHILE", r"while"),
    ("SEND", r"send"),
    ("RECEIVE", r"receive"),
    ("OUTPUT", r"output"),
    ("BOOL", r"\b(true|false)\b"),
    ("NUMBER", r"\b\d+\b"),
    ("STRING", r'"([^"]*)"'),
    ("EQ", r"=="),
    ("NEQ", r"!="),
    ("LTE", r"<="),
    ("GTE", r">="),
    ("LT", r"<"),
    ("GT", r">"),
    ("AND", r"&&"),
    ("OR", r"\|\|"),
    ("NOT", r"!"),
    ("ASSIGN", r"="),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("MULT", r"\*"),
    ("MLCOMMENT", r"/\*[\s\S]*?\*/"),  # Corrigido para multiline robusto e antes de DIV
    ("DIV", r"/"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMMA", r","),
    ("SEMICOLON", r";"),
    ("WHITESPACE", r"\s+"),
    ("COMMENT", r"#.*"),
    ("INPUT", r"input"),
    ("ID", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("BREAK", r"break"),
    ("CONTINUE", r"continue"),
]

@dataclass
class Token:
    """
    Classe que representa um Token (Lexema) da linguagem.

    Attributes:
        tag (str): Tag do token.
        value (str): Valor do token.
    """
    tag: str
    value: str

    def __repr__(self):
        return f"{{{self.value}, {self.tag}}}"
