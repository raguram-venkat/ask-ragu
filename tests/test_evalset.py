"""The checker against a throwaway vault built to match eval/questions.sample.yaml."""

import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ask_ragu import evalset
from ask_ragu.settings import settings

SAMPLE = Path(__file__).parents[1] / "eval" / "questions.sample.yaml"


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_excluded_dirs", {"Templates"})
    monkeypatch.setattr(settings, "vault_stripped_fences", set())
    monkeypatch.setattr(
        settings, "vault_folder_types", {"01 MOCs": "moc", "02 Concepts": "concept"}
    )
    monkeypatch.setattr(settings, "vault_default_note_type", "fleeting")
    for path, text in {
        "02 Concepts/Espresso.md": "Extraction takes 25 s. Grind matters: see [[Grinder]].",
        "02 Concepts/Grinder.md": "Finer grind slows the flow.",
        "01 MOCs/Coffee.md": "- [[Espresso]]\n- [[Grinder]]",
        "Templates/T.md": "template",
    }.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(text)
    git = ["git", "-C", str(tmp_path)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run(
        [*git, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c"], check=True
    )
    return tmp_path


def errors(questions, vault):
    return evalset.check(questions, vault).errors


def test_sample_is_valid_apart_from_size(vault):
    qs = evalset.load(SAMPLE)
    assert [e for e in errors(qs, vault) if not e.startswith("need at least")] == []


def test_enough_questions_pass(vault):
    qs = evalset.load(SAMPLE)
    many = [replace(q, id=f"{q.id}-{i}") for i in range(4) for q in qs]  # 16: 4 hop, 4 unanswerable
    assert errors(many, vault) == []


@pytest.mark.parametrize(
    "change, message",
    [
        (dict(gold=["02 Concepts/Missing.md"]), "not in the vault"),
        (dict(gold=["Templates/T.md"]), "excluded from the index"),
        (
            dict(
                kind="hop",
                via="02 Concepts/Grinder.md",
                gold=["02 Concepts/Grinder.md", "02 Concepts/Espresso.md"],
            ),
            "isn't a hop",
        ),  # fmt: skip
        (dict(kind="hop", via=None), "hop needs"),
        (dict(kind="unanswerable"), "gold must be empty"),
        (dict(kind="trivia"), "not in"),
    ],
)
def test_each_rule_reports(vault, change, message):
    q = replace(evalset.load(SAMPLE)[0], **change)
    assert any(message in e for e in errors([q], vault))


def test_duplicate_ids_and_drafts(vault):
    q = evalset.load(SAMPLE)[0]
    r = evalset.check([q, replace(q, origin="draft")], vault)
    assert any("duplicate id" in e for e in r.errors)
    assert any("still a draft" in w for w in r.warnings)
