#!/usr/bin/env python3

import sys
import os

# Додаємо поточну директорію до Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# ІМПОРТИ (адаптуйте до назв ваших файлів!)
try:
    # Варіант 1: якщо файли з великими літерами
    from SymbolTable import SymbolTable
    from VMWriter import VMWriter
except ImportError:
    try:
        # Варіант 2: якщо файли з маленькими літерами
        from symbol_table import SymbolTable
        from vm_writer import VMWriter
    except ImportError as e:
        print(f"❌ Помилка імпорту: {e}")
        print("Перевірте назви файлів:")
        print("  SymbolTable.py або symbol_table.py")
        print("  VMWriter.py або vm_writer.py")
        raise


class CompilationEngine:
    def __init__(self, tokenizer, vm_writer):
        self.tokenizer = tokenizer
        self.vm_writer = vm_writer
        self.symbol_table = SymbolTable()  # ✅ Тепер працюватиме!
        self.class_name = ""
        self.label_counter = 0

        # Operators mapping
        self.OPERATORS = {
            '+': 'add',
            '-': 'sub',
            '*': 'Math.multiply',
            '/': 'Math.divide',
            '&': 'and',
            '|': 'or',
            '<': 'lt',
            '>': 'gt',
            '=': 'eq'
        }

    def compile_class(self):
        """'class' className '{' classVarDec* subroutineDec* '}'"""
        self._eat('keyword', 'class')
        self.class_name = self._eat('identifier')
        self._eat('symbol', '{')

        # Compile class variables
        while self.tokenizer.peek() and self.tokenizer.peek()[1] in ('static', 'field'):
            self.compile_class_var_dec()

        # Compile subroutines
        while self.tokenizer.peek() and self.tokenizer.peek()[1] in ('constructor', 'function', 'method'):
            self.compile_subroutine_dec()

        self._eat('symbol', '}')

    def compile_class_var_dec(self):
        """('static' | 'field') type varName (',' varName)* ';'"""
        kind = self._eat('keyword')  # static or field
        var_type = self._eat_type()
        var_name = self._eat('identifier')

        self.symbol_table.define(var_name, var_type, kind)

        while self.tokenizer.peek() and self.tokenizer.peek()[1] == ',':
            self._eat('symbol', ',')
            var_name = self._eat('identifier')
            self.symbol_table.define(var_name, var_type, kind)

        self._eat('symbol', ';')

    def compile_subroutine_dec(self):
        """('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody"""
        self.symbol_table.start_subroutine()

        subroutine_type = self._eat('keyword')  # constructor, function, method
        return_type = self._eat_type() if self.tokenizer.peek()[1] != 'void' else self._eat('keyword', 'void')
        subroutine_name = self._eat('identifier')

        # For methods: 'this' is first argument
        if subroutine_type == 'method':
            self.symbol_table.define('this', self.class_name, 'arg')

        self._eat('symbol', '(')
        self.compile_parameter_list()
        self._eat('symbol', ')')

        # Compile body
        self.compile_subroutine_body(subroutine_type, f"{self.class_name}.{subroutine_name}")

    def compile_subroutine_body(self, subroutine_type, full_name):
        """'{' varDec* statements '}'"""
        self._eat('symbol', '{')

        # Local variables
        while self.tokenizer.peek() and self.tokenizer.peek()[1] == 'var':
            self.compile_var_dec()

        # Number of local variables
        n_locals = self.symbol_table.var_count('var')
        self.vm_writer.write_function(full_name, n_locals)

        # For constructors: allocate memory
        if subroutine_type == 'constructor':
            n_fields = self.symbol_table.var_count('field')
            self.vm_writer.write_push('constant', n_fields)
            self.vm_writer.write_call('Memory.alloc', 1)
            self.vm_writer.write_pop('pointer', 0)  # THIS = new object

        # For methods: setup THIS
        elif subroutine_type == 'method':
            self.vm_writer.write_push('argument', 0)  # first arg = object
            self.vm_writer.write_pop('pointer', 0)  # THIS = object

        # Compile statements
        self.compile_statements()
        self._eat('symbol', '}')

    def compile_parameter_list(self):
        """((type varName) (',' type varName)*)?"""
        if self.tokenizer.peek() and self.tokenizer.peek()[1] != ')':
            param_type = self._eat_type()
            param_name = self._eat('identifier')
            self.symbol_table.define(param_name, param_type, 'arg')

            while self.tokenizer.peek() and self.tokenizer.peek()[1] == ',':
                self._eat('symbol', ',')
                param_type = self._eat_type()
                param_name = self._eat('identifier')
                self.symbol_table.define(param_name, param_type, 'arg')

    def compile_var_dec(self):
        """'var' type varName (',' varName)* ';'"""
        self._eat('keyword', 'var')
        var_type = self._eat_type()
        var_name = self._eat('identifier')

        self.symbol_table.define(var_name, var_type, 'var')

        while self.tokenizer.peek() and self.tokenizer.peek()[1] == ',':
            self._eat('symbol', ',')
            var_name = self._eat('identifier')
            self.symbol_table.define(var_name, var_type, 'var')

        self._eat('symbol', ';')

    def compile_statements(self):
        """statement*"""
        while self.tokenizer.peek() and self.tokenizer.peek()[1] in ('let', 'if', 'while', 'do', 'return'):
            token = self.tokenizer.peek()[1]
            if token == 'let':
                self.compile_let()
            elif token == 'if':
                self.compile_if()
            elif token == 'while':
                self.compile_while()
            elif token == 'do':
                self.compile_do()
            elif token == 'return':
                self.compile_return()

    def compile_let(self):
        """'let' varName ('[' expression ']')? '=' expression ';'"""
        self._eat('keyword', 'let')
        var_name = self._eat('identifier')

        # Array access: let array[index] = expression
        is_array = False
        if self.tokenizer.peek() and self.tokenizer.peek()[1] == '[':
            is_array = True
            self._eat('symbol', '[')
            self.compile_expression()  # index
            self._eat('symbol', ']')

            # Calculate address: array + index
            self._push_var(var_name)
            self.vm_writer.write_arithmetic('add')

            # ✅ ВИПРАВЛЕННЯ: зберегти адресу у temp[1] для вкладених масивів
            self.vm_writer.write_pop('temp', 1)  # temp[1] = array + index

        self._eat('symbol', '=')
        self.compile_expression()  # value to assign
        self._eat('symbol', ';')

        # Assign value
        if is_array:
            # ✅ ВИПРАВЛЕННЯ: відновити адресу з temp[1] та встановити THAT
            self.vm_writer.write_push('temp', 1)
            self.vm_writer.write_pop('pointer', 1)  # THAT = array + index
            self.vm_writer.write_pop('that', 0)  # array[index] = value
        else:
            self._pop_var(var_name)  # varName = value

    def compile_if(self):
        """'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?"""
        self._eat('keyword', 'if')

        label_true = self._new_label("IF_TRUE")
        label_false = self._new_label("IF_FALSE")
        label_end = self._new_label("IF_END")

        self._eat('symbol', '(')
        self.compile_expression()  # condition
        self._eat('symbol', ')')

        # In Jack: if (condition) executes if condition = true
        self.vm_writer.write_arithmetic('not')
        self.vm_writer.write_if(label_false)

        self.vm_writer.write_label(label_true)
        self._eat('symbol', '{')
        self.compile_statements()  # if body
        self._eat('symbol', '}')

        # Handle else
        if self.tokenizer.peek() and self.tokenizer.peek()[1] == 'else':
            self.vm_writer.write_goto(label_end)
            self.vm_writer.write_label(label_false)

            self._eat('keyword', 'else')
            self._eat('symbol', '{')
            self.compile_statements()  # else body
            self._eat('symbol', '}')

            self.vm_writer.write_label(label_end)
        else:
            self.vm_writer.write_label(label_false)

    def compile_while(self):
        """'while' '(' expression ')' '{' statements '}'"""
        self._eat('keyword', 'while')

        label_start = self._new_label("WHILE_START")
        label_end = self._new_label("WHILE_END")

        self.vm_writer.write_label(label_start)

        self._eat('symbol', '(')
        self.compile_expression()  # condition
        self._eat('symbol', ')')

        self.vm_writer.write_arithmetic('not')
        self.vm_writer.write_if(label_end)

        self._eat('symbol', '{')
        self.compile_statements()  # loop body
        self._eat('symbol', '}')

        self.vm_writer.write_goto(label_start)
        self.vm_writer.write_label(label_end)

    def compile_do(self):
        """'do' subroutineCall ';'"""
        self._eat('keyword', 'do')
        self.compile_subroutine_call()
        self._eat('symbol', ';')

        # Discard return value (void methods)
        self.vm_writer.write_pop('temp', 0)

    def compile_return(self):
        """'return' expression? ';'"""
        self._eat('keyword', 'return')

        if self.tokenizer.peek() and self.tokenizer.peek()[1] != ';':
            self.compile_expression()  # return value
        else:
            # void method: return 0
            self.vm_writer.write_push('constant', 0)

        self._eat('symbol', ';')
        self.vm_writer.write_return()

    def compile_expression(self):
        """term (op term)*"""
        self.compile_term()

        while self.tokenizer.peek() and self.tokenizer.peek()[1] in self.OPERATORS:
            op = self._eat('symbol')
            self.compile_term()

            if op in ('+', '-', '&', '|', '<', '>', '='):
                self.vm_writer.write_arithmetic(self.OPERATORS[op])
            elif op == '*':
                self.vm_writer.write_call('Math.multiply', 2)
            elif op == '/':
                self.vm_writer.write_call('Math.divide', 2)

    def compile_term(self):
        """integerConstant | stringConstant | keywordConstant |
           varName | varName '[' expression ']' | subroutineCall |
           '(' expression ')' | unaryOp term"""
        token_type, token_value = self.tokenizer.peek()

        # 1. Integer constant
        if token_type == 'integerConstant':
            self._eat('integerConstant')
            self.vm_writer.write_push('constant', int(token_value))

        # 2. String constant
        elif token_type == 'stringConstant':
            self._eat('stringConstant')
            self._compile_string(token_value)

        # 3. Keywords: true, false, null, this
        elif token_type == 'keyword' and token_value in ('true', 'false', 'null', 'this'):
            keyword = self._eat('keyword')
            if keyword == 'true':
                self.vm_writer.write_push('constant', 1)
                self.vm_writer.write_arithmetic('neg')  # true = -1 in Jack
            elif keyword in ('false', 'null'):
                self.vm_writer.write_push('constant', 0)
            elif keyword == 'this':
                self.vm_writer.write_push('pointer', 0)  # current object

        # 4. Unary operators: - or ~
        elif token_type == 'symbol' and token_value in ('-', '~'):
            op = self._eat('symbol')
            self.compile_term()
            self.vm_writer.write_arithmetic('neg' if op == '-' else 'not')

        # 5. Parentheses: (expression)
        elif token_type == 'symbol' and token_value == '(':
            self._eat('symbol', '(')
            self.compile_expression()
            self._eat('symbol', ')')

        # 6. Identifier (variable, array, subroutine call)
        elif token_type == 'identifier':
            # Check next token to determine type
            next_token = self.tokenizer.peek_next()

            # 6a. Subroutine call: name(...) or name.method(...)
            if next_token and next_token[1] in ('(', '.'):
                self.compile_subroutine_call()

            # 6b. Array access: varName[expression]
            elif next_token and next_token[1] == '[':
                var_name = self._eat('identifier')
                self._eat('symbol', '[')
                self.compile_expression()  # index
                self._eat('symbol', ']')

                # ✅ ВИПРАВЛЕННЯ: правильна обробка вкладених масивів
                # Calculate address: array + index
                self._push_var(var_name)
                self.vm_writer.write_arithmetic('add')

                # Зберегти адресу у temp[0] (для вкладених викликів)
                self.vm_writer.write_pop('temp', 0)  # temp[0] = array + index

                # Відновити адресу та встановити THAT
                self.vm_writer.write_push('temp', 0)
                self.vm_writer.write_pop('pointer', 1)  # THAT = array + index
                self.vm_writer.write_push('that', 0)  # value array[index]

            # 6c. Simple variable
            else:
                var_name = self._eat('identifier')
                self._push_var(var_name)

        else:
            raise SyntaxError(f"Invalid term: {token_type} {token_value}")

    def compile_subroutine_call(self):
        """CRITICAL: Handle Main.main() calls from Sys.jack"""
        # Store first name part
        first_name = self._eat('identifier')
        n_args = 0

        # Check if it's Class.method() or obj.method()
        if self.tokenizer.peek() and self.tokenizer.peek()[1] == '.':
            self._eat('symbol', '.')
            subroutine_name = self._eat('identifier')

            # Check if first_name is a variable (object)
            kind = self.symbol_table.kind_of(first_name)

            if kind != 'NONE':
                # It's obj.method(...) - pass object as first arg
                self._push_var(first_name)
                n_args = 1
                class_name = self.symbol_table.type_of(first_name)
                full_name = f"{class_name}.{subroutine_name}"
            else:
                # It's Class.method(...) - static call
                full_name = f"{first_name}.{subroutine_name}"
                # STATIC CALL: 0 arguments (NOT THIS!)
                # Important: For Main.main() called from Sys.jack
                # This should be call Main.main 0 (not 1)

        else:
            # It's method(...) in current class
            # Pass 'this' as first argument
            self.vm_writer.write_push('pointer', 0)  # this
            n_args = 1
            full_name = f"{self.class_name}.{first_name}"

        self._eat('symbol', '(')
        n_args += self.compile_expression_list()
        self._eat('symbol', ')')

        # Generate call
        self.vm_writer.write_call(full_name, n_args)

    def compile_expression_list(self):
        """(expression (',' expression)*)?"""
        count = 0

        if self.tokenizer.peek() and self.tokenizer.peek()[1] != ')':
            self.compile_expression()
            count = 1

            while self.tokenizer.peek() and self.tokenizer.peek()[1] == ',':
                self._eat('symbol', ',')
                self.compile_expression()
                count += 1

        return count

    def _compile_string(self, string):
        """Generate code for string constants"""
        length = len(string)
        self.vm_writer.write_push('constant', length)
        self.vm_writer.write_call('String.new', 1)

        for char in string:
            self.vm_writer.write_push('constant', ord(char))
            self.vm_writer.write_call('String.appendChar', 2)

    def _push_var(self, var_name):
        """Push variable value onto stack"""
        kind = self.symbol_table.kind_of(var_name)
        index = self.symbol_table.index_of(var_name)

        segment_map = {
            'STATIC': 'static',
            'FIELD': 'this',
            'ARG': 'argument',
            'VAR': 'local'
        }

        segment = segment_map.get(kind)
        if segment:
            self.vm_writer.write_push(segment, index)
        else:
            raise NameError(f"Unknown variable: {var_name}")

    def _pop_var(self, var_name):
        """Pop value from stack into variable"""
        kind = self.symbol_table.kind_of(var_name)
        index = self.symbol_table.index_of(var_name)

        segment_map = {
            'STATIC': 'static',
            'FIELD': 'this',
            'ARG': 'argument',
            'VAR': 'local'
        }

        segment = segment_map.get(kind)
        if segment:
            self.vm_writer.write_pop(segment, index)
        else:
            raise NameError(f"Unknown variable: {var_name}")

    def _eat(self, expected_type, expected_value=None):
        """Check and consume token"""
        if not self.tokenizer.has_more_tokens():
            raise EOFError("Unexpected end of file")

        self.tokenizer.advance()
        token_type, token_value = self.tokenizer.current_token

        if token_type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token_type}")

        if expected_value is not None and token_value != expected_value:
            raise SyntaxError(f"Expected '{expected_value}', got '{token_value}'")

        return token_value

    def _eat_type(self):
        """Eat type: 'int', 'char', 'boolean' or class identifier"""
        token_type, token_value = self.tokenizer.peek()

        if token_type == 'keyword' and token_value in ('int', 'char', 'boolean'):
            return self._eat('keyword')
        elif token_type == 'identifier':
            return self._eat('identifier')
        else:
            raise SyntaxError(f"Invalid type: {token_value}")

    def _new_label(self, base):
        """Create unique label"""
        self.label_counter += 1
        return f"{base}_{self.label_counter}"