"""
faculty_kb_chunks.py
---------------------
Reads faculty-submitted knowledge base from Google Sheets and produces:

Level 1 — Per entry:    narrative + faq chunks
Level 2 — Per faculty:  all topics submitted by one faculty member
Level 3 — Per tag:      all entries sharing a common tag

Key feature: Every chunk explicitly attributes the information to the
submitting faculty member so the LLM can say
"According to [faculty_name], ..."

Columns expected in Google Sheet:
  faculty_name | topic | detail | tags | file_url

Entry point: build(excel_path, semester) — called by generate_chunks.py
"""

from collections import defaultdict

SOURCE = "faculty_knowledge_base"


# ── Helpers ────────────────────────────────────────────────────────────────

def clean(v) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "—", "-", "") else s


def make_slug(text: str) -> str:
    return (str(text).lower()
                     .replace(" ", "_")
                     .replace(".", "")
                     .replace("/", "_")
                     .replace("-", "_")
                     .replace("&", "and")
                     .replace("(", "")
                     .replace(")", "")
                     .replace(",", "")
                     [:60])


def parse_tags(tags_str: str) -> list[str]:
    """Parse comma-separated tags into a clean list."""
    if not tags_str:
        return []
    return [t.strip() for t in tags_str.split(",") if t.strip()]


# ── Level 1: Per-entry chunks ──────────────────────────────────────────────

def per_entry_chunks(rows: list[dict], semester: str) -> list[dict]:
    chunks = []

    for i, r in enumerate(rows):
        faculty = clean(r.get("faculty_name"))
        topic   = clean(r.get("topic"))
        detail  = clean(r.get("detail"))
        tags    = parse_tags(clean(r.get("tags", "")))
        file_url = clean(r.get("file_url", ""))

        if not faculty or not topic or not detail:
            print(f"  [WARN] Skipping row {i+1} — missing faculty_name, topic or detail")
            continue

        tags_text    = f" Related tags: {', '.join(tags)}." if tags else ""
        file_text    = (
            f" Additional reference material is available at: {file_url}"
            if file_url else ""
        )

        # ── Narrative ──────────────────────────────────────────────────────
        narrative = (
            f"The following information about '{topic}' was submitted by "
            f"{faculty} at COMSATS University Islamabad, Sahiwal Campus. "
            f"{detail}{tags_text}{file_text}"
        )

        # ── FAQ ────────────────────────────────────────────────────────────
        faq_pairs = [
            (
                f"What is '{topic}'?",
                f"According to {faculty}: {detail}"
                + (f" For more details: {file_url}" if file_url else "")
            ),
            (
                f"Who provided information about '{topic}'?",
                f"This information was submitted by {faculty}."
            ),
        ]

        if tags:
            faq_pairs.append((
                f"What topics are related to '{topic}'?",
                f"Related topics/tags: {', '.join(tags)}."
            ))

        if file_url:
            faq_pairs.append((
                f"Is there a document or file available for '{topic}'?",
                f"Yes. {faculty} has shared a reference file: {file_url}"
            ))

        faq_text = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in faq_pairs)

        # ── Metadata ───────────────────────────────────────────────────────
        meta = {
            "faculty_name": faculty,
            "topic":        topic,
            "tags":         ", ".join(tags),
            "has_file":     bool(file_url),
            "source":       SOURCE,
            "semester":     semester,
        }

        slug    = make_slug(f"{faculty}_{topic}")
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


# ── Level 2: Per-faculty summary chunks ───────────────────────────────────

def per_faculty_chunks(rows: list[dict], semester: str) -> list[dict]:
    chunks = []
    by_faculty = defaultdict(list)

    for r in rows:
        faculty = clean(r.get("faculty_name"))
        topic   = clean(r.get("topic"))
        detail  = clean(r.get("detail"))
        if faculty and topic and detail:
            by_faculty[faculty].append(r)

    for faculty, entries in sorted(by_faculty.items()):
        topics = [clean(e.get("topic")) for e in entries]
        count  = len(entries)

        topic_lines = []
        for e in entries:
            t        = clean(e.get("topic"))
            d        = clean(e.get("detail"))
            file_url = clean(e.get("file_url", ""))
            line     = f"- {t}: {d[:120]}{'...' if len(d) > 120 else ''}"
            if file_url:
                line += f" [File: {file_url}]"
            topic_lines.append(line)

        narrative = (
            f"{faculty} has submitted {count} knowledge base "
            f"{'entry' if count == 1 else 'entries'} at COMSATS University "
            f"Islamabad, Sahiwal Campus. "
            f"Topics covered: {', '.join(topics)}.\n\n"
            + "\n".join(topic_lines)
        )

        faq = "\n\n".join([
            f"Q: What information has {faculty} submitted?\n"
            f"A: {faculty} has submitted {count} entries covering: "
            f"{', '.join(topics)}.",

            f"Q: How many topics has {faculty} added to the knowledge base?\n"
            f"A: {faculty} has submitted {count} "
            f"{'topic' if count == 1 else 'topics'}.",
        ])

        slug    = make_slug(faculty)
        base_id = f"{SOURCE}_{semester}_faculty_{slug}"

        meta = {
            "faculty_name":   faculty,
            "topics_covered": ", ".join(topics),
            "entry_count":    count,
            "source":         SOURCE,
            "semester":       semester,
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
            "text":       faq,
            "metadata":   meta,
        })

    return chunks


# ── Level 3: Per-tag chunks ────────────────────────────────────────────────

def per_tag_chunks(rows: list[dict], semester: str) -> list[dict]:
    chunks = []
    by_tag = defaultdict(list)

    for r in rows:
        tags   = parse_tags(clean(r.get("tags", "")))
        topic  = clean(r.get("topic"))
        detail = clean(r.get("detail"))
        if topic and detail:
            for tag in tags:
                by_tag[tag.lower()].append(r)

    for tag, entries in sorted(by_tag.items()):
        if len(entries) < 2:
            continue  # skip tags with only one entry — not useful for summary

        faculties = list({clean(e.get("faculty_name")) for e in entries})
        topics    = [clean(e.get("topic")) for e in entries]

        narrative = (
            f"The following knowledge base entries are tagged '{tag}' "
            f"at COMSATS University Islamabad, Sahiwal Campus. "
            f"Submitted by: {', '.join(faculties)}. "
            f"Topics: {', '.join(topics)}.\n\n"
            + "\n".join(
                f"- [{clean(e.get('faculty_name'))}] {clean(e.get('topic'))}: "
                f"{clean(e.get('detail'))[:120]}..."
                for e in entries
            )
        )

        faq = (
            f"Q: What information is available about '{tag}'?\n"
            f"A: {len(entries)} entries tagged '{tag}': "
            + "; ".join(
                f"{clean(e.get('topic'))} (by {clean(e.get('faculty_name'))})"
                for e in entries
            ) + "."
        )

        slug    = make_slug(tag)
        base_id = f"{SOURCE}_{semester}_tag_{slug}"

        meta = {
            "tag":        tag,
            "entry_count": len(entries),
            "source":     SOURCE,
            "semester":   semester,
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
            "text":       faq,
            "metadata":   meta,
        })

    return chunks


# ── Main build functions ───────────────────────────────────────────────────

def build_chunks(rows: list[dict], semester: str = "spring_2026") -> list[dict]:
    chunks = []
    chunks.extend(per_entry_chunks(rows,   semester))
    chunks.extend(per_faculty_chunks(rows, semester))
    chunks.extend(per_tag_chunks(rows,     semester))
    return chunks


def build(excel_path: str = None,
          semester:   str = "spring_2026",
          **kwargs) -> list[dict]:
    """
    Entry point called by generate_chunks.py.
    Reads faculty knowledge base from Google Sheets.

    Expected columns (row 1 = headers, no title rows):
        faculty_name | topic | detail | tags | file_url

    - faculty_name: who submitted this entry
    - topic:        short title of the information
    - detail:       full explanation
    - tags:         comma-separated keywords
    - file_url:     optional Google Drive or any URL for extra reference
    """
    from rag_pipeline.sheets_reader import read_sheet

    df = read_sheet(
        topic      = "faculty_knowledge_base",
        sheet_name = None,       # use tab name from sheets_config.json
        header_row = 0,          # first row = headers (simple flat sheet)
    )

    # Clean column names
    df.columns = [
        c.strip().lower()
         .replace(" ", "_")
         .replace("/", "_")
        for c in df.columns
    ]

    # Normalize column names
    rename = {}
    for c in df.columns:
        if   "faculty" in c and "name" in c: rename[c] = "faculty_name"
        elif "topic"   in c:                 rename[c] = "topic"
        elif "detail"  in c:                 rename[c] = "detail"
        elif "tag"     in c:                 rename[c] = "tags"
        elif "file"    in c or "url" in c:   rename[c] = "file_url"
    df = df.rename(columns=rename)

    # Drop empty rows
    required = ["faculty_name", "topic", "detail"]
    for col in required:
        if col not in df.columns:
            print(f"  [ERROR] Missing required column '{col}' in faculty_knowledge_base sheet")
            return []

    df = df[df["faculty_name"].notna() & (df["faculty_name"].str.strip() != "")].copy()
    df = df[df["topic"].notna()  & (df["topic"].str.strip()  != "")].copy()
    df = df[df["detail"].notna() & (df["detail"].str.strip() != "")].copy()
    df = df.reset_index(drop=True)

    print(f"  [faculty_kb] Loaded {len(df)} entries from Google Sheets")

    if len(df) == 0:
        print("  [faculty_kb] No entries found — sheet may be empty")
        return []

    rows = [
        {k: clean(v) for k, v in row.items()}
        for _, row in df.iterrows()
    ]

    return build_chunks(rows, semester)
