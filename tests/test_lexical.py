"""Lexical search (Sprint 4 Task 1): OR-ed question lexemes over chunks.tsv, ts_rank_cd."""

import pytest

from ask_ragu import db
from ask_ragu.retrieval.lexical import lexical_search
from ask_ragu.settings import settings

CHUNKS = {  # name: (heading_path, content)
    "both": ("Pulls", "Espresso runs long, Ristretto runs short."),
    "espresso": ("Machines", "Espresso needs nine bars."),
    "heading": ("Ristretto Basics", "Short and sweet."),
    "body": ("Ratios", "A Ristretto uses less water."),
    "js": ("Runtimes", "node.js runs JavaScript outside the browser."),
    "url": ("Links", "Mirror at https://x.com/a'b for the slides."),
}


@pytest.fixture
def search(conn, monkeypatch):
    monkeypatch.setattr(settings, "retrieval_candidates", 50)
    db.migrate(conn)
    (note,) = conn.execute(
        "INSERT INTO notes (path, title, note_type, content_hash)"
        " VALUES ('N.md', 'N', 'concept', '') RETURNING id"
    ).fetchone()
    names = {}
    for order, (name, (heading, content)) in enumerate(CHUNKS.items()):
        (cid,) = conn.execute(
            "INSERT INTO chunks (note_id, chunk_order, heading_path, content, embedding)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (note, order, heading, content, str([0.0] * 384)),
        ).fetchone()
        names[cid] = name

    def search(question):
        return [names[cid] for cid, _, _ in lexical_search(conn, question)]

    return search


def test_words_are_ored_and_ranked_by_weighted_matches(search):
    # No chunk has every lexeme (differ, espresso, ristretto): AND would find nothing.
    # ts_rank_cd: a heading match (A) counts 1.0, a body match (B) 0.4; ties by chunk id.
    got = search("What is the difference between Espresso and Ristretto?")
    assert got == ["heading", "both", "espresso", "body"]  # 1.0, 0.8, 0.4, 0.4


def test_one_heading_match_outranks_body_matches(search):
    assert search("ristretto") == ["heading", "both", "body"]  # 1.0, 0.4, 0.4


def test_lexemes_match_the_index_exactly(search):
    assert search("node.js") == ["js"]  # one lexeme, not node + js
    assert search("https://x.com/a'b") == ["url"]  # a quote inside a lexeme is escaped


@pytest.mark.parametrize("question", ["", "   ", "the and of", "?!...", "a " * 3000])
def test_no_lexemes_means_no_hits_and_no_notice(conn, search, question):
    notices = []
    conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    assert search(question) == []
    assert notices == []


@pytest.mark.parametrize(
    "question", ["'; DROP TABLE chunks; --", "foo & bar | !baz (x) <-> y:*", '-espresso "x" or']
)
def test_input_is_never_search_syntax(search, question):
    search(question)  # no error: operators are just characters
    assert search("-espresso") == search("espresso")  # no negation


def test_candidates_cap(search, monkeypatch):
    monkeypatch.setattr(settings, "retrieval_candidates", 2)
    assert len(search("espresso ristretto water")) == 2
