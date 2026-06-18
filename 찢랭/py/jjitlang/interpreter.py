import sys


_KEYWORDS = {
    '형수': 'DECLARE',
    '새끼': 'TYPE',
    '찢': 'ASSIGN',
    '놈': 'INPUT',
    '미친년': 'IF',
    '병신': 'ELSE',
    '지가 나온 구멍': 'WHILE',
    '씨발년': 'TRUE',
    '씨발년아': 'TRUE',
    '시발련': 'FALSE',
    '시팔련': 'NOT',
    '개새끼': 'FREE',
    '칼로 쑤신다': 'INC',
    '이 인간 쓰.레.기.야': 'PANIC',
}

_START = '야, 이 씨발련아'
_END = '니 친정 엄마, 씹구멍 찢으면 좋겠니'


class Token:
    def __init__(self, typ, value=None):
        self.type = typ
        self.value = value
    def __repr__(self):
        return f'T({self.type},{self.value!r})'


class InterpreterError(Exception):
    pass


def is_comment(stripped):
    return stripped.startswith('#') or stripped.startswith('//')


class Interpreter:
    def __init__(self):
        self.vars = {}

    def get_indent(self, line):
        return len(line) - len(line.lstrip())

    def strip_min_indent(self, lines):
        if not lines:
            return []
        indents = [self.get_indent(l) for l in lines]
        min_i = min(indents)
        return [l[min_i:] for l in lines]

    def tokenize_line(self, text):
        tokens = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == ' ' or ch == '\t':
                i += 1
                continue
            if ch == ',':
                tokens.append(Token('COMMA'))
                i += 1
                continue
            if ch == '.':
                tokens.append(Token('DOT'))
                i += 1
                continue
            if ch in '><=!':
                if i + 1 < len(text) and text[i:i+2] in ('>=', '<=', '==', '!='):
                    tokens.append(Token('OPERATOR', text[i:i+2]))
                    i += 2
                    continue
                if ch in '><':
                    tokens.append(Token('OPERATOR', ch))
                    i += 1
                    continue
                i += 1
                continue
            if ch.isdigit():
                start = i
                i += 1
                while i < len(text) and text[i].isdigit():
                    i += 1
                tokens.append(Token('NUMBER', int(text[start:i])))
                continue
            matched = False
            for kw in sorted(_KEYWORDS.keys(), key=len, reverse=True):
                if i + len(kw) <= len(text) and text[i:i+len(kw)] == kw:
                    tokens.append(Token('KEYWORD', kw))
                    i += len(kw)
                    matched = True
                    break
            if not matched:
                i += 1
        return tokens

    def eval_val(self, raw):
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, int):
            return raw
        s = str(raw)
        if s in self.vars:
            return self.vars[s]
        try:
            return int(s)
        except ValueError:
            return 0

    def eval_cond(self, cond_tokens):
        vals = []
        for t in cond_tokens:
            if t.type == 'NUMBER':
                vals.append(str(t.value))
            elif t.type == 'OPERATOR':
                vals.append(t.value)
            elif t.type == 'KEYWORD':
                if t.value in ('씨발년', '씨발년아'):
                    vals.append('1')
                elif t.value == '시발련':
                    vals.append('0')
        if len(vals) == 1:
            return bool(self.eval_val(vals[0]))
        if len(vals) == 3:
            left = self.eval_val(vals[0])
            op = vals[1]
            right = self.eval_val(vals[2])
            if op == '>': return left > right
            if op == '<': return left < right
            if op == '>=': return left >= right
            if op == '<=': return left <= right
            if op == '==': return left == right
            if op == '!=': return left != right
        return False

    def run(self, code):
        raw_lines = code.split('\n')
        found_start = False
        found_end = False
        body_lines = []
        for line in raw_lines:
            stripped = line.strip()
            if not stripped or is_comment(stripped):
                continue
            if not found_start:
                if stripped == _START:
                    found_start = True
                continue
            if stripped == _END:
                found_end = True
                break
            body_lines.append(line)
        if not found_start:
            raise InterpreterError('시작 마커가 없음: ' + _START)
        if not found_end:
            raise InterpreterError('종료 마커가 없음: ' + _END)
        self.exec_block(body_lines, 0)

    def exec_block(self, lines, base_indent):
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped or is_comment(stripped):
                i += 1
                continue
            indent = self.get_indent(line)
            if indent < base_indent:
                break
            if indent > base_indent:
                i += 1
                continue

            tokens = self.tokenize_line(stripped)
            if not tokens:
                i += 1
                continue

            if tokens[0].type == 'KEYWORD':
                kw = tokens[0].value
                if kw == '형수':
                    self._declare(tokens)

                elif kw == '미친년':
                    cond_tokens = self._extract_cond([t for t in tokens[1:] if t.type not in ('COMMA', 'DOT')])
                    body = []
                    i += 1
                    has_else = False
                    else_body = []
                    while i < len(lines):
                        nstripped = lines[i].strip()
                        nindent = self.get_indent(lines[i])
                        if not nstripped or is_comment(nstripped):
                            i += 1
                            continue
                        if nindent <= indent:
                            break
                        if nstripped == '병신':
                            has_else = True
                            i += 1
                            while i < len(lines):
                                enindent = self.get_indent(lines[i])
                                enstripped = lines[i].strip()
                                if not enstripped or is_comment(enstripped):
                                    i += 1
                                    continue
                                if enindent <= indent:
                                    break
                                else_body.append(lines[i])
                                i += 1
                            break
                        body.append(lines[i])
                        i += 1
                    if self.eval_cond(cond_tokens):
                        self.exec_block(self.strip_min_indent(body), 0)
                    elif has_else:
                        self.exec_block(self.strip_min_indent(else_body), 0)
                    continue

                elif kw == '지가 나온 구멍':
                    cond_tokens = self._extract_cond([t for t in tokens[1:] if t.type not in ('COMMA', 'DOT')])
                    body = []
                    i += 1
                    while i < len(lines):
                        nindent = self.get_indent(lines[i])
                        nstripped = lines[i].strip()
                        if not nstripped or is_comment(nstripped):
                            i += 1
                            continue
                        if nindent <= indent:
                            break
                        body.append(lines[i])
                        i += 1
                    while self.eval_cond(cond_tokens):
                        self.exec_block(self.strip_min_indent(body), 0)
                    continue

                else:
                    self._op(tokens)

            elif tokens[0].type == 'NUMBER':
                self._op(tokens)

            i += 1

    def _extract_cond(self, tokens):
        result = []
        for t in tokens:
            if t.type in ('COMMA', 'DOT'):
                continue
            if t.type == 'NUMBER':
                result.append(t)
            elif t.type == 'OPERATOR':
                result.append(t)
            elif t.type == 'KEYWORD':
                if t.value in ('씨발년', '씨발년아', '시발련'):
                    result.append(t)
                else:
                    break
            else:
                break
        return result

    def _declare(self, tokens):
        nums = [t for t in tokens if t.type == 'NUMBER']
        if not nums:
            raise InterpreterError('형수: 변수명 없음')
        for n in nums:
            self.vars[str(n.value)] = 0

    def _op(self, tokens):
        nums = [t for t in tokens if t.type == 'NUMBER']
        if not nums:
            return
        var_name = str(nums[0].value)
        kws = [t for t in tokens if t.type == 'KEYWORD']
        if not kws:
            return
        kw = kws[0].value

        if kw == '찢':
            if var_name not in self.vars:
                raise InterpreterError(f'변수 {var_name} 선언 안됨')
            rest = [t for t in tokens[1:] if t.type not in ('COMMA', 'DOT') and not (t.type == 'KEYWORD' and t.value == '찢')]
            if not rest:
                return
            rt = rest[0]
            if rt.type == 'NUMBER':
                self.vars[var_name] = rt.value
            elif rt.type == 'KEYWORD':
                if rt.value in ('씨발년', '씨발년아'):
                    self.vars[var_name] = 1
                elif rt.value == '시발련':
                    self.vars[var_name] = 0
                elif rt.value == '놈':
                    try:
                        self.vars[var_name] = int(input())
                    except (EOFError, ValueError):
                        self.vars[var_name] = 0

        elif kw == '칼로 쑤신다':
            if var_name not in self.vars:
                raise InterpreterError(f'변수 {var_name} 선언 안됨')
            self.vars[var_name] += 1
            print(self.vars[var_name])

        elif kw == '시팔련':
            if var_name not in self.vars:
                raise InterpreterError(f'변수 {var_name} 선언 안됨')
            self.vars[var_name] = not self.vars[var_name]

        elif kw == '개새끼':
            self.vars.pop(var_name, None)

        elif kw == '이 인간 쓰.레.기.야':
            v = self.vars.get(var_name, '?')
            raise InterpreterError(f'Panic! 변수 {var_name} = {v}')


def main():
    if len(sys.argv) < 2:
        print('python -m jjitlang <file.jjit>')
        sys.exit(1)
    with open(sys.argv[1], encoding='utf-8') as f:
        code = f.read()
    try:
        Interpreter().run(code)
    except InterpreterError as e:
        print(f'오류: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
