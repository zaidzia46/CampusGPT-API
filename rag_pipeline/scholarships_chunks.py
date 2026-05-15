import pandas as pd


SOURCE = "scholarships"
DEFAULT_SEMESTER = "spring_2026"
SEMESTER = DEFAULT_SEMESTER

def _narrative_merit_engineering(r: dict) -> str:
    exam = r["exam_type"]
    pct  = r["min_marks_pct"]
    return (
        f"The {r['scholarship_name']} is a merit-based, internally funded scholarship "
        f"available to students admitted into BS Engineering programs at COMSATS University "
        f"Islamabad, Sahiwal Campus. It is awarded to candidates who scored {pct}% or above "
        f"in their {exam} examination. The total semester fee is Rs. {r['total_semester_fee']:,}, "
        f"which includes a total tuition fee of Rs. {r['total_tuition_fee']:,}. Under this scholarship, "
        f"Rs. {r['scholarship_amount']:,} is waived from the tuition fee, leaving the student "
        f"responsible for paying Rs. {r['student_pays']:,} per semester. "
        f"This scholarship continues in subsequent semesters provided the student maintains "
        f"a CGPA of 3.3 out of 4.0. One restoration chance is allowed if the CGPA drops. "
        f"Students involved in disciplinary matters are permanently disqualified. "
        f"A one-time admission fee of Rs. 22,000 is charged separately at the time of admission."
    )


def _narrative_merit_non_engineering(r: dict) -> str:
    pct = r["min_marks_pct"]
    return (
        f"The {r['scholarship_name']} is a merit-based, internally funded scholarship for "
        f"students admitted into BS Non-Engineering programs at COMSATS University Islamabad, "
        f"Sahiwal Campus. Students who scored {pct}% or above in their Intermediate or equivalent "
        f"examination are eligible. The total semester fee is Rs. {r['total_semester_fee']:,} "
        f"(tuition fee Rs. {r['total_tuition_fee']:,}). A scholarship of Rs. {r['scholarship_amount']:,} "
        f"is deducted from tuition, so the student pays Rs. {r['student_pays']:,} per semester. "
        f"Continuation requires a CGPA of 3.3/4.0 or higher. One CGPA restoration chance is "
        f"permitted across the full degree (8 semesters). Disciplinary violations result in "
        f"permanent disqualification. A one-time admission fee of Rs. 22,000 applies."
    )


def _narrative_special(r: dict) -> str:
    return (
        f"The {r['scholarship_name']} is a special, internally funded scholarship at COMSATS "
        f"University Islamabad, Sahiwal Campus. It is automatically awarded to all eligible and "
        f"admitted students of the relevant program — no separate application is required. "
        f"In the first semester, tuition fee waiver is Rs. 59,000, and for the remaining seven "
        f"semesters the waiver is Rs. 37,000 per semester. The student pays Rs. 98,000 per semester "
        f"(total semester fee Rs. {r['total_semester_fee']:,}). A one-time admission fee of Rs. 22,000 "
        f"is NOT charged for special scholarship students. CGPA of 3.3/4.0 must be maintained "
        f"for continuation."
    )


def _narrative_english(r: dict) -> str:
    return (
        f"The {r['scholarship_name']} is a special, internally funded scholarship available to "
        f"all eligible and admitted students of the BS English program at COMSATS University "
        f"Islamabad, Sahiwal Campus. The scholarship provides a tuition fee waiver of Rs. 65,000 "
        f"per semester. The student pays Rs. 70,000 per semester as the semester fee. "
        f"No separate application is needed — all admitted BS English students receive it. "
        f"CGPA of 3.3/4.0 must be maintained for continuation."
    )


def _narrative_external(r: dict) -> str:
    note = r.get("notes", "Contact the Student Support Center for eligibility details.")
    return (
        f"The {r['scholarship_name']} is an externally funded scholarship available at COMSATS "
        f"University Islamabad, Sahiwal Campus. Eligibility is determined by the funding body: "
        f"{r['eligibility_description']}. {note} "
        f"Students interested in this scholarship should approach the Student Support Center "
        f"with their relevant documents. Scholarship amounts and terms are subject to the "
        f"funding body's approval and may vary each semester."
    )


def _narrative_kinship(r: dict) -> str:
    return (
        f"The Kinship / Sibling Concession is available to students at COMSATS University "
        f"Islamabad, Sahiwal Campus on a kinship or sibling basis. The concession amount is "
        f"Rs. 16,000 per semester for all BS programs. Students should contact the Student "
        f"Support Center and provide relevant documentation to avail this concession."
    )


def _faq_merit_engineering(r: dict) -> str:
    exam = r["exam_type"]
    pct  = r["min_marks_pct"]
    return "\n".join([
        f"Q: I got {pct}% in my {exam}. How much scholarship will I get for BS Engineering?",
        f"A: You qualify for the {r['scholarship_name']}. Your tuition fee waiver is "
        f"Rs. {r['scholarship_amount']:,} per semester. You will pay Rs. {r['student_pays']:,} "
        f"per semester (total semester fee is Rs. {r['total_semester_fee']:,}).",
        "",
        f"Q: What is the minimum percentage required to get Rs. {r['scholarship_amount']:,} "
        f"scholarship in BS Engineering ({exam})?",
        f"A: You need {pct}% or above in {exam} to receive this scholarship.",
        "",
        f"Q: Will I lose the scholarship if my CGPA drops?",
        f"A: Yes. You must maintain a CGPA of 3.3/4.0. If it drops, the scholarship is "
        f"discontinued. However, one restoration chance is allowed during the entire degree.",
        "",
        f"Q: Is the admission fee included in the Rs. {r['student_pays']:,} I pay per semester?",
        f"A: No. A one-time admission fee of Rs. 22,000 is charged separately at admission.",
    ])


def _faq_merit_non_engineering(r: dict) -> str:
    pct = r["min_marks_pct"]
    return "\n".join([
        f"Q: I scored {pct}% in FSc. What scholarship do I get for a BS Non-Engineering program?",
        f"A: You qualify for the {r['scholarship_name']}. You receive Rs. {r['scholarship_amount']:,} "
        f"off your tuition and pay Rs. {r['student_pays']:,} per semester.",
        "",
        f"Q: How much is the total semester fee after this scholarship?",
        f"A: Rs. {r['student_pays']:,} per semester (down from Rs. {r['total_semester_fee']:,}).",
        "",
        f"Q: What CGPA must I maintain to keep this scholarship?",
        f"A: You must maintain a CGPA of 3.3 out of 4.0. One restoration chance is given.",
    ])


def _faq_special(r: dict) -> str:
    return "\n".join([
        f"Q: Do I need to apply separately for the {r['scholarship_name']}?",
        f"A: No. It is automatically awarded to all admitted students of the program.",
        "",
        f"Q: How much will I pay per semester under this scholarship?",
        f"A: Rs. 98,000 per semester. In semester 1 the tuition waiver is Rs. 59,000; "
        f"from semester 2 onward the waiver is Rs. 37,000.",
        "",
        f"Q: Is the Rs. 22,000 admission fee charged for special scholarship students?",
        f"A: No. The admission fee is waived for all special scholarship program students.",
    ])


def _faq_english(r: dict) -> str:
    return "\n".join([
        f"Q: How much scholarship do BS English students get?",
        f"A: All admitted BS English students receive a tuition fee waiver of Rs. 65,000 "
        f"per semester and pay Rs. 70,000 per semester.",
        "",
        f"Q: Do I need to apply for the BS English scholarship?",
        f"A: No. It is automatically awarded to all eligible admitted students.",
    ])


def _faq_external(r: dict) -> str:
    return "\n".join([
        f"Q: What is the {r['scholarship_name']}?",
        f"A: It is an externally funded scholarship. Eligibility: {r['eligibility_description']}.",
        "",
        f"Q: How do I apply for the {r['scholarship_name']}?",
        f"A: Contact the Student Support Center at COMSATS Sahiwal Campus with your documents. "
        f"The final award is subject to the funding body's approval.",
        "",
        f"Q: Is the amount of the {r['scholarship_name']} fixed?",
        f"A: No. The amount depends on the funding body's approval and may vary each semester.",
    ])


def _faq_kinship(r: dict) -> str:
    return "\n".join([
        f"Q: What is the kinship or sibling concession at COMSATS Sahiwal?",
        f"A: Students with a sibling currently enrolled can get Rs. 16,000 off per semester "
        f"for all BS programs.",
        "",
        f"Q: How do I claim the kinship concession?",
        f"A: Visit the Student Support Center with proof of sibling enrollment.",
    ])


def _metadata(r: dict, semester: str = DEFAULT_SEMESTER) -> dict:
    return {
        "scholarship_id":        r.get("sr_no"),
        "scholarship_name":      r.get("scholarship_name"),
        "category":              r.get("category"),
        "funding_source":        r.get("funding_source"),
        "program_type":          r.get("program_type"),
        "exam_type":             r.get("exam_type"),
        "min_marks_pct":         r.get("min_marks_pct"),
        "scholarship_amount_rs": r.get("scholarship_amount"),
        "student_pays_rs":       r.get("student_pays"),
        "is_need_based":         r.get("is_need_based", False),
        "is_female_only":        r.get("is_female_only", False),
        "is_auto_awarded":       r.get("is_auto_awarded", False),
        "source":                SOURCE,
        "semester":              semester,
    }



def _build_chunks_for_row(r: dict, semester: str = DEFAULT_SEMESTER) -> list[dict]:
    cat  = str(r.get("category", "")).strip()
    name = str(r.get("scholarship_name", "")).lower()

    # ── sr_no=1: Top-10 Board Position (100% waiver, no numeric fees) ──
    if r.get("sr_no") == 1 or "top 10" in name or "board position" in name:
        narrative = (
            "The High Achievers Scholarship at COMSATS University Islamabad, Sahiwal Campus "
            "provides a 100% tuition fee waiver to students who secured a Top Ten (10) Board "
            "Position from any Board across Pakistan. This applies to all undergraduate degree "
            "programs. The student pays only Rs. 7,000 per semester, covering non-tuition "
            "charges. No separate application is needed — position holders are identified at "
            "admission. Continuation requires maintaining a CGPA of 3.3 out of 4.0."
        )
        faq = "\n".join([
            "Q: I got a top 10 position in my Board exams. What scholarship do I get at COMSATS Sahiwal?",
            "A: You qualify for the High Achievers Scholarship — 100% tuition fee waiver. You only pay Rs. 7,000 per semester.",
            "",
            "Q: Does the top 10 board scholarship apply to all programs?",
            "A: Yes. It applies to all undergraduate degree programs at COMSATS Sahiwal Campus.",
            "",
            "Q: Do I need to apply separately for this scholarship?",
            "A: No. You will be identified at the time of admission based on your board result.",
        ])

    elif r.get("sr_no") == 13 or "daanish" in name:
        narrative = (
            "The Special Scholarship for Students of Daanish Schools System is available at "
            "COMSATS University Islamabad, Sahiwal Campus. It provides a lumpsum scholarship "
            "of up to full fee waiver, determined as per PEEF Eligibility Criteria alongside "
            "CUI Sahiwal Campus Scholarship policy. The one-time admission fee of Rs. 22,000 "
            "is not charged for Daanish School students."
        )
        faq = "\n".join([
            "Q: Is there a scholarship for Daanish School students at COMSATS Sahiwal?",
            "A: Yes. Daanish School students can receive a lumpsum scholarship of up to full fee waiver.",
            "",
            "Q: How is the Daanish Schools scholarship amount determined?",
            "A: It is determined as per PEEF Eligibility Criteria alongside CUI Sahiwal Campus Scholarship policy.",
            "",
            "Q: Is the admission fee charged for Daanish School students?",
            "A: No. The Rs. 22,000 admission fee is waived for Daanish School students.",
        ])

    elif cat == "merit_internal":
        if "engineering" in str(r.get("program_type", "")).lower():
            narrative = _narrative_merit_engineering(r)
            faq       = _faq_merit_engineering(r)
        else:
            narrative = _narrative_merit_non_engineering(r)
            faq       = _faq_merit_non_engineering(r)

    elif cat == "special_internal":
        if "english" in name:
            narrative = _narrative_english(r)
            faq       = _faq_english(r)
        elif "kinship" in name or "sibling" in name:
            narrative = _narrative_kinship(r)
            faq       = _faq_kinship(r)
        else:
            narrative = _narrative_special(r)
            faq       = _faq_special(r)

    else:
        narrative = _narrative_external(r)
        faq       = _faq_external(r)

    base_id = f"{SOURCE}_{semester}_sr{int(r['sr_no']):02}"

    return [
        {
            "chunk_id":   f"{base_id}_narrative",
            "chunk_type": "narrative",
            "topic":      SOURCE,
            "semester":   semester,
            "source":     SOURCE,
            "text":       narrative,
            "metadata":   _metadata(r, semester=semester),
        },
        {
            "chunk_id":   f"{base_id}_faq",
            "chunk_type": "faq",
            "topic":      SOURCE,
            "semester":   semester,
            "source":     SOURCE,
            "text":       faq,
            "metadata":   _metadata(r, semester=semester),
        },
        {
            "chunk_id":   f"{base_id}_metadata",
            "chunk_type": "metadata",
            "topic":      SOURCE,
            "semester":   semester,
            "source":     SOURCE,
            "text":       (
                f"Scholarship: {r.get('scholarship_name')} | "
                f"Category: {r.get('category')} | "
                f"Program: {r.get('program_type')} | "
                f"Exam: {r.get('exam_type', 'N/A')} | "
                f"Min marks: {r.get('min_marks_pct', 'N/A')}% | "
                f"Scholarship amount: Rs. {r.get('scholarship_amount', 'varies')} | "
                f"Student pays: Rs. {r.get('student_pays', 'varies')} | "
                f"Need-based: {r.get('is_need_based', False)} | "
                f"Female only: {r.get('is_female_only', False)} | "
                f"Semester: {semester}"
            ),
            "metadata":   _metadata(r, semester=semester),
        },
    ]


GLOBAL_POLICY_CHUNKS = [
    {
        "chunk_id":   f"{SOURCE}_{SEMESTER}_policy_cgpa",
        "chunk_type": "policy",
        "topic":      SOURCE,
        "semester":   SEMESTER,
        "source":     SOURCE,
        "text": (
            "All merit-based scholarships at COMSATS University Islamabad, Sahiwal Campus "
            "are continued in subsequent semesters only if the student maintains a CGPA of "
            "3.3 out of 4.0, or as per CUI rules. If a student's CGPA drops below this "
            "threshold, the merit scholarship is discontinued. However, exactly one chance "
            "for restoration of the scholarship is allowed during the entire degree program "
            "(spanning 8 semesters). Students involved in any disciplinary matter are "
            "permanently disqualified from all types of scholarships with no exceptions."
        ),
        "metadata": {"source": SOURCE, "semester": SEMESTER, "chunk_type": "policy",
                     "topic": "cgpa_continuation_rule"},
    },
    {
        "chunk_id":   f"{SOURCE}_{SEMESTER}_policy_admission_fee",
        "chunk_type": "policy",
        "topic":      SOURCE,
        "semester":   SEMESTER,
        "source":     SOURCE,
        "text": (
            "At COMSATS University Islamabad, Sahiwal Campus, a one-time admission fee of "
            "Rs. 22,000 is charged at the time of admission for all programs. This fee is "
            "in addition to the semester fee. The admission fee is NOT charged for students "
            "admitted under Special Scholarship programs and students from the Daanish School "
            "System."
        ),
        "metadata": {"source": SOURCE, "semester": SEMESTER, "chunk_type": "policy",
                     "topic": "admission_fee"},
    },
    {
        "chunk_id":   f"{SOURCE}_{SEMESTER}_policy_validity",
        "chunk_type": "policy",
        "topic":      SOURCE,
        "semester":   SEMESTER,
        "source":     SOURCE,
        "text": (
            "The scholarship scheme described here is effective for Spring 2026 only at "
            "COMSATS University Islamabad, Sahiwal Campus. The fee structure is subject to "
            "revision at CUI, PS Islamabad at any stage. Students should verify current "
            "amounts with the Student Support Center each semester."
        ),
        "metadata": {"source": SOURCE, "semester": SEMESTER, "chunk_type": "policy",
                     "topic": "validity_disclaimer"},
    },
]
def _policy_chunks(semester: str = DEFAULT_SEMESTER) -> list[dict]:
    chunks = []
    for chunk in GLOBAL_POLICY_CHUNKS:
        policy_chunk = {**chunk, "semester": semester}
        policy_chunk["chunk_id"] = policy_chunk["chunk_id"].replace(DEFAULT_SEMESTER, semester)
        policy_chunk["metadata"] = {**chunk["metadata"], "semester": semester}
        chunks.append(policy_chunk)
    return chunks


def build_chunks(df: pd.DataFrame, semester: str = DEFAULT_SEMESTER) -> list[dict]:
    chunks = _policy_chunks(semester)
    for _, row in df.iterrows():
        r = row.where(pd.notna(row), other=None).to_dict()
        try:
            chunks.extend(_build_chunks_for_row(r, semester=semester))
        except Exception as e:
            print(f"  [WARN] Skipped sr_no={r.get('sr_no')}: {e}")

    return chunks


def build(excel_path: str = None, semester: str = DEFAULT_SEMESTER, **kwargs) -> list[dict]:
    """
    Reads scholarships data from Google Sheets and returns all chunks.
    excel_path is kept as parameter for compatibility but is ignored.
    """
    from sheets_reader import read_sheet

    df = read_sheet(
        topic      = "scholarships",
        sheet_name = "Scholarships",
        header_row = 2       # row index 2 = 3rd row = actual headers
    )

    # Clean column names
    df.columns = [c.strip().lower().replace(" ", "_").replace("\n", "_")
                  for c in df.columns]

    # Drop section separator rows — no numeric sr_no
    first_col = df.columns[0]
    df = df[pd.to_numeric(df[first_col], errors="coerce").notna()].copy()
    df = df.rename(columns={first_col: "sr_no"})

    rename = {}
    for c in df.columns:
        if "scholarship_name" in c:          rename[c] = "scholarship_name"
        elif "category"       in c:          rename[c] = "category"
        elif "funding_source" in c:          rename[c] = "funding_source"
        elif "program_type"   in c:          rename[c] = "program_type"
        elif "exam_type"      in c:          rename[c] = "exam_type"
        elif "min_marks"      in c:          rename[c] = "min_marks_pct"
        elif "total_semester" in c:          rename[c] = "total_semester_fee"
        elif "total_tuition"  in c:          rename[c] = "total_tuition_fee"
        elif "scholarship_amount" in c:      rename[c] = "scholarship_amount"
        elif "student_pays"   in c:          rename[c] = "student_pays"
        elif "need"           in c:          rename[c] = "is_need_based"
        elif "female"         in c:          rename[c] = "is_female_only"
        elif "auto"           in c:          rename[c] = "is_auto_awarded"
        elif "eligibility"    in c:          rename[c] = "eligibility_description"
        elif "notes" in c or "special" in c: rename[c] = "notes"
    df = df.rename(columns=rename)

    # Coerce numeric columns
    for col in ("sr_no", "min_marks_pct", "total_semester_fee",
                "total_tuition_fee", "scholarship_amount", "student_pays"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Coerce yes/no columns
    for col in ("is_need_based", "is_female_only", "is_auto_awarded"):
        if col in df.columns:
            df[col] = df[col].str.strip().str.lower().map(
                {"yes": True, "no": False}).fillna(False)

    return build_chunks(df, semester=semester)
