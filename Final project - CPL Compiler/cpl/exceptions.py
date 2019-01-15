
class CPLException(Exception):
    pass


class CPLCompoundException(CPLException):
    def __init__(self, exceptions):
        self.exceptions = exceptions
