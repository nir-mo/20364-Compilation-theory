
class CPLException(Exception):
    def __init__(self, line, messgae):
        self.line = line
        self.message = messgae


class CPLCompoundException(CPLException):
    def __init__(self, exceptions):
        self.exceptions = exceptions
