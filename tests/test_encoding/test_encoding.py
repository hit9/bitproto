import os
import subprocess
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional


@dataclass
class _TestCase:
    """_TestCase is a test case descriptor."""

    # Name of this test case.
    name: str

    # Languages to use in this case, defaults to ["c", "go", "py"]
    langs: List[str] = field(default_factory=list)

    # Command `run` formatter, defaults to "run-{lang}"
    cmd_run_fmt: str = "run-{lang}"

    # Command `clean`, defaults to "clean"
    cmd_clean: str = "clean"

    # Whether to compare output of command run.
    compare_output: bool = True

    def __post_init__(self) -> None:
        if not self.langs:
            self.langs = ["c", "go", "py"]

    @property
    def rootdir(self) -> str:
        """Returns the rootdir of this test case."""
        return os.path.join(os.path.dirname(__file__), "encoding-cases", self.name)

    def execute_cmd_run(self, lang: str) -> bytes:
        """Execute makefile command `run` for given lang.
        Returns output.
        """
        sub_cmd = self.cmd_run_fmt.format(lang=lang)
        cmd = f"make {sub_cmd}"
        return subprocess.check_output(cmd, shell=True)

    def execute_cmd_clean(self) -> None:
        cmd = f"make {self.cmd_clean}"
        subprocess.check_call(cmd, shell=True)

    def compare_outputs(self, outputs: List[bytes]) -> None:
        """Compares if given outputs are the same.
        Raises AssertionError if not.
        """
        for out in outputs:
            assert out.strip() == outputs[0].strip()

    def run(self) -> None:
        """Run this case, returns the """
        current_cwd = os.getcwd()
        outputs: List[bytes] = []

        try:
            os.chdir(self.rootdir)

            for lang in self.langs:
                out = self.execute_cmd_run(lang)
                outputs.append(out)

            if self.compare_output:
                self.compare_outputs(outputs)

        finally:
            self.execute_cmd_clean()
            os.chdir(current_cwd)


def test_encoding_drone() -> None:
    _TestCase("drone").run()
