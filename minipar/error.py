class SyntaxError(Exception):

    def __init__(self, line: int, msg: str):
        self.message = f"Erro de Sintaxe (linha {line}): {msg}"
        super().__init__(self.message)


class SemanticError(Exception):

    def __init__(self, msg: str):
        self.message = f"Erro de Semântica: {msg}"
        super().__init__(self.message)


class RunTimeError(Exception):

    def __init__(self, msg: str):
        self.message = f"Erro em Tempo de Execução: {msg}"
        super().__init__(self.message)
