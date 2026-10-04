import pytest

from ask_ragu.index.chunk import chunk_note
from ask_ragu.settings import settings

MAX = 120


@pytest.fixture(autouse=True)
def chunk_rules(monkeypatch):
    """Small, pinned thresholds so each rule is easy to trigger and .env can't break tests."""
    for name, value in {
        "chunk_max_chars": MAX,
        "chunk_merge_below_chars": 30,
        "chunk_overlap_chars": 40,
        "stub_min_chars": 10,
    }.items():
        monkeypatch.setattr(settings, name, value)


def chunks(body):
    return [(c.heading_path, c.content) for c in chunk_note("T", body)]


def long(word, n=6):
    return " ".join([word] * n)  # ~ n * (len(word)+1) chars


def test_stub_note_gives_no_chunks():
    assert chunks("tiny") == []


def test_heading_path_and_content_without_heading_line():
    body = f"## Alpha\n{long('alpha')}\n### Beta\n{long('beta')}\n## Gamma\n{long('gamma')}"
    assert chunks(body) == [
        ("T > Alpha", long("alpha")),
        ("T > Alpha > Beta", long("beta")),
        ("T > Gamma", long("gamma")),
    ]


def test_heading_only_parent_folds_into_child_path():
    assert chunks(f"## Parent\n### Child\n{long('child')}") == [
        ("T > Parent > Child", long("child"))
    ]


def test_heading_inside_code_is_not_a_heading():
    body = f"## Real\n{long('real', 3)}\n```\n## not a heading\n```"
    assert chunks(body) == [("T > Real", f"{long('real', 3)}\n```\n## not a heading\n```")]


def test_preamble_is_its_own_chunk():
    body = f"{long('intro')}\n## Next\n{long('next')}"
    assert chunks(body) == [("T", long("intro")), ("T > Next", long("next"))]


def test_small_sections_merge_with_shared_prefix_path():
    body = f"## A\n{long('aaaa')}\n### A1\nshort\n### A2\n{long('second')}"
    # "short" (5 chars) is under the merge threshold, so it joins the previous chunk;
    # the shared path is "T > A" and A1's heading moves into the text.
    assert chunks(body) == [
        ("T > A", f"{long('aaaa')}\n\n### A1\nshort"),
        ("T > A > A2", long("second")),
    ]


def test_merge_never_exceeds_max():
    body = f"## A\n{'x' * (MAX - 5)}\n## B\nshort"
    assert [len(c) <= MAX for _, c in chunks(body)] == [True, True]


def test_oversize_section_splits_on_paragraphs_with_overlap():
    paras = [long(w, 5) for w in ("one", "two", "three", "four", "five")]
    out = chunks("## Big\n" + "\n\n".join(paras))
    assert len(out) > 1
    assert all(path == "T > Big" and 0 < len(c) <= MAX for path, c in out)
    # each window after the first starts with the previous window's last paragraph
    for (_, prev), (_, nxt) in zip(out, out[1:], strict=False):
        assert nxt.startswith(prev.split("\n\n")[-1])


def test_headingless_note_and_giant_line_stay_under_max():
    out = chunks("z" * (MAX * 3 + 7))
    assert [p for p, _ in out] == ["T"] * 4
    assert all(0 < len(c) <= MAX for _, c in out)
