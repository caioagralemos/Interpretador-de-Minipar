"""
Módulo da Tabela de Símbolos

Define classes para gerenciar escopos e variáveis durante a análise.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, Union


@dataclass
class Symbol:
    """
    Classe que representa um símbolo.

    Attributes:
        name (str): Nome do símbolo.
        type (str): Tipo do símbolo.
    """
    name: str
    type: str


@dataclass
class SymTable:
    """
    Classe que representa a tabela de símbolos.

    Attributes:
        table (dict): Tabela de símbolos no escopo atual.
        prev (SymTable): Referência ao escopo anterior.
    """
    table: Dict[str, Symbol] = field(default_factory=dict)
    prev: Optional["SymTable"] = None

    def insert(self, name: str, symbol: Symbol) -> bool:
        if name in self.table:
            return False
        self.table[name] = symbol
        return True

    def find(self, name: str) -> Optional[Symbol]:
        current = self
        while current:
            if name in current.table:
                return current.table[name]
            current = current.prev
        return None


@dataclass
class VarTable:
    """
    Classe que representa a tabela de variáveis

    table (dict): tabela de variáveis
    prev (VarTable): referência â tabela de escopo maior
    """

    table: dict[str, Any] = field(default_factory=dict)
    prev: Optional["VarTable"] = None

    def find(self, string: str) -> Union["VarTable", None]:
        """
        Busca uma variável na tabela pelo seu nome

        Returns:
            VarTable | None: Tabela onde se encontra a variável ou vazio
        """

        st = self
        while st:
            value = st.table.get(string)
            if value is None:
                st = st.prev
                continue
            return st
