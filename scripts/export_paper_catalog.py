#!/usr/bin/env python3
"""Export the public paper-catalog snapshot from the audit SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def rows(connection: sqlite3.Connection, query: str, parameters: tuple = ()) -> list[dict]:
    return [dict(row) for row in connection.execute(query, parameters)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("output", type=Path, nargs="?", default=Path("paper_catalog_data.js"))
    args = parser.parse_args()

    connection = sqlite3.connect(args.database)
    connection.row_factory = sqlite3.Row

    papers = rows(
        connection,
        """
        SELECT ce.ordinal AS reference_number, p.paper_id, p.title, p.doi, p.venue,
               p.publication_year, p.authors_raw, p.review_stage,
               rr.evidence_level, rr.run_status
        FROM corpus_entries ce
        JOIN papers p ON p.paper_id = ce.paper_id
        JOIN paper_review_runs rr ON rr.corpus_entry_id = ce.corpus_entry_id
        ORDER BY ce.ordinal
        """,
    )

    for paper in papers:
        paper["protocol"] = {
            item["item_code"]: {
                "status": item["response_status"],
                "value": item["response_value"],
                "locator": item["source_locator"],
            }
            for item in rows(
                connection,
                """
                SELECT pi.item_code, pr.response_status, pr.response_value,
                       pr.source_locator
                FROM protocol_responses pr
                JOIN protocol_items pi ON pi.protocol_item_id = pr.protocol_item_id
                JOIN paper_review_runs rr ON rr.review_run_id = pr.review_run_id
                JOIN corpus_entries ce ON ce.corpus_entry_id = rr.corpus_entry_id
                WHERE ce.paper_id = ?
                ORDER BY pi.ordinal
                """,
                (paper["paper_id"],),
            )
        }
        paper["patterns"] = [
            item["pattern_id"]
            for item in rows(
                connection,
                "SELECT pattern_id FROM cross_pattern_papers WHERE paper_id = ? ORDER BY pattern_id",
                (paper["paper_id"],),
            )
            if item["pattern_id"] != "XPP-SYNTAX-TITLE-LEXICON"
        ]

    patterns = rows(
        connection,
        """
        SELECT pattern_id, pattern_type, shared_feature, comparison_method,
               evidence_summary, target_set_prevalence, alternative_explanation,
               confidence, materiality, status, notes
        FROM cross_paper_patterns
        WHERE pattern_id != 'XPP-SYNTAX-TITLE-LEXICON'
        ORDER BY pattern_id
        """,
    )
    for pattern in patterns:
        pattern["papers"] = [
            item["reference_number"]
            for item in rows(
                connection,
                """
                SELECT ce.ordinal AS reference_number
                FROM cross_pattern_papers cpp
                JOIN corpus_entries ce ON ce.paper_id = cpp.paper_id
                WHERE cpp.pattern_id = ?
                ORDER BY ce.ordinal
                """,
                (pattern["pattern_id"],),
            )
        ]

    protocol_items = rows(
        connection,
        "SELECT item_code, prompt, ordinal FROM protocol_items ORDER BY ordinal",
    )
    payload = {
        "meta": {
            "corpus_size": len(papers),
            "full_text_count": sum(p["evidence_level"] == "full_text" for p in papers),
            "citation_only_count": sum(p["evidence_level"] == "citation_only" for p in papers),
            "pattern_count": len(patterns),
            "protocol_field_count": len(protocol_items),
            "snapshot_date": "2026-08-12",
            "review_status": "First-pass extraction; independent review pending",
        },
        "protocol_items": protocol_items,
        "patterns": patterns,
        "papers": papers,
    }

    args.output.write_text(
        "window.PAPER_CATALOG = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
