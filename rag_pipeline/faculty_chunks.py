"""
faculty_chunks.py
-----------------
Reads faculty & staff office directory from Google Sheets and produces:

Level 1 — Per person:    "Where is Dr. X?" / "Which cabin is Dr. X in?"
Level 2 — Per office:    "Who is in Cabin 4?" / "Who shares CS-04?"
Level 3 — Per dept:      "Who are the CS faculty?" / "List Math department"
Level 4 — Per block/floor: "Who is on C Block Ground Floor?"

Entry point: build(excel_path, semester) — called by generate_chunks.py
"""

from collections import defaultdict

SOURCE = "faculty_directory"

DEPT_FULL = {
    "CS":           "Computer Science",
    "Math":         "Mathematics",
    "Civil":        "Civil Engineering",
    "Electrical":   "Electrical Engineering",
    "Mechanical":   "Mechanical Engineering",
    "Computer Eng": "Computer Engineering",
    "IT/Admin":     "IT / Administration",
    "Mixed":        "General / Mixed",
}


# ── Helpers ────────────────────────────────────────────────────────────────

def clean(v) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none", "—", "-") else s


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
                     [:50])


def dept_name(dept_code: str) -> str:
    return DEPT_FULL.get(dept_code, dept_code)


# ── Level 1: Per-person chunks ─────────────────────────────────────────────

def per_person_chunks(rows: list[dict], semester: str) -> list[dict]:
    chunks = []

    for r in rows:
        name     = clean(r.get("occupant_name"))
        office   = clean(r.get("office_cabin"))
        oid      = clean(r.get("office_id"))
        dept     = clean(r.get("department"))
        block    = clean(r.get("block"))
        floor    = clean(r.get("floor"))
        wing     = clean(r.get("side_wing"))
        role     = clean(r.get("special_role_note"))

        if not name:
            continue

        dept_full  = dept_name(dept)
        wing_text  = f" ({wing} side)" if wing else ""
        role_text  = f" {name} holds the role of {role}." if role else ""

        narrative = (
            f"{name} is a faculty/staff member of the {dept_full} Department "
            f"at COMSATS University Islamabad, Sahiwal Campus. "
            f"Their office is {office} (Office ID: {oid}), located in {block}, "
            f"{floor}{wing_text}.{role_text}"
        )

        faq = "\n\n".join([
            f"Q: Where is {name}'s office?\n"
            f"A: {name} is in {office} ({oid}), {block} {floor}{wing_text}.",

            f"Q: Which cabin or office does {name} sit in?\n"
            f"A: {name} is in {office} (ID: {oid}) at {block}, {floor}.",

            f"Q: Which department does {name} belong to?\n"
            f"A: {name} is in the {dept_full} Department.",

            *(
                [f"Q: What is {name}'s role?\nA: {name}'s role is {role}."]
                if role else []
            ),
        ])

        slug    = make_slug(name)
        base_id = f"{SOURCE}_{semester}_{slug}"

        meta = {
            "name":        name,
            "office_id":   oid,
            "office":      office,
            "department":  dept,
            "block":       block,
            "floor":       floor,
            "wing":        wing,
            "role":        role,
            "source":      SOURCE,
            "semester":    semester,
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


# ── Level 2: Per-office chunks ─────────────────────────────────────────────

def per_office_chunks(rows: list[dict], semester: str) -> list[dict]:
    chunks = []
    offices = defaultdict(list)

    for r in rows:
        name = clean(r.get("occupant_name"))
        oid  = clean(r.get("office_id"))
        if name and oid:
            offices[oid].append(r)

    for oid, members in offices.items():
        first     = members[0]
        office    = clean(first.get("office_cabin"))
        dept      = clean(first.get("department"))
        block     = clean(first.get("block"))
        floor     = clean(first.get("floor"))
        wing      = clean(first.get("side_wing"))
        dept_full = dept_name(dept)
        wing_text = f" ({wing} side)" if wing else ""

        names     = [clean(m.get("occupant_name")) for m in members]
        names_str = ", ".join(names)
        count     = len(names)

        narrative = (
            f"{office} (Office ID: {oid}) is located in {block}, {floor}{wing_text} "
            f"at COMSATS University Islamabad, Sahiwal Campus. "
            f"It belongs to the {dept_full} Department and currently "
            f"{'has' if count == 1 else 'is shared by'} "
            f"{count} {'person' if count == 1 else 'people'}: {names_str}."
        )

        roles = [clean(m.get("special_role_note")) for m in members if clean(m.get("special_role_note"))]
        if roles:
            narrative += f" Notable roles: {', '.join(roles)}."

        faq = "\n\n".join([
            f"Q: Who is in {office} ({oid})?\n"
            f"A: {names_str} {'is' if count == 1 else 'are'} in {office} ({oid}), "
            f"{block} {floor}{wing_text}.",

            f"Q: Where is {office} located?\n"
            f"A: {office} ({oid}) is in {block}, {floor}{wing_text}, "
            f"{dept_full} Department.",

            f"Q: How many people share {office}?\n"
            f"A: {count} {'person' if count == 1 else 'people'}: {names_str}.",
        ])

        slug    = make_slug(oid)
        base_id = f"{SOURCE}_{semester}_office_{slug}"

        meta = {
            "office_id":  oid,
            "office":     office,
            "department": dept,
            "block":      block,
            "floor":      floor,
            "wing":       wing,
            "occupants":  names_str,
            "count":      count,
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


# ── Level 3: Per-department chunks ─────────────────────────────────────────

def per_dept_chunks(rows: list[dict], semester: str) -> list[dict]:
    chunks = []
    depts = defaultdict(list)

    for r in rows:
        dept = clean(r.get("department"))
        name = clean(r.get("occupant_name"))
        if dept and name:
            depts[dept].append(r)

    for dept, members in sorted(depts.items()):
        dept_full = dept_name(dept)
        names     = [clean(m.get("occupant_name")) for m in members]
        count     = len(names)

        # Find HOD
        hod = next(
            (clean(m.get("occupant_name")) for m in members
             if "hod" in clean(m.get("special_role_note", "")).lower()),
            None
        )

        # Unique blocks/floors
        locations = list({
            f"{clean(m.get('block'))} {clean(m.get('floor'))}"
            for m in members
        })

        narrative = (
            f"The {dept_full} Department at COMSATS University Islamabad, "
            f"Sahiwal Campus has {count} faculty/staff members. "
            + (f"The Head of Department (HOD) is {hod}. " if hod else "")
            + f"Department offices are located in: {', '.join(locations)}. "
            f"Faculty members: {', '.join(names)}."
        )

        faq = "\n\n".join([
            f"Q: Who are the faculty members of the {dept_full} Department?\n"
            f"A: The {dept_full} Department has {count} members: {', '.join(names)}.",

            f"Q: Who is the HOD of {dept_full}?\n"
            f"A: " + (
                f"The HOD of {dept_full} is {hod}."
                if hod else
                f"The HOD information for {dept_full} is not listed separately."
            ),

            f"Q: Where are the {dept_full} faculty offices?\n"
            f"A: {dept_full} offices are in: {', '.join(locations)}.",

            f"Q: How many faculty are in {dept_full}?\n"
            f"A: There are {count} faculty/staff members in the {dept_full} Department.",
        ])

        slug    = make_slug(dept)
        base_id = f"{SOURCE}_{semester}_dept_{slug}"

        meta = {
            "department":      dept,
            "department_full": dept_full,
            "hod":             hod or "",
            "count":           count,
            "source":          SOURCE,
            "semester":        semester,
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


# ── Level 4: Per block+floor chunks ───────────────────────────────────────

def per_location_chunks(rows: list[dict], semester: str) -> list[dict]:
    chunks = []
    locations = defaultdict(list)

    for r in rows:
        block = clean(r.get("block"))
        floor = clean(r.get("floor"))
        name  = clean(r.get("occupant_name"))
        if block and floor and name:
            locations[(block, floor)].append(r)

    for (block, floor), members in sorted(locations.items()):
        names = [clean(m.get("occupant_name")) for m in members]
        count = len(names)

        depts_here = list({clean(m.get("department")) for m in members})
        depts_str  = ", ".join(dept_name(d) for d in depts_here if d)

        narrative = (
            f"{block}, {floor} at COMSATS University Islamabad, Sahiwal Campus "
            f"has offices for {count} faculty/staff members from the following "
            f"departments: {depts_str}. "
            f"Faculty/staff on this floor: {', '.join(names)}."
        )

        faq = "\n\n".join([
            f"Q: Who is on {floor} of {block}?\n"
            f"A: {count} faculty/staff are on {floor} of {block}: {', '.join(names)}.",

            f"Q: Which departments have offices on {floor} of {block}?\n"
            f"A: Departments with offices here: {depts_str}.",
        ])

        slug    = make_slug(f"{block}_{floor}")
        base_id = f"{SOURCE}_{semester}_location_{slug}"

        meta = {
            "block":    block,
            "floor":    floor,
            "count":    count,
            "source":   SOURCE,
            "semester": semester,
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
    chunks.extend(per_person_chunks(rows,   semester))
    chunks.extend(per_office_chunks(rows,   semester))
    chunks.extend(per_dept_chunks(rows,     semester))
    chunks.extend(per_location_chunks(rows, semester))
    return chunks


def build(excel_path: str = None,
          semester:   str = "spring_2026",
          **kwargs) -> list[dict]:
    """
    Entry point called by generate_chunks.py.
    Reads faculty directory from Google Sheets.
    One row per person — handles shared offices automatically.
    New faculty added to Google Sheet are picked up on next generate run.
    """
    import pandas as pd
    from rag_pipeline.sheets_reader import read_sheet

    df = read_sheet(
        topic      = "faculty_directory",
        sheet_name = "Faculty & Staff Directory",
        header_row = 2,   # row index 2 = 3rd row = actual headers
    )

    # Clean column names
    df.columns = [
        c.strip().lower()
         .replace(" ", "_")
         .replace("/", "_")
         .replace("(", "")
         .replace(")", "")
         .replace(".", "")
        for c in df.columns
    ]

    # Normalize column names
    rename = {}
    for c in df.columns:
        if c == "#" or c == "sr" or c == "no":        rename[c] = "sr_no"
        elif "office_id"    in c:                      rename[c] = "office_id"
        elif "office"       in c and "cabin" in c:     rename[c] = "office_cabin"
        elif "office"       in c or "cabin" in c:      rename[c] = "office_cabin"
        elif "occupant"     in c or "name"  in c:      rename[c] = "occupant_name"
        elif "department"   in c or "dept"  in c:      rename[c] = "department"
        elif "block"        in c:                      rename[c] = "block"
        elif "floor"        in c:                      rename[c] = "floor"
        elif "side"         in c or "wing"  in c:      rename[c] = "side_wing"
        elif "role"         in c or "note"  in c:      rename[c] = "special_role_note"
    df = df.rename(columns=rename)

    # Drop empty rows and footer rows
    if "occupant_name" not in df.columns:
        print("  [ERROR] Could not find occupant name column in faculty sheet")
        return []

    df = df[df["occupant_name"].notna()].copy()
    df = df[~df["occupant_name"].str.startswith("Total")].copy()
    df = df.reset_index(drop=True)

    print(f"  [faculty] Loaded {len(df)} faculty/staff from Google Sheets")

    rows = [
        {k: clean(v) for k, v in row.items()}
        for _, row in df.iterrows()
    ]

    return build_chunks(rows, semester)