import json
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
    compare_output_as_json: bool = False

    cc_optimization_arg: str = ""

    optimization_mode_arg: str = ""
    support_optimization_mode: bool = True

    def __post_init__(self) -> None:
        if not self.langs:
            self.langs = ["c", "go", "py"]
        self.cc_optimization_arg = os.environ.get("BP_TEST_CC_OPTIMIZATION", "")
        self.optimization_mode_arg = os.environ.get("BP_TEST_OPTIMIZATION_ARG", "")

    @property
    def rootdir(self) -> str:
        """Returns the rootdir of this test case."""
        return os.path.join(os.path.dirname(__file__), "encoding-cases", self.name)

    def execute_cmd_run(self, lang: str) -> bytes:
        """Execute makefile command `run` for given lang.
        Returns output.
        """
        sub_cmd = self.cmd_run_fmt.format(lang=lang)
        cmd = f"make -s  --no-print-directory {sub_cmd}"
        if lang in {"c", "cpp"} and self.cc_optimization_arg != "":
            cmd += " CC_OPTIMIZATION_ARG=" + self.cc_optimization_arg
        if self.optimization_mode_arg:
            cmd += " OPTIMIZATION_MODE_ARGS=" + self.optimization_mode_arg
        return subprocess.check_output(cmd, shell=True)

    def execute_cmd_clean(self) -> None:
        cmd = f"make -s  --no-print-directory {self.cmd_clean}"
        subprocess.check_call(cmd, shell=True)

    def compare_outputs(self, outputs: List[bytes]) -> None:
        """Compares if given outputs are the same.
        Raises AssertionError if not.
        """
        for out in outputs:
            if not self.compare_output_as_json:
                assert out.strip() == outputs[0].strip()
            else:
                assert json.loads(out.strip()) == json.loads(outputs[0].strip())

    def run(self) -> None:
        """Run this case, returns the"""

        if self.optimization_mode_arg and not self.support_optimization_mode:
            return

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
    _TestCase("drone", langs=["c", "cpp", "go", "py"]).run()


def test_encoding_drone_json() -> None:
    _TestCase(
        "drone_json", compare_output_as_json=True, support_optimization_mode=False
    ).run()


def test_encoding_extensible() -> None:
    _TestCase("extensible", support_optimization_mode=False).run()


def test_encoding_empty() -> None:
    _TestCase("empty", support_optimization_mode=False).run()


def test_encoding_consts() -> None:
    _TestCase("consts").run()


def test_encoding_nested() -> None:
    _TestCase("nested").run()


def test_encoding_arrays() -> None:
    _TestCase("arrays").run()


def test_encoding_scatter() -> None:
    _TestCase("scatter").run()


def test_encoding_enums() -> None:
    _TestCase("enums").run()


def test_encoding_signed() -> None:
    _TestCase("signed").run()


def test_encoding_complexx() -> None:
    _TestCase("complexx", support_optimization_mode=False).run()


def test_encoding_issue52() -> None:
    _TestCase(
        "issue-52",
        langs=["py", "c"],
        compare_output=False,
        compare_output_as_json=False,
        support_optimization_mode=False,
    )
