"""Lexical search (SPEC §9 step 2): full-text over chunks.tsv (heading path weight A, body B).

The query is the question's own lexemes, OR-ed. websearch_to_tsquery ANDs every word, and no
chunk holds every word of a natural question (0 matches for 5 of 5 sample questions on the real
vault), so OR them and let ts_rank_cd rank chunks that match more of them, closer together,
higher. The lexemes come from to_tsvector with the same 'english' config the index uses, so
they match exactly (node.js stays one lexeme, prisoner's -> prisoner), and input can never act
as search syntax: no -negation, "phrases" or or/and operators.
"""

from uuid import UUID

import psycopg

from ask_ragu.settings import settings

# Each lexeme is a quoted tsquery literal ('' and \\ doubled), cast without re-parsing.
# A question with no lexemes (empty, all stopwords, only punctuation) gives q = NULL: no matches,
# and no "query doesn't contain lexemes" notice.
SEARCH = r"""
WITH q AS (
    SELECT string_agg(
               '''' || replace(replace(lexeme, '\', '\\'), '''', '''''') || '''', ' | '
           )::tsquery AS q
    FROM unnest(tsvector_to_array(to_tsvector('english', %(question)s))) AS lexeme
)
SELECT c.id, c.note_id, ts_rank_cd(c.tsv, q.q) AS score
FROM chunks c, q
WHERE c.tsv @@ q.q
ORDER BY score DESC, c.id
LIMIT %(k)s
"""


def lexical_search(conn: psycopg.Connection, question: str) -> list[tuple[int, UUID, float]]:
    """(chunk_id, note_id, score), best first; RETRIEVAL_CANDIDATES at most, [] if no lexemes."""
    return conn.execute(
        SEARCH, {"question": question, "k": settings.retrieval_candidates}
    ).fetchall()
