import sys


# ─── Tokenizer ───────────────────────────────────────────────────────────────

_KEYWORDS = {
    '\ud615\uc218': 'DECLARE',
    '\uc0c8\ub07c': 'TYPE',
    '\ucc22': 'ASSIGN',
    '\ub18c': 'INPUT',
    '\ubbf8\uce5c\ub144': 'IF',
    '\ubcd1\uc2e0': 'ELSE',
    '\uc9c0\uac00 \ub098\uc628 \uad6c\uba39': 'WHILE',
    '\uc528\ubc1c\ub144': 'TRUE',
    '\uc528\ubc1c\ub144\uc544': 'TRUE',
    '\uc2dc\ubc1c\ub828': 'FALSE',
    '\uc2dc\ud314\ub828': 'NOT',
    '\uac1c\uc0c8\ub07c': 'FREE',
    '\uce7c\ub85c \uc465\uc2e0\ub2e4': 'INC',
    '\uc774 \uc778\uac04 \uc4f0.\ub808.\uae30.\uc57c': 'PANIC',
}

_KEYWORD_STRINGS = sorted(_KEYWORDS.keys(), key=len, reverse=True)

_START = '\uc57c, \uc774 \uc528\ubc1c\ub828\uc544'
_END = '\ub2c8 \uce5c\uc815 \uc5c4\ub9c8, \uc529\uad6c\uba39 \ucc22\uc73c\uba74 \uc88b\uaca0\ub2c8?'


class Token:
    def __init__(self, typ, value=None, pos=0):
        self.type = typ
        self.value = value
        self.pos = pos

    def __repr__(self):
        return f'T({self.type},{self.value!r})'


def tokenize(code):
    tokens = []
    pos = 0
    n = len(code)

    while pos < n:
        ch = code[pos]

        if ch in ' \t\n\r':
            pos += 1
            continue

        if ch == ',':
            tokens.append(Token('COMMA', pos=pos))
            pos += 1
            continue

        if ch == '.':
            tokens.append(Token('DOT', pos=pos))
            pos += 1
            continue

        if ch == '(':
            tokens.append(Token('LPAREN', pos=pos))
            pos += 1
            continue

        if ch == ')':
            tokens.append(Token('RPAREN', pos=pos))
            pos += 1
            continue

        if ch == '{':
            tokens.append(Token('LBRACE', pos=pos))
            pos += 1
            continue

        if ch == '}':
            tokens.append(Token('RBRACE', pos=pos))
            pos += 1
            continue

        if ch.isdigit():
            start = pos
            pos += 1
            while pos < n and code[pos].isdigit():
                pos += 1
            tokens.append(Token('NUMBER', int(code[start:pos]), pos=start))
            continue

        if ch in '><=!':
            if pos + 1 < n and code[pos:pos+2] in ('>=', '<=', '==', '!='):
                tokens.append(Token('OPERATOR', code[pos:pos+2], pos=pos))
                pos += 2
                continue
            if ch in '><':
                tokens.append(Token('OPERATOR', ch, pos=pos))
                pos += 1
                continue
            pos += 1
            continue

        matched = False
        for kw in _KEYWORD_STRINGS:
            if pos + len(kw) <= n and code[pos:pos+len(kw)] == kw:
                tokens.append(Token('KEYWORD', kw, pos=pos))
                pos += len(kw)
                matched = True
                break

        if not matched:
            pos += 1

    tokens.append(Token('EOF'))
    return tokens


# ─── AST ─────────────────────────────────────────────────────────────────────

class Program:
    def __init__(self, statements):
        self.statements = statements

class DeclareStmt:
    def __init__(self, var_name): self.var_name = var_name
class AssignStmt:
    def __init__(self, var_name, value_expr): self.var_name = var_name; self.value_expr = value_expr
class IncStmt:
    def __init__(self, var_name): self.var_name = var_name
class NotStmt:
    def __init__(self, var_name): self.var_name = var_name
class FreeStmt:
    def __init__(self, var_name): self.var_name = var_name
class PanicStmt:
    def __init__(self, var_name): self.var_name = var_name
class IfStmt:
    def __init__(self, condition, body, else_body=None): self.condition = condition; self.body = body; self.else_body = else_body
class WhileStmt:
    def __init__(self, condition, body): self.condition = condition; self.body = body

class Expr:
    pass
class NumberLiteral(Expr):
    def __init__(self, value): self.value = value
class VarRef(Expr):
    def __init__(self, name): self.name = name
class BoolLiteral(Expr):
    def __init__(self, value): self.value = value
class BinaryOp(Expr):
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right


# ─── Parser ──────────────────────────────────────────────────────────────────

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token('EOF')

    def advance(self):
        t = self.peek()
        self.pos += 1
        return t

    def expect(self, typ, value=None):
        t = self.peek()
        if t.type != typ or (value is not None and t.value != value):
            raise ParseError(f'line ~{t.pos}: expected {value or typ}, got {t.type}({t.value})')
        return self.advance()

    def parse(self):
        stmts = []
        while self.peek().type != 'EOF':
            s = self.parse_statement()
            if s:
                stmts.append(s)
        return Program(stmts)

    def parse_statement(self):
        t = self.peek()
        if t.type == 'KEYWORD' and t.value == '\ud615\uc218':
            return self._declare()
        if t.type == 'KEYWORD' and t.value == '\ubbf8\uce5c\ub144':
            return self._if()
        if t.type == 'KEYWORD' and t.value == '\uc9c0\uac00 \ub098\uc628 \uad6c\uba39':
            return self._while()
        if t.type == 'KEYWORD' and t.value == '\ubcd1\uc2e0':
            raise ParseError('else without matching if')
        if t.type == 'NUMBER':
            return self._var_op()
        raise ParseError(f'line ~{t.pos}: unexpected {t.type}({t.value})')

    def _declare(self):
        self.expect('KEYWORD', '\ud615\uc218')
        self.expect('COMMA')
        self.expect('KEYWORD', '\uc0c8\ub07c')
        self.expect('COMMA')
        name = self.expect('NUMBER').value
        self.expect('DOT')
        return DeclareStmt(name)

    def _if(self):
        self.expect('KEYWORD', '\ubbf8\uce5c\ub144')
        self.expect('COMMA')
        self.expect('LPAREN')
        cond = self._condition()
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = self._block()
        self.expect('RBRACE')
        self.expect('DOT')
        else_body = None
        if self.peek().type == 'KEYWORD' and self.peek().value == '\ubcd1\uc2e0':
            self.advance()
            self.expect('LBRACE')
            else_body = self._block()
            self.expect('RBRACE')
            self.expect('DOT')
        return IfStmt(cond, body, else_body)

    def _while(self):
        self.expect('KEYWORD', '\uc9c0\uac00 \ub098\uc628 \uad6c\uba39')
        self.expect('COMMA')
        self.expect('LPAREN')
        cond = self._condition()
        self.expect('RPAREN')
        self.expect('LBRACE')
        body = self._block()
        self.expect('RBRACE')
        self.expect('DOT')
        return WhileStmt(cond, body)

    def _block(self):
        stmts = []
        while self.peek().type not in ('RBRACE', 'EOF'):
            s = self.parse_statement()
            if s:
                stmts.append(s)
        return stmts

    def _var_op(self):
        var = self.expect('NUMBER').value
        self.expect('COMMA')
        kw = self.expect('KEYWORD').value

        if kw == '\ucc22':
            val = self._assign_val()
            self.expect('DOT')
            return AssignStmt(var, val)
        if kw == '\uce7c\ub85c \uc465\uc2e0\ub2e4':
            self.expect('DOT')
            return IncStmt(var)
        if kw == '\uc2dc\ud314\ub828':
            self.expect('DOT')
            return NotStmt(var)
        if kw == '\uac1c\uc0c8\ub07c':
            self.expect('DOT')
            return FreeStmt(var)
        if kw == '\uc774 \uc778\uac04 \uc4f0.\ub808.\uae30.\uc57c':
            self.expect('DOT')
            return PanicStmt(var)
        raise ParseError(f'unknown keyword: {kw}')

    def _assign_val(self):
        t = self.peek()
        if t.type == 'KEYWORD':
            if t.value in ('\uc528\ubc1c\ub144', '\uc528\ubc1c\ub144\uc544'):
                self.advance(); return BoolLiteral(True)
            if t.value == '\uc2dc\ubc1c\ub828':
                self.advance(); return BoolLiteral(False)
            if t.value == '\ub18c':
                self.advance(); return None
        if t.type == 'NUMBER':
            self.advance(); return NumberLiteral(t.value)
        raise ParseError(f'line ~{t.pos}: expected value, got {t.type}({t.value})')

    def _condition(self):
        left = self._val()
        if self.peek().type == 'OPERATOR':
            op = self.advance().value
            right = self._val()
            return BinaryOp(left, op, right)
        return left

    def _val(self):
        t = self.peek()
        if t.type == 'NUMBER':
            self.advance(); return VarRef(t.value)
        if t.type == 'KEYWORD':
            if t.value in ('\uc528\ubc1c\ub144', '\uc528\ubc1c\ub144\uc544'):
                self.advance(); return BoolLiteral(True)
            if t.value == '\uc2dc\ubc1c\ub828':
                self.advance(); return BoolLiteral(False)
        raise ParseError(f'line ~{t.pos}: expected value, got {t.type}({t.value})')


# ─── Interpreter ─────────────────────────────────────────────────────────────

class InterpreterError(Exception):
    pass

class Interpreter:
    def __init__(self):
        self.vars = {}

    def eval(self, expr):
        if isinstance(expr, NumberLiteral): return expr.value
        if isinstance(expr, VarRef):
            if expr.name not in self.vars:
                raise InterpreterError(f'var {expr.name} not declared')
            return self.vars[expr.name]
        if isinstance(expr, BoolLiteral): return expr.value
        if isinstance(expr, BinaryOp):
            l = self.eval(expr.left); r = self.eval(expr.right)
            if expr.op == '>': return l > r
            if expr.op == '<': return l < r
            if expr.op == '>=': return l >= r
            if expr.op == '<=': return l <= r
            if expr.op == '==': return l == r
            if expr.op == '!=': return l != r
            raise InterpreterError(f'unknown op: {expr.op}')
        raise InterpreterError(f'unknown expr: {type(expr).__name__}')

    def exec(self, stmt):
        if isinstance(stmt, DeclareStmt):
            if stmt.var_name in self.vars:
                raise InterpreterError(f'var {stmt.var_name} already declared')
            self.vars[stmt.var_name] = 0

        elif isinstance(stmt, AssignStmt):
            if stmt.var_name not in self.vars:
                raise InterpreterError(f'var {stmt.var_name} not declared')
            if stmt.value_expr is None:
                try:
                    self.vars[stmt.var_name] = int(input())
                except (EOFError, ValueError):
                    self.vars[stmt.var_name] = 0
            else:
                self.vars[stmt.var_name] = self.eval(stmt.value_expr)

        elif isinstance(stmt, IncStmt):
            if stmt.var_name not in self.vars:
                raise InterpreterError(f'var {stmt.var_name} not declared')
            self.vars[stmt.var_name] += 1

        elif isinstance(stmt, NotStmt):
            if stmt.var_name not in self.vars:
                raise InterpreterError(f'var {stmt.var_name} not declared')
            self.vars[stmt.var_name] = not self.vars[stmt.var_name]

        elif isinstance(stmt, FreeStmt):
            self.vars.pop(stmt.var_name, None)

        elif isinstance(stmt, PanicStmt):
            v = self.vars.get(stmt.var_name, '<unknown>')
            raise InterpreterError(f'Panic! var {stmt.var_name} = {v}')

        elif isinstance(stmt, IfStmt):
            if self.eval(stmt.condition):
                self.exec_all(stmt.body)
            elif stmt.else_body:
                self.exec_all(stmt.else_body)

        elif isinstance(stmt, WhileStmt):
            while self.eval(stmt.condition):
                self.exec_all(stmt.body)

    def exec_all(self, stmts):
        for s in stmts:
            self.exec(s)

    def run(self, code):
        lines = code.split('\n')
        found_start = False
        found_end = False
        body = []

        for line in lines:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            if not found_start:
                if s == _START:
                    found_start = True
                continue
            if s == _END:
                found_end = True
                break
            body.append(line)

        if not found_start:
            raise InterpreterError('missing start marker')
        if not found_end:
            raise InterpreterError('missing end marker')

        src = '\n'.join(body)
        tokens = tokenize(src)
        prog = Parser(tokens).parse()
        self.exec_all(prog.statements)


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m jjitlang <file.jjit>')
        sys.exit(1)

    with open(sys.argv[1], encoding='utf-8') as f:
        code = f.read()

    try:
        Interpreter().run(code)
    except InterpreterError as e:
        print(f'\uc624\ub958: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
