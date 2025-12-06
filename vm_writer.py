class VMWriter:
    SEGMENT_MAP = {
        'CONST': 'constant',
        'ARG': 'argument',
        'VAR': 'local',
        'STATIC': 'static',
        'FIELD': 'this',
        'THAT': 'that',
        'POINTER': 'pointer',
        'TEMP': 'temp'
    }

    def __init__(self, output_file):
        self.output = open(output_file, 'w')

    def write_push(self, segment, index):
        """push segment index"""
        segment = self.SEGMENT_MAP.get(segment, segment)
        self.output.write(f"push {segment} {index}\n")

    def write_pop(self, segment, index):
        """pop segment index"""
        segment = self.SEGMENT_MAP.get(segment, segment)
        self.output.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command):
        """Арифметична/логічна команда"""
        self.output.write(f"{command}\n")

    def write_label(self, label):
        """label"""
        self.output.write(f"label {label}\n")

    def write_goto(self, label):
        """goto"""
        self.output.write(f"goto {label}\n")

    def write_if(self, label):
        """if-goto"""
        self.output.write(f"if-goto {label}\n")

    def write_call(self, name, n_args):
        """call name nArgs"""
        self.output.write(f"call {name} {n_args}\n")

    def write_function(self, name, n_vars):
        """function name nVars"""
        self.output.write(f"function {name} {n_vars}\n")

    def write_return(self):
        """return"""
        self.output.write("return\n")

    def close(self):
        self.output.close()