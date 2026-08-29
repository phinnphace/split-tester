#!/usr/bin/env python3
"""Export the deliberately small first-iteration Paper Trail map.

SQLite remains authoritative. The browser payload contains six paper-level
relationship categories, their pairwise overlaps, the complete 45-item corpus
citation list, the ten current diagnostic cross-paper patterns, and the short
reference-source list supplied for the site. It does not contain full article
text, local paths, or held self-citation edges.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
WORKSPACE_DIR = REPO_DIR.parent
DEFAULT_DB = WORKSPACE_DIR / "paper_catalog" / "papers.sqlite3"
DEFAULT_ANALYSIS_DB = (
    WORKSPACE_DIR
    / "paper_catalog"
    / "iterations"
    / "2026-08-29"
    / "papers.sqlite3"
)
DEFAULT_OUTPUT = REPO_DIR / "paper_trail_map_data.js"
REFERENCE_CANDIDATES = (
    WORKSPACE_DIR / "reference-citation.txt",
    WORKSPACE_DIR / "reference-citations.txt",
    WORKSPACE_DIR / "refernce-citations.txt",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--analysis-db", type=Path, default=DEFAULT_ANALYSIS_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--reference-citations", type=Path)
    return parser.parse_args()


def scalar(connection: sqlite3.Connection, sql: str, parameters: tuple[Any, ...] = ()) -> Any:
    row = connection.execute(sql, parameters).fetchone()
    if row is None:
        raise ValueError("Expected a scalar query result")
    return row[0]


def repair_text(value: str | None) -> str | None:
    """Reverse the UTF-8-as-MacRoman mojibake present in a few CSV round trips."""
    if value is None:
        return None
    value = value.strip()
    try:
        repaired = value.encode("mac_roman").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
    return repaired


def paper_ids_for_concept(connection: sqlite3.Connection, concept_id: str) -> list[str]:
    return [
        row[0]
        for row in connection.execute(
            """
            SELECT DISTINCT paper_id
            FROM paper_concept_occurrences
            WHERE concept_id=?
            ORDER BY paper_id
            """,
            (concept_id,),
        )
    ]


def load_corpus_papers(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        WITH paper_venues AS (
            SELECT paper_id, MIN(normalized_name) AS normalized_name
            FROM v_paper_venue_relationships
            GROUP BY paper_id
        )
        SELECT
            ce.ordinal,
            p.paper_id,
            p.title,
            p.doi,
            p.publication_year,
            vr.normalized_name AS venue
        FROM corpus_entries ce
        JOIN papers p ON p.paper_id=ce.paper_id
        LEFT JOIN paper_venues vr ON vr.paper_id=p.paper_id
        WHERE ce.corpus_id='CORPUS-HCNN-CLEAN-V1'
        ORDER BY ce.ordinal
        """
    ).fetchall()
    if len(rows) != 45:
        raise ValueError(f"Expected 45 corpus papers; found {len(rows)}")

    authors: dict[str, list[tuple[int, str]]] = defaultdict(list)
    author_rows = connection.execute(
        """
        SELECT DISTINCT paper_id, author_order, name_as_returned
        FROM v_external_author_affiliation_relationships
        ORDER BY paper_id, author_order, name_as_returned
        """
    )
    seen_authors: set[tuple[str, int, str]] = set()
    for row in author_rows:
        key = (row["paper_id"], row["author_order"], row["name_as_returned"])
        if key in seen_authors:
            continue
        seen_authors.add(key)
        authors[row["paper_id"]].append(
            (row["author_order"], repair_text(row["name_as_returned"]))
        )

    papers: list[dict[str, Any]] = []
    for row in rows:
        author_names = [name for _, name in sorted(authors[row["paper_id"]])]
        if not author_names:
            raise ValueError(f"No author list registered for {row['paper_id']}")
        papers.append(
            {
                "ordinal": row["ordinal"],
                "paperId": row["paper_id"],
                "authors": author_names,
                "year": row["publication_year"],
                "title": repair_text(row["title"]),
                "venue": repair_text(row["venue"]),
                "doi": row["doi"],
            }
        )
    return papers


def load_cross_citations(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT citing_paper_id, cited_paper_id
        FROM external_citation_edges
        WHERE classification_as_returned='CROSS-CITATION (Zero Shared Authors)'
        ORDER BY citing_paper_id, cited_paper_id
        """
    ).fetchall()
    return [
        {"citingPaperId": row["citing_paper_id"], "citedPaperId": row["cited_paper_id"]}
        for row in rows
    ]


def load_venue_counts(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        {
            "label": row["normalized_name"],
            "count": row["paper_count"],
            "paperIds": row["paper_ids"].split(",") if row["paper_ids"] else [],
        }
        for row in connection.execute(
            """
            SELECT normalized_name, paper_count, paper_ids
            FROM v_venue_paper_counts
            ORDER BY paper_count DESC, normalized_name
            """
        )
    ]


def load_registered_publisher_rollups(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rollups = [
        {"label": row["publisher_name"], "count": row["paper_count"]}
        for row in connection.execute(
            """
            SELECT publisher_name, COUNT(DISTINCT paper_id) AS paper_count
            FROM v_paper_publisher_relationships
            GROUP BY publisher_id, publisher_name
            ORDER BY paper_count DESC, publisher_name
            """
        )
    ]
    family_count = scalar(
        connection,
        "SELECT COUNT(DISTINCT paper_id) FROM v_paper_publisher_relationships",
    )
    rollups.append({"label": "Springer Nature family", "count": family_count})
    return rollups


def load_reference_citations(explicit_path: Path | None) -> list[str]:
    candidates = (explicit_path,) if explicit_path else REFERENCE_CANDIDATES
    source = next((path for path in candidates if path and path.is_file()), None)
    if source is None:
        searched = ", ".join(str(path) for path in candidates if path)
        raise ValueError(f"Reference-citation file not found; searched: {searched}")
    blocks = [block.strip() for block in source.read_text(encoding="utf-8").split("\n\n")]
    citations = [" ".join(block.splitlines()) for block in blocks if block]
    if not citations:
        raise ValueError(f"Reference-citation file is empty: {source}")
    return citations


def load_diagnostic_patterns(db_path: Path) -> list[dict[str, Any]]:
    if not db_path.is_file():
        raise ValueError(f"Missing diagnostic catalog database: {db_path}")

    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if scalar(connection, "PRAGMA integrity_check") != "ok":
            raise ValueError("Diagnostic catalog integrity check failed")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Diagnostic catalog has foreign-key violations")

        rows = connection.execute(
            """
            SELECT pattern_id, pattern_type, shared_feature, comparison_method,
                   evidence_summary, target_set_prevalence,
                   alternative_explanation, confidence, materiality, status
            FROM cross_paper_patterns
            ORDER BY pattern_id
            """
        ).fetchall()
        patterns: list[dict[str, Any]] = []
        for row in rows:
            memberships = connection.execute(
                """
                SELECT ce.ordinal, cpp.role
                FROM cross_pattern_papers cpp
                JOIN corpus_entries ce ON ce.paper_id=cpp.paper_id
                WHERE cpp.pattern_id=?
                ORDER BY ce.ordinal
                """,
                (row["pattern_id"],),
            ).fetchall()
            patterns.append(
                {
                    "id": row["pattern_id"],
                    "type": row["pattern_type"],
                    "label": row["shared_feature"],
                    "method": row["comparison_method"],
                    "summary": row["evidence_summary"],
                    "prevalence": row["target_set_prevalence"],
                    "alternative": row["alternative_explanation"],
                    "confidence": row["confidence"],
                    "materiality": row["materiality"],
                    "status": row["status"],
                    "paperOrdinals": [member["ordinal"] for member in memberships],
                    "memberships": [
                        {"ordinal": member["ordinal"], "role": member["role"]}
                        for member in memberships
                    ],
                }
            )
    finally:
        connection.close()

    if len(patterns) != 10:
        raise ValueError(f"Expected 10 public diagnostic patterns; found {len(patterns)}")
    expected_ids = {
        "XPP-AUTHOR-MICROCLUSTERS",
        "XPP-BIOMEDICAL-ESCALATION",
        "XPP-COMPOUND-MODEL-NAMING",
        "XPP-HIGH-SCORE-WEAK-INDEPENDENCE",
        "XPP-LANGUAGE-TO-CLASSIFICATION",
        "XPP-LOCALIZED-SIGN-LANGUAGE",
        "XPP-PHYSIOLOGICAL-HAND-SENSING",
        "XPP-REPORTING-MISMATCHES",
        "XPP-SWARM-EVOLUTIONARY-OPTIMIZATION",
        "XPP-SYNTAX-TITLE-LEXICON",
    }
    actual_ids = {pattern["id"] for pattern in patterns}
    if actual_ids != expected_ids:
        raise ValueError(
            "Public diagnostic pattern identifiers differ from the current catalog"
        )
    return patterns


def build_payload(
    db_path: Path,
    analysis_db_path: Path,
    reference_path: Path | None,
) -> dict[str, Any]:
    if not db_path.is_file():
        raise ValueError(f"Missing catalog database: {db_path}")

    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if scalar(connection, "PRAGMA integrity_check") != "ok":
            raise ValueError("Catalog database integrity check failed")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Catalog database has foreign-key violations")

        papers = load_corpus_papers(connection)
        ordinal_by_id = {paper["paperId"]: paper["ordinal"] for paper in papers}
        all_paper_ids = [paper["paperId"] for paper in papers]
        cross_citations = load_cross_citations(connection)
        cross_paper_ids = sorted(
            {
                paper_id
                for edge in cross_citations
                for paper_id in (edge["citingPaperId"], edge["citedPaperId"])
            }
        )
        venue_counts = load_venue_counts(connection)
        publisher_rollups = load_registered_publisher_rollups(connection)

        patterns = [
            {
                "id": "cross-citations",
                "label": "cross-citations",
                "count": len(cross_citations),
                "countLabel": f"{len(cross_citations)} links",
                "paperIds": cross_paper_ids,
                "details": [
                    {
                        "label": f"#{ordinal_by_id[edge['citingPaperId']]:02d} → #{ordinal_by_id[edge['citedPaperId']]:02d}",
                        "count": None,
                    }
                    for edge in cross_citations
                ],
            },
            {
                "id": "publisher",
                "label": "Publisher",
                "count": len(venue_counts),
                "countLabel": f"{len(venue_counts)} venues · {len(all_paper_ids)} papers",
                "paperIds": all_paper_ids,
                "details": venue_counts,
                "rollups": publisher_rollups,
            },
            {
                "id": "non-english-sign-language-use",
                "label": "non-English sign language use",
                "paperIds": paper_ids_for_concept(connection, "DISC-SL-GENERIC"),
            },
            {
                "id": "cnn",
                "label": "Convolutional Neural Networks (CNN)",
                "paperIds": paper_ids_for_concept(connection, "DISC-METHOD-CNN"),
            },
            {
                "id": "non-machine-readable-titles",
                "label": "Non-machine readable titles",
                "paperIds": [
                    row[0]
                    for row in connection.execute(
                        "SELECT paper_id FROM v_paper_title_format_group ORDER BY paper_id"
                    )
                ],
            },
            {
                "id": "gesture-recognition",
                "label": "gesture recognition",
                "paperIds": paper_ids_for_concept(connection, "DISC-TASK-GESTURE"),
            },
        ]
    finally:
        connection.close()

    for pattern in patterns:
        pattern.setdefault("count", len(pattern["paperIds"]))
        pattern.setdefault("countLabel", f"{len(pattern['paperIds'])} papers")
        pattern["paperOrdinals"] = [ordinal_by_id[paper_id] for paper_id in pattern["paperIds"]]

    edges: list[dict[str, Any]] = []
    for index, left in enumerate(patterns):
        left_papers = set(left["paperIds"])
        for right in patterns[index + 1 :]:
            shared = sorted(left_papers.intersection(right["paperIds"]))
            if shared:
                edges.append(
                    {
                        "source": left["id"],
                        "target": right["id"],
                        "sharedPaperIds": shared,
                        "sharedPaperOrdinals": [ordinal_by_id[paper_id] for paper_id in shared],
                        "count": len(shared),
                    }
                )

    payload = {
        "meta": {
            "title": "Paper Trail working corpus map",
            "status": "Analysis in progress",
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "schemaVersion": "8",
            "corpusId": "CORPUS-HCNN-CLEAN-V1",
            "paperCount": len(papers),
            "relationshipCount": len(patterns),
            "crossCitationCount": len(cross_citations),
            "diagnosticPatternCount": 10,
        },
        "patterns": patterns,
        "edges": edges,
        "diagnosticPatterns": load_diagnostic_patterns(analysis_db_path),
        "papers": papers,
        "referenceCitations": load_reference_citations(reference_path),
    }

    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    forbidden = ("/Users/", "file://", "gwo-citation-station", "full_text")
    if any(token in serialized for token in forbidden):
        raise ValueError("Public payload contains local-only or full-text material")
    if len(patterns) != 6:
        raise ValueError("The first-iteration public map must contain exactly six nodes")
    return payload


def main() -> int:
    args = parse_args()
    try:
        payload = build_payload(args.db, args.analysis_db, args.reference_citations)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        body = (
            "// Generated from the Paper Trail SQLite catalog. Do not edit by hand.\n"
            "window.PAPER_TRAIL_MAP_DATA="
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            + ";\n"
        )
        args.output.write_text(body, encoding="utf-8")
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "output": str(args.output),
                "nodes": len(payload["patterns"]),
                "edges": len(payload["edges"]),
                "papers": len(payload["papers"]),
                "referenceCitations": len(payload["referenceCitations"]),
                "diagnosticPatterns": len(payload["diagnosticPatterns"]),
                "counts": {
                    pattern["id"]: pattern["countLabel"]
                    for pattern in payload["patterns"]
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
