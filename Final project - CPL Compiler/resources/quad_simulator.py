# written by Yaniv Noy   works with Python 2.7
from __future__ import print_function
import re
from sys import stdin, stderr, argv

trace = False


class symtable(object):
    """ name -> value table """

    class _symdata(object):
        def __init__(self, value):
            self.value = value
            # cur_inst_num is a global set by interpret()
            self.decl_line = cur_inst_num

    def __init__(self):
        self._t = dict()  # name -> _symdata dictionary

    def get(self, numt, sym):
        """ retrieves the value of sym, ensuring its type is numt """
        return self._get_sd(numt, sym).value

    def update(self, numt, sym, value):
        """ adds or updates a symbol, with type constraints """
        try:
            self._get_sd(numt, sym).value = value
        except KeyError:
            self._t[sym] = symtable._symdata(value)

    _is_sym_re = re.compile("[_a-zA-Z][_a-zA-Z0-9]*$")

    @staticmethod
    def is_sym(name):
        return type(name) is str and symtable._is_sym_re.match(name) != None

    def _get_sd(self, numt, sym):
        """ returns sym's _symdata, ensuring the type is numt """
        assert symtable.is_sym(sym), str(sym) + " is not a valid symbol"

        sd = self._t[sym]
        if type(sd.value) is not numt:
            raise TypeError(
                "%s is %s but must be %s (see instruction %d)"
                % (sym, type(sd.value).__name__, numt.__name__, sd.decl_line))

        return sd


# singleton
symtable = symtable()


def ASN(numt, asym, av):
    symtable.update(numt, asym, val(numt, av))


def PRT(numt, av):
    print(val(numt, av))


def INP(numt, asym):
    symtable.update(numt, asym, numt(raw_input(numt.__name__ + "? ")))


def EQL(numt, asym, av1, av2):
    res = compare(numt, av1, av2)
    symtable.update(int, asym, int(res == 0))


def NQL(numt, asym, av1, av2):
    res = compare(numt, av1, av2)
    symtable.update(int, asym, int(res != 0))


def LSS(numt, asym, av1, av2):
    res = compare(numt, av1, av2)
    symtable.update(int, asym, int(res < 0))


def GRT(numt, asym, av1, av2):
    res = compare(numt, av1, av2)
    symtable.update(int, asym, int(res > 0))


def ADD(numt, asym, av1, av2):
    symtable.update(numt, asym, val(numt, av1) + val(numt, av2))


def SUB(numt, asym, av1, av2):
    symtable.update(numt, asym, val(numt, av1) - val(numt, av2))


def DIV(numt, asym, av1, av2):
    # Converting result to numt for compatability with Py3k's division
    div_res = val(numt, av1) / val(numt, av2)
    symtable.update(numt, asym, numt(div_res))


def MLT(numt, asym, av1, av2):
    symtable.update(numt, asym, val(numt, av1) * val(numt, av2))


def IASN(*args): ASN(int, *args)


def IPRT(*args): PRT(int, *args)


def IINP(*args): INP(int, *args)


def IEQL(*args): EQL(int, *args)


def INQL(*args): NQL(int, *args)


def ILSS(*args): LSS(int, *args)


def IGRT(*args): GRT(int, *args)


def IADD(*args): ADD(int, *args)


def ISUB(*args): SUB(int, *args)


def IDIV(*args): DIV(int, *args)


def IMLT(*args): MLT(int, *args)


def RASN(*args): ASN(float, *args)


def RPRT(*args): PRT(float, *args)


def RINP(*args): INP(float, *args)


def REQL(*args): EQL(float, *args)


def RNQL(*args): NQL(float, *args)


def RLSS(*args): LSS(float, *args)


def RGRT(*args): GRT(float, *args)


def RADD(*args): ADD(float, *args)


def RSUB(*args): SUB(float, *args)


def RDIV(*args): DIV(float, *args)


def RMLT(*args): MLT(float, *args)


def ITOR(asym, av):
    symtable.update(float, asym, float(val(int, av)))


def RTOI(asym, av):
    symtable.update(int, asym, int(val(float, av)))


def JUMP(inst_num):
    l = val(int, inst_num)
    assert l > 0, "jump target must be positive"
    codelines.send(l)


def JMPZ(inst_num, asym):
    if val(int, asym) == 0:
        JUMP(inst_num)


def HALT():
    codelines.close()


def val(numt, asym_or_val):
    if symtable.is_sym(asym_or_val):
        return symtable.get(numt, asym_or_val)
    else:
        return numt(asym_or_val)


def compare(numt, av1, av2):
    return val(numt, av1) - val(numt, av2)


def error(err_inst_num, err_inst_code, msg):
    print("error at %d(`%s`):" % (err_inst_num, err_inst_code), msg,
          file=stderr)


def codelines_generator(code_string):
    """Generates the next instruction as (inum, i) from the raw code_string.
    Accepts a new instruction number."""

    # First, remove comments (anything after a '#' or between /* */)
    code_string = re.sub("#.*", "", code_string)
    code_string = re.sub(r"/\*.+?\*/", "", code_string, re.DOTALL)

    # Next, find the code in each line to allow a flexible input
    # format, such as instruction numbering, empty lines, etc.
    code_only_re = r"""  [A-Z]{4}\b[ \t]*           # op code
                         (?:[a-zA-Z-0-9._]+[ \t]*)  # non-capturing arg group
                         {0,3}                      # 0 - 3 arguments
                         """
    # Note: codelines start at 0, while instruction numbering starts at 1
    codelines = re.findall(code_only_re, code_string, flags=re.VERBOSE)
    ip = 1
    try:
        while True:
            line = codelines[ip - 1]
            if trace:
                print("Executing `%s`" % line)
            jmp_ip = yield (ip, line)
            prev_ip = ip  # save previous ip only after a successful execution
            if jmp_ip:
                yield None  # dummy yield for send() result
                ip = jmp_ip
            else:
                ip = ip + 1
    except IndexError:
        if jmp_ip:
            error(prev_ip, codelines[prev_ip - 1],
                  "can't jump to " + str(ip))
        else:
            error(ip, "(none)", "missing HALT command")


code = """\
#  output should be 11, 5.5, 5, 4
1. IASN i -5
2. IASN j 16
3. IADD j i j
4  IPRT j
5  ITOR rj j
6  RMLT rj rj 0.5
7  RPRT rj
8  RTOI irj rj
9  IPRT irj

IASN s 0        # check comparison operators
REQL b 1 1.0
IADD s s b
RLSS b 1 2.5
IADD s s b
INQL b 1 2
IADD s s b
RGRT b 5.1 5
IADD s s b
IPRT s

IASN x 0
JMPZ x 1    # no jump - no error

HALT
"""


def interpret():
    try:
        global cur_inst_num
        for cur_inst_num, codeline in codelines:
            tokens = codeline.split()

            opname = tokens[0]
            globals()[opname](*tokens[1:])

    except TypeError as e:
        error(cur_inst_num, codeline, str(e))
        raise
    except KeyError as e:
        error(cur_inst_num, codeline, "bad opcode: '%s'" % opname)


if __name__ == "__main__":
    if len(argv) == 1:
        print("Interpreting hard-coded QUD")
    else:
        if argv[1] == "-":
            code = stdin.read()
        else:
            code = open(argv[1]).read()

        trace = len(argv) > 2 and argv[2] == "-t"

    codelines = codelines_generator(code)
    interpret()
