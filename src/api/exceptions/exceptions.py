class NotFoundError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class InvalidIdError(Exception):
    def __init__(self, detail: str = "ID inválido"):
        self.detail = detail

class InternalError(Exception):
    def __init__(self, detail: str = "Error interno del servidor"):
        self.detail = detail