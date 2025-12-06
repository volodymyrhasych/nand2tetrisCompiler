import os
import sys
from jack_tokenizer import JackTokenizer
from compilation_engine import CompilationEngine
from vm_writer import VMWriter


class JackCompiler:
    def __init__(self, input_path):
        self.input_path = os.path.abspath(input_path)
        self.files = self._find_all_jack_files()

        if not self.files:
            raise ValueError(f"No .jack files found in {input_path}")

    def _find_all_jack_files(self):
        """Find ALL .jack files recursively"""
        jack_files = []

        if os.path.isfile(self.input_path):
            if self.input_path.endswith('.jack'):
                return [self.input_path]
            else:
                raise ValueError("Input must be a .jack file or directory")

        # Directory - find all .jack files
        for root, dirs, files in os.walk(self.input_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in sorted(files):  # Sort for consistency
                if file.endswith('.jack'):
                    full_path = os.path.join(root, file)
                    jack_files.append(full_path)

        return sorted(jack_files)  # Sort for consistent compilation order

    def compile(self):
        """Compile all .jack files"""
        print(f"🔧 Jack Compiler - compiling {len(self.files)} file(s)")

        success_count = 0
        for jack_file in self.files:
            try:
                self._compile_single_file(jack_file)
                success_count += 1
            except Exception as e:
                print(f"   ❌ Failed to compile {os.path.basename(jack_file)}: {e}")
                raise

        print(f"\n✅ Successfully compiled {success_count}/{len(self.files)} files")

    def _compile_single_file(self, jack_file):
        """Compile a single .jack file to .vm"""
        filename = os.path.basename(jack_file)
        print(f"   📄 Compiling {filename}...", end="", flush=True)

        # Create output filename
        base_name = os.path.splitext(jack_file)[0]
        vm_file = base_name + '.vm'

        # Initialize components
        tokenizer = JackTokenizer(jack_file)
        vm_writer = VMWriter(vm_file)
        compiler = CompilationEngine(tokenizer, vm_writer)

        # Compile
        compiler.compile_class()
        vm_writer.close()

        print(f" ✅ -> {os.path.basename(vm_file)}")


def main():
    """Main entry point for the Jack compiler"""
    if len(sys.argv) != 2:
        print("Jack Compiler - Nand2Tetris Project 12")
        print("Usage: python JackCompiler.py <input.jack or directory>")
        print("\nExamples:")
        print("  python JackCompiler.py Main.jack")
        print("  python JackCompiler.py projects/12/Square/")
        print("\nTest directories:")
        print("  projects/12/Seven/          - Simple test (one file)")
        print("  projects/12/ConvertToBin/   - No Sys.jack")
        print("  projects/12/Square/         - With Sys.jack")
        print("  projects/12/Average/        - With Sys.jack")
        print("  projects/12/ComplexArrays/  - Complex test")
        sys.exit(1)

    try:
        compiler = JackCompiler(sys.argv[1])
        compiler.compile()
    except Exception as e:
        print(f"\n❌ Compilation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()