import subprocess
import tempfile
import os
import sys


class SubprocessRunner:

    @staticmethod
    def _set_limits():
        return

    @staticmethod
    def execute(code: str, stdin_input: str = "") -> str:

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:

            f.write(code)
            f.flush()
            fname = f.name

        try:

            print("RUNNER STDIN:", repr(stdin_input))
            process = subprocess.run(
                [sys.executable, fname],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=3
            )

            output = process.stdout + process.stderr

            return output.strip()

        except subprocess.TimeoutExpired:

            return "ERROR: Execution timed out"

        finally:

            os.unlink(fname)