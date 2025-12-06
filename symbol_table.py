class SymbolTable:
    def __init__(self):
        self.class_table = {}
        self.subroutine_table = {}
        self.counts = {
            'static': 0,
            'field': 0,
            'arg': 0,
            'var': 0
        }

    def start_subroutine(self):
        """Очистити таблицю підпрограми"""
        self.subroutine_table.clear()
        self.counts['arg'] = 0
        self.counts['var'] = 0

    def define(self, name, type, kind):
        """Додати нову змінну"""
        if kind in ('static', 'field'):
            self.class_table[name] = {
                'type': type,
                'kind': kind,
                'index': self.counts[kind]
            }
        else:  # arg, var
            self.subroutine_table[name] = {
                'type': type,
                'kind': kind,
                'index': self.counts[kind]
            }
        self.counts[kind] += 1

    def var_count(self, kind):
        """Кількість змінних даного виду"""
        return self.counts[kind]

    def kind_of(self, name):
        """Повернути вид змінної (STATIC, FIELD, ARG, VAR або NONE)"""
        if name in self.subroutine_table:
            return self.subroutine_table[name]['kind'].upper()
        elif name in self.class_table:
            return self.class_table[name]['kind'].upper()
        return 'NONE'

    def type_of(self, name):
        """Повернути тип змінної"""
        if name in self.subroutine_table:
            return self.subroutine_table[name]['type']
        elif name in self.class_table:
            return self.class_table[name]['type']
        return None

    def index_of(self, name):
        """Повернути індекс змінної"""
        if name in self.subroutine_table:
            return self.subroutine_table[name]['index']
        elif name in self.class_table:
            return self.class_table[name]['index']
        return -1