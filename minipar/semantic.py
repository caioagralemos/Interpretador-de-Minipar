"""
Módulo de Análise Semântica

Realiza verificações semânticas na AST gerada pela análise sintática.
"""

from dataclasses import dataclass, field
from typing import List
from minipar import ast, error as err


@dataclass
class SemanticAnalyzer:
    """
    Classe para análise semântica da AST.

    Attributes:
        context_stack (list): Pilha de contexto para escopos.
        function_table (dict): Tabela de funções declaradas.
    """
    context_stack: List[ast.Node] = field(default_factory=list)
    function_table: dict = field(default_factory=dict)

    def visit(self, node: ast.Node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.Node):
        for attr in dir(node):
            value = getattr(node, attr)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.Node):
                        self.visit(item)
            elif isinstance(value, ast.Node):
                self.visit(value)

    def visit_Assign(self, node: ast.Assign):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        if left_type != right_type:
            raise err.SemanticError("Tipos incompatíveis na atribuição.")

    def visit_If(self, node: ast.If):
        cond_type = self.visit(node.condition)
        if cond_type != "BOOL":
            raise err.SemanticError("Condição do 'if' deve ser do tipo BOOL.")
        for stmt in node.body:
            self.visit(stmt)
        if node.else_stmt:
            for stmt in node.else_stmt:
                self.visit(stmt)

    def visit_While(self, node: ast.While):
        cond_type = self.visit(node.condition)
        if cond_type != "BOOL":
            raise err.SemanticError("Condição do 'while' deve ser do tipo BOOL.")
        for stmt in node.body:
            self.visit(stmt)

    def visit_Relational(self, node: ast.Relational):
        # Expressões relacionais sempre retornam BOOL
        return "BOOL"

    def visit_Logical(self, node: ast.Logical):
        # Expressões lógicas sempre retornam BOOL
        return "BOOL"

    def visit_Unary(self, node: ast.Unary):
        # Expressão unária '!' sempre retorna BOOL
        if node.token.value == "!":
            return "BOOL"
        return self.visit(node.expr)
