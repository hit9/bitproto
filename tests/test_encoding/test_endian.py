"""Tests for big-endian host support.

These run on a little-endian CI host without emulation, exploiting two facts:

1. The optimization-mode big-endian code path is *endian-neutral* (it extracts
   field bytes by value, with explicit shifts), so compiling the generated code
   with ``-DBP_BIG_ENDIAN`` and running it on a little-endian host still produces
   the correct, byte-identical wire output.  ``test_opt_mode_big_endian_branch``
   compiles each optimization-mode case both ways and asserts the wire bytes
   match each other and the (endian-independent) Python reference.

2. The runtime/non-optimization big-endian path *is* host-dependent (it reverses
   a field's bytes assuming the host is big-endian), so it cannot be exercised
   by compiling native structs on a little-endian host.  Instead
   ``test_runtime_big_endian_layout`` feeds it memory laid out *by hand* as
   big-endian and checks the wire bytes; that is host-independent because the
   raw bytes are supplied directly.

A genuine big-endian end-to-end run (e.g. qemu-user on s390x) is the gold
standard for CI but is intentionally out of scope here.
"""

import os
import shutil
import subprocess

import pytest

HERE = os.path.dirname(__file__)
CASES_DIR = os.path.join(HERE, "encoding-cases")
LIB_C_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "lib", "c"))

# Optimization-mode cases that emit encoded wire bytes to stdout (the "consts"
# case supports optimization mode but prints nothing, so it is excluded here).
OPT_MODE_CASES = [
    "nested",
    "arrays",
    "scatter",
    "enums",
    "signed",
]

_HAVE_TOOLS = all(shutil.which(t) for t in ("make", "bitproto", "gcc"))
requires_tools = pytest.mark.skipif(
    not _HAVE_TOOLS, reason="needs make, bitproto and gcc on PATH"
)


def _make(case: str, target: str, **env_extra: str) -> bytes:
    env = dict(os.environ, **env_extra)
    return subprocess.check_output(
        f"make -s --no-print-directory {target}",
        shell=True,
        cwd=os.path.join(CASES_DIR, case),
        env=env,
    )


def _clean(case: str) -> None:
    subprocess.check_call(
        "make -s --no-print-directory clean",
        shell=True,
        cwd=os.path.join(CASES_DIR, case),
    )


@requires_tools
@pytest.mark.parametrize("case", OPT_MODE_CASES)
def test_opt_mode_big_endian_branch(case: str) -> None:
    """The optimization-mode #else (big-endian) branch must produce the same
    wire bytes as the little-endian branch (which the rest of the suite already
    validates against the Python/Go reference encoders).
    """
    try:
        little = _make(case, "run-c", OPTIMIZATION_MODE_ARGS="-O").strip()
        _clean(case)  # force a fresh re-generate / re-compile
        big = _make(
            case,
            "run-c",
            OPTIMIZATION_MODE_ARGS="-O",
            CC_OPTIMIZATION_ARG="-DBP_BIG_ENDIAN",
        ).strip()
        # Best effort: also compare against the endian-independent Python
        # encoder when a "python" interpreter is available to the Makefile.
        reference = None
        if shutil.which("python"):
            reference = _make(case, "run-py").strip()
    finally:
        _clean(case)

    # The big-endian branch compiled and round-tripped (run-c asserts the
    # round-trip internally) ...
    assert big, "big-endian build produced no output"
    # ... and emits wire bytes identical to the little-endian branch.
    assert little == big, f"{case}: LE and BE wire bytes differ"
    if reference is not None:
        assert reference == big, f"{case}: BE wire bytes differ from python"


# A self-contained, host-independent check of the runtime big-endian path:
# feed BpEndecodeBaseType memory laid out as big-endian and assert the wire is
# the expected little-endian byte sequence.
_RUNTIME_BE_TEST_C = r"""
#include <assert.h>
#include <string.h>
#include "bitproto.h"

static void enc(int nbits, unsigned char *data, unsigned char *want, int n) {
    unsigned char s[16] = {0};
    struct BpProcessorContext ctx = BpProcessorContext(true, s);
    BpEndecodeBaseType(nbits, &ctx, data);
    assert(memcmp(s, want, n) == 0);
}

static void dec(int nbits, unsigned char *wire, unsigned char *want, int n) {
    unsigned char data[16] = {0};
    struct BpProcessorContext ctx = BpProcessorContext(false, wire);
    BpEndecodeBaseType(nbits, &ctx, data);
    assert(memcmp(data, want, n) == 0);
}

int main(void) {
    /* uint32 0x12345678: BE memory {12 34 56 78} <-> LE wire {78 56 34 12} */
    enc(32, (unsigned char[]){0x12,0x34,0x56,0x78},
            (unsigned char[]){0x78,0x56,0x34,0x12}, 4);
    dec(32, (unsigned char[]){0x78,0x56,0x34,0x12},
            (unsigned char[]){0x12,0x34,0x56,0x78}, 4);
    /* uint12 0x0ABC in a uint16: BE memory {0A BC} <-> LE wire {BC 0A} */
    enc(12, (unsigned char[]){0x0A,0xBC}, (unsigned char[]){0xBC,0x0A}, 2);
    dec(12, (unsigned char[]){0xBC,0x0A}, (unsigned char[]){0x0A,0xBC}, 2);
    /* uint20 0xABCDE in a uint32 (storage 4 != ceil(20/8)=3) */
    enc(20, (unsigned char[]){0x00,0x0A,0xBC,0xDE},
            (unsigned char[]){0xDE,0xBC,0x0A}, 3);
    dec(20, (unsigned char[]){0xDE,0xBC,0x0A},
            (unsigned char[]){0x00,0x0A,0xBC,0xDE}, 4);
    return 0;
}
"""


@requires_tools
def test_runtime_big_endian_layout(tmp_path) -> None:
    """The non-optimization runtime big-endian path maps big-endian field memory
    to little-endian wire bytes (and back), verified host-independently.
    """
    src = tmp_path / "be_runtime_test.c"
    src.write_text(_RUNTIME_BE_TEST_C)
    binpath = tmp_path / "be_runtime_test"
    subprocess.check_call(
        [
            "gcc",
            "-DBP_BIG_ENDIAN",
            "-I",
            LIB_C_DIR,
            str(src),
            os.path.join(LIB_C_DIR, "bitproto.c"),
            "-o",
            str(binpath),
        ]
    )
    subprocess.check_call([str(binpath)])
