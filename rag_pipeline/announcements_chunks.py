"""
announcements_chunks.py
------------------------
Reads announcements from the database and produces:

Level 1 — Per announcement: narrative + faq chunks
Level 2 — Per type summary: one chunk per announcement type
Level 3 — Overview: active announcements + deactivated announcements

Entry point: build(excel_path) — called by generate_chunks.py
"""

from collections import defaultdict

SOURCE   = "announcements"

VALID_TYPES = {
    "Holiday", "Exam", "Fee", "Event",
    "Result", "Admission", "General"
}


# ── Helpers ────────────────────────────────────────────────────────────────

def clean(v) -> str:
    """Return clean string or empty string for None/nan."""
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "-", "—") else s


def make_status_text(row: dict) -> str:
    """Build a natural language status line from is_active."""
    active  = clean(row.get("is_active", "")).lower() == "yes"

    if not active:
        return "This announcement has been deactivated by the admin."
    return "This announcement is currently active."


def make_slug(title: str) -> str:
    """Convert title to a safe chunk ID slug."""
    return (title.lower()
                 .replace(" ", "_")
                 .replace("/", "_")
                 .replace("-", "_")
                 .replace("&", "and")
                 .replace("(", "")
                 .replace(")", "")
                 .replace(",", "")
                 [:60])


# ── Level 1: Per-announcement chunks ──────────────────────────────────────

def per_announcement_chunks(rows: list[dict], semester: str = "spring_2026") -> list[dict]:
    chunks = []

    for row in rows:
        title       = clean(row.get("title"))
        description = clean(row.get("description"))
        ann_type    = clean(row.get("type", "General"))
        audience    = clean(row.get("target_audience", "All"))
        active      = clean(row.get("is_active", "Yes")).lower() == "yes"

        if not title or not description:
            print(f"  [WARN] Skipping row with missing title or description")
            continue

        status_text = make_status_text(row)

        # ── Narrative ──────────────────────────────────────────────────────
        narrative = (
            f"{title} — {ann_type} announcement at COMSATS University Islamabad, "
            f"Sahiwal Campus. {description} "
            f"Target audience: {audience}. {status_text}"
        ).strip()

        # ── FAQ ────────────────────────────────────────────────────────────
        faq_pairs = [
            (
                f"What is the {title}?",
                f"{description} {status_text}"
            ),
        ]

        if audience != "All":
            faq_pairs.append((
                f"Who is the {title} announcement for?",
                f"The {title} announcement is for {audience}."
            ))

        faq_text = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in faq_pairs)

        meta = {
            "title":           title,
            "type":            ann_type,
            "target_audience": audience,
            "is_active":       active,
            "source":          SOURCE,
            "semester":        semester,
        }

        slug    = make_slug(title)
        base_id = f"{SOURCE}_{semester}_{slug}"

        chunks.append({
            "chunk_id":   f"{base_id}_narrative",
            "chunk_type": "narrative",
            "topic":      SOURCE,
            "semester":   semester,
            "source":     SOURCE,
            "text":       narrative,
            "metadata":   meta,
        })
        chunks.append({
            "chunk_id":   f"{base_id}_faq",
            "chunk_type": "faq",
            "topic":      SOURCE,
            "semester":   semester,
            "source":     SOURCE,
            "text":       faq_text,
            "metadata":   meta,
        })

    return chunks


# ── Level 2: Per-type summary chunks ──────────────────────────────────────

def per_type_chunks(rows: list[dict], semester: str = "spring_2026") -> list[dict]:
    chunks = []
    by_type = defaultdict(list)

    for row in rows:
        ann_type = clean(row.get("type", "General")) or "General"
        by_type[ann_type].append(row)

    for ann_type, type_rows in sorted(by_type.items()):
        active_rows = [
            r for r in type_rows
            if clean(r.get("is_active", "Yes")).lower() == "yes"
        ]
        inactive_rows = [
            r for r in type_rows
            if clean(r.get("is_active", "Yes")).lower() != "yes"
        ]

        def row_summary(r):
            return clean(r.get("title", ""))

        all_summaries      = [row_summary(r) for r in type_rows]
        active_summaries   = [row_summary(r) for r in active_rows]
        inactive_summaries = [row_summary(r) for r in inactive_rows]

        narrative = (
            f"All {ann_type} announcements at COMSATS University Islamabad, "
            f"Sahiwal Campus for {semester.replace('_', ' ').title()}:\n"
            + "\n".join(f"- {s}" for s in all_summaries)
            + (
                f"\n\nActive {ann_type} announcements: "
                + (", ".join(r for r in active_summaries) if active_summaries
                   else f"No active {ann_type} announcements.")
            )
            + (
                f"\n\nDeactivated {ann_type} announcements: "
                + (", ".join(r for r in inactive_summaries) if inactive_summaries
                   else f"No deactivated {ann_type} announcements.")
            )
        )

        faq_text = "\n\n".join([
            f"Q: What {ann_type.lower()} announcements are there?\n"
            f"A: {ann_type} announcements: "
            + (", ".join(clean(r.get("title","")) for r in type_rows) or "None."),

            f"Q: Are there any active {ann_type.lower()} announcements?\n"
            f"A: " + (
                "Active: " + ", ".join(clean(r.get("title","")) for r in active_rows) + "."
                if active_rows
                else f"There are no active {ann_type.lower()} announcements currently."
            ),

            f"Q: What deactivated {ann_type.lower()} announcements are there?\n"
            f"A: " + (
                "Deactivated: " + ", ".join(clean(r.get("title","")) for r in inactive_rows) + "."
                if inactive_rows
                else f"No deactivated {ann_type.lower()} announcements recorded."
            ),
        ])

        slug    = ann_type.lower().replace(" ", "_")
        base_id = f"{SOURCE}_{semester}_{slug}_type_summary"
        meta    = {
            "type":     ann_type,
            "source":   SOURCE,
            "semester": semester,
            "level":    "type_summary",
        }

        chunks.append({
            "chunk_id":   f"{base_id}_narrative",
            "chunk_type": "narrative",
            "topic":      SOURCE,
            "semester":   semester,
            "source":     SOURCE,
            "text":       narrative,
            "metadata":   meta,
        })
        chunks.append({
            "chunk_id":   f"{base_id}_faq",
            "chunk_type": "faq",
            "topic":      SOURCE,
            "semester":   semester,
            "source":     SOURCE,
            "text":       faq_text,
            "metadata":   meta,
        })

    return chunks


# ── Level 3: Active + Deactivated overview chunks ──────────────────────────

def overview_chunks(rows: list[dict], semester: str = "spring_2026") -> list[dict]:
    chunks = []

    active_rows = [
        r for r in rows
        if clean(r.get("is_active", "Yes")).lower() == "yes"
    ]
    inactive_rows = [
        r for r in rows
        if clean(r.get("is_active", "Yes")).lower() != "yes"
    ]

    def fmt(r):
        title     = clean(r.get("title", ""))
        ann_type  = clean(r.get("type",  "General"))
        return f"{title} [{ann_type}]"

    # Active overview
    active_text = (
        f"Currently active announcements at COMSATS University Islamabad, "
        f"Sahiwal Campus ({semester.replace('_', ' ').title()}):\n"
        + (
            "\n".join(f"- {fmt(r)}" for r in active_rows)
            if active_rows
            else "No active announcements at this time."
        )
    )

    chunks.append({
        "chunk_id":   f"{SOURCE}_{semester}_active_overview",
        "chunk_type": "overview",
        "topic":      SOURCE,
        "semester":   semester,
        "source":     SOURCE,
        "text":       active_text,
        "metadata": {
            "level":    "active_overview",
            "source":   SOURCE,
            "semester": semester,
        },
    })

    # Deactivated overview
    inactive_text = (
        f"Deactivated announcements at COMSATS University Islamabad, "
        f"Sahiwal Campus ({semester.replace('_', ' ').title()}):\n"
        + (
            "\n".join(f"- {fmt(r)}" for r in inactive_rows)
            if inactive_rows
            else "No deactivated announcements recorded."
        )
    )

    chunks.append({
        "chunk_id":   f"{SOURCE}_{semester}_inactive_overview",
        "chunk_type": "overview",
        "topic":      SOURCE,
        "semester":   semester,
        "source":     SOURCE,
        "text":       inactive_text,
        "metadata": {
            "level":    "inactive_overview",
            "source":   SOURCE,
            "semester": semester,
        },
    })

    # Full overview (all announcements — useful for broad queries)
    full_text = (
        f"All announcements at COMSATS University Islamabad, "
        f"Sahiwal Campus ({semester.replace('_', ' ').title()}):\n\n"
        f"ACTIVE ({len(active_rows)}):\n"
        + ("\n".join(f"- {fmt(r)}" for r in active_rows) or "None.")
        + (
            f"\n\nDEACTIVATED ({len(inactive_rows)}):\n"
            + "\n".join(f"- {fmt(r)}" for r in inactive_rows)
            if inactive_rows else ""
        )
    )

    chunks.append({
        "chunk_id":   f"{SOURCE}_{semester}_full_overview",
        "chunk_type": "overview",
        "topic":      SOURCE,
        "semester":   semester,
        "source":     SOURCE,
        "text":       full_text,
        "metadata": {
            "level":    "full_overview",
            "source":   SOURCE,
            "semester": semester,
        },
    })

    return chunks


# ── Main build function ────────────────────────────────────────────────────

def build_chunks(rows: list[dict], semester: str = "spring_2026") -> list[dict]:
    """Build all 3 levels of chunks from a list of announcement dicts."""
    all_chunks = []
    all_chunks.extend(per_announcement_chunks(rows, semester))
    all_chunks.extend(per_type_chunks(rows, semester))
    all_chunks.extend(overview_chunks(rows, semester))
    return all_chunks


def build(excel_path: str = None, semester: str = "spring_2026", **kwargs) -> list[dict]:
    import os
    import psycopg2
 
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()
 
    cur.execute(
        """
        SELECT title, description, type, target_audience, is_active
        FROM announcements
        WHERE semester = %s
        ORDER BY created_at DESC
        """,
        (semester,)
    )
 
    cols = ["title", "description", "type", "target_audience", "is_active"]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
 
    cur.close()
    conn.close()
 
    print(f"  [announcements] Loaded {len(rows)} announcements "
          f"for semester '{semester}' from database")
 
    return build_chunks(rows, semester=semester)
