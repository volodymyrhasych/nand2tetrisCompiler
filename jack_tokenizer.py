class JackTokenizer:
    KEYWORDS = {'class', 'constructor', 'function', 'method', 'field', 'static',
                'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null',
                'this', 'let', 'do', 'if', 'else', 'while', 'return'}

    SYMBOLS = {'{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/',
               '&', '|', '<', '>', '=', '~'}

    def __init__(self, input_file):
        """Open input file and tokenize it"""
        with open(input_file, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

        self.tokens = []
        self.current_token = None
        self.token_index = -1
        self._tokenize()

    def _tokenize(self):
        """Convert input file to tokens"""
        in_comment = False
        in_string = False
        current_string = ""

        for line in self.lines:
            line = line.strip()
            i = 0
            while i < len(line):
                # Skip comments
                if not in_comment and line[i:i + 2] == '//':
                    break  # Line comment, skip rest of line

                if not in_comment and line[i:i + 2] == '/*':
                    in_comment = True
                    i += 1
                elif in_comment and line[i:i + 2] == '*/':
                    in_comment = False
                    i += 1
                elif in_comment:
                    i += 1
                    continue

                # Handle string constants
                elif line[i] == '"' and not in_string:
                    in_string = True
                    current_string = ""
                elif line[i] == '"' and in_string:
                    in_string = False
                    self.tokens.append(('stringConstant', current_string))
                    current_string = ""
                elif in_string:
                    current_string += line[i]

                # Handle symbols
                elif line[i] in self.SYMBOLS:
                    self.tokens.append(('symbol', line[i]))

                # Handle numbers
                elif line[i].isdigit():
                    num = line[i]
                    while i + 1 < len(line) and line[i + 1].isdigit():
                        i += 1
                        num += line[i]
                    self.tokens.append(('integerConstant', num))

                # Handle identifiers/keywords
                elif line[i].isalpha() or line[i] == '_':
                    identifier = line[i]
                    while i + 1 < len(line) and (line[i + 1].isalnum() or line[i + 1] == '_'):
                        i += 1
                        identifier += line[i]

                    if identifier in self.KEYWORDS:
                        self.tokens.append(('keyword', identifier))
                    else:
                        self.tokens.append(('identifier', identifier))

                # Skip whitespace
                elif line[i] in ' \t':
                    pass
                else:
                    # Unexpected character
                    pass

                i += 1

    def has_more_tokens(self):
        """Are there more tokens?"""
        return self.token_index + 1 < len(self.tokens)

    def advance(self):
        """Get next token"""
        if self.has_more_tokens():
            self.token_index += 1
            self.current_token = self.tokens[self.token_index]
        return self.current_token

    def peek(self):
        """Look at next token without consuming it"""
        if self.token_index + 1 < len(self.tokens):
            return self.tokens[self.token_index + 1]
        return None

    def peek_next(self):
        """Look at token after next (for two-token lookahead)"""
        if self.token_index + 2 < len(self.tokens):
            return self.tokens[self.token_index + 2]
        return None

    def token_type(self):
        """Type of current token"""
        return self.current_token[0] if self.current_token else None

    def keyword(self):
        """Current keyword"""
        return self.current_token[1] if self.token_type() == 'keyword' else None

    def symbol(self):
        """Current symbol"""
        return self.current_token[1] if self.token_type() == 'symbol' else None

    def identifier(self):
        """Current identifier"""
        return self.current_token[1] if self.token_type() == 'identifier' else None

    def int_val(self):
        """Integer value of current token"""
        return int(self.current_token[1]) if self.token_type() == 'integerConstant' else None

    def string_val(self):
        """String value of current token"""
        return self.current_token[1] if self.token_type() == 'stringConstant' else None