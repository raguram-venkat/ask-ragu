"""scripts/scan_vault_leaks.py (ADR-0022): diff line numbers and whole-word title matching."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "scan", Path(__file__).parent.parent / "scripts" / "scan_vault_leaks.py"
)
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

DIFF = """commit 0123456789abcdef0123
diff --git a/notes.md b/notes.md
--- a/notes.md
+++ b/notes.md
@@ -3,0 +4,2 @@
+Pulled a Ristretto today.
+nothing here
@@ -10 +12 @@
-old
+espresso (C++) and espressos
"""


def test_added_lines_carry_commit_path_and_line():
    assert scan.added_lines(DIFF) == [
        ("0123456789ab notes.md:4", "Pulled a Ristretto today."),
        ("0123456789ab notes.md:5", "nothing here"),
        ("0123456789ab notes.md:12", "espresso (C++) and espressos"),
    ]


def test_titles_match_whole_words_case_insensitive_never_printed():
    pattern = scan.matcher(["ristretto", "Espresso", "C++", "  "])
    hits = scan.scan(scan.added_lines(DIFF), pattern)
    # "espressos" is not a whole-word "Espresso"; regex characters in titles are literal.
    assert hits == {"0123456789ab notes.md:4": 1, "0123456789ab notes.md:12": 2}
