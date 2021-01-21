import os
import subprocess
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional


@dataclass
class _TestCase:
    """_TestCase is the case runner wrapper."""

    # Name of this test case.
    name: str

    # Languages to use in this case, defaults to ["c", "go", "py"]
    langs: List[str] = field(default_factory=list)

    # Default working directory for each lang.
    # The workdir is a string path relative to the root directory of this case.
    # Defaults to {"c": "c", "go": "go", "py": ""}
    workdirs: Dict[str, str] = field(default_factory=dict)

    # Outdirs for bitproto generation, in format of dict: lang => outdir
    # The outdir is a string path relative to the workdir of this lang.
    # Defaults to {"c": "", "go": "bp", "py": ""}
    outdirs: Dict[str, str] = field(default_factory=dict)

    # List of bitproto's filename need to compile.
    # Defaults to ["{name}.bitproto"].
    bp_files: List[str] = field(default_factory=list)

    # Source files, in format of dict: lang => filename list.
    # Defaults to {"c": ["main.c"], "go": ["main.go"], "py": ["main.py"]}
    source_files: Dict[str, List[str]] = field(default_factory=dict)

    # Build filename, in format of dict: lang => filename list.
    # Defaults to {"c": "main", go: "main"}
    build_files: Dict[str, str] = field(default_factory=dict)

    # CC command to use for c, defaults to "CC".
    cc: str = "CC"

    # Defaults
    DEFAULT_LANGS: ClassVar[List[str]] = ["c", "go", "py"]
    DEFAULT_OUTDIRS: ClassVar[Dict[str, str]] = {"go": "bp"}
    DEFAULT_SOURCE_FILES: ClassVar[Dict[str, List[str]]] = {
        "c": ["main.c"],
        "go": ["main.go"],
        "py": ["main.py"],
    }
    DEFAULT_BUILD_FILES: ClassVar[Dict[str, str]] = {"c": "main", "go": "main"}

    def __post_init__(self) -> None:
        if not self.langs:
            self.langs = self.DEFAULT_LANGS

        for lang, outdir in self.DEFAULT_OUTDIRS.items():
            if lang in self.langs:
                self.outdirs.setdefault(lang, outdir)

        if not self.bp_files:
            self.bp_files = [f"{self.name}.bitproto"]

        for lang, source_files in self.DEFAULT_SOURCE_FILES.items():
            if lang in self.langs:
                self.source_files.setdefault(lang, source_files)

        for lang, build_file in self.DEFAULT_BUILD_FILES.items():
            if lang in self.langs:
                self.build_files.setdefault(lang, build_file)

    def log(self, s: str) -> None:
        print(s + "\n")

    def get_workdir(self, lang: str) -> str:
        """Returns the workdir for given language."""
        default_workdir = lang
        return self.workdirs.get(lang, default_workdir)

    def get_outdir(self, lang: str) -> str:
        """Returns the bitproto outdir relative to workdir for given language."""
        return self.outdirs.get(lang, "")

    def get_build_filename(self, lang: str) -> str:
        """Returns the build filename of given lang.
        Returns empty string if not exist.
        """
        return self.build_files.get(lang, "")

    def chdir(self) -> None:
        """Change working dir to current root dir."""
        rootdir = self.format_rootdir_path()
        os.chdir(rootdir)
        self.log("chdir => {rootdir}")

    def format_generated_bp_file(self, bp_filename: str, extension: str) -> str:
        """Formats the generated bp file for given source_filename and extension.

        {bp_filename_slug}_bp.{extension}
        """
        return bp_filename.rstrip(".bitproto") + "_bp" + extension

    def format_rootdir_path(self) -> str:
        """Format the abs path of the rootdir of this case."""
        return os.path.join(os.path.dirname(__file__), "encoding-cases", self.name)

    def format_bp_lib_dir_path(self) -> str:
        """Formats the relative path of the directory of bitproto lib."""
        return os.path.join("..", "..", "..", "..", "lib")

    def format_bp_lib_c_dir_path(self) -> str:
        """Formats the relative path of the directory of bitproto c lib."""
        return os.path.join(self.format_bp_lib_dir_path(), "c")

    def format_bp_lib_c_file_path(self) -> str:
        """Formats the relative path of the c lib file bitproto.c."""
        return os.path.join(self.format_bp_lib_c_dir_path(), "bitproto.c")

    def format_bp_filepath(self, filename: str) -> str:
        """Formats the relative filepath of given bitproto filename."""
        return os.path.join("", filename)

    def format_bp_outdir_path(self, lang: str) -> str:
        """Format the relative path of given bitproto's outdir."""
        return os.path.join(self.get_workdir(lang), self.get_outdir(lang))

    def formart_bp_out_filepath(
        self, lang: str, source_bp_filename: str, extension: str
    ) -> str:
        """Formats the relative path of generated bitproto file,
        by given source bp filename and target extension.
        """
        out = self.format_generated_bp_file(source_bp_filename, extension)
        return os.path.join(self.format_bp_outdir_path(lang), out)

    def format_source_filepath(self, lang: str, filename: str) -> str:
        """Format the path of given source filename."""
        return os.path.join(self.get_workdir(lang), filename)

    def format_build_filepath(self, lang: str) -> str:
        """Formats the relative path of build file.
        Returns empty string if not exist."""
        out = self.get_build_filename(lang)
        if not out:
            return ""
        return os.path.join(self.get_workdir(lang), out)

    def compile_bp(self) -> None:
        """Compile bitproto files."""
        for filename in self.bp_files:
            filepath = self.format_bp_filepath(filename)
            for lang in self.langs:
                out = self.format_bp_outdir_path(lang)
                cmd = f"bitproto {lang} {filepath} {out}"
                subprocess.check_call(cmd, shell=True)
                self.log(f"ok => {cmd}")

    def compile_c(self) -> None:
        lang = "c"
        source_filepath_list: List[str] = []

        for source_filename in self.source_files[lang]:
            source_filepath = self.format_source_filepath(lang, source_filename)
            source_filepath_list.append(source_filepath)

        # Append the bitproto generated file.
        for bp_filename in self.bp_files:
            generated_filepath = self.formart_bp_out_filepath(lang, bp_filename, ".c")
            source_filepath_list.append(generated_filepath)

        # Append the bitproto.c
        source_filepath_list.append(self.format_bp_lib_c_file_path())

        source = " ".join(source_filepath_list)
        libdir_c = self.format_bp_lib_c_dir_path()
        build = self.format_build_filepath(lang)

        cmd = f"{self.cc} -I. -I{libdir_c} {source} -o {build}"
        subprocess.check_call(cmd, shell=True)
        self.log(f"ok => {cmd}")

    def compile_go(self) -> None:
        pass

    def compile(self) -> None:
        self.compile_bp()

        for lang in self.langs:
            if lang == "c":
                self.compile_c()
            if lang == "go":
                self.compile_go()

    def run(self) -> None:
        self.chdir()
        self.compile()
        # clear build finally
        pass


def test_encoding_drone() -> None:
    _TestCase("drone").run()
