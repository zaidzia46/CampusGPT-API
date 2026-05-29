import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path so chunk files can import sheets_reader
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "rag_pipeline"))

from rag_pipeline import announcements_chunks, blocks_chunks, faculty_chunks, scholarships_chunks, fees_chunks, basic_info_chunks

CHUNKS_DIR = ROOT / "UNIdata" / "chunks"

SOURCES = [
    ("scholarships", scholarships_chunks, "scholarships_{semester}.xlsx"),
    ("basic_info",   basic_info_chunks,   "basic_info_{semester}.xlsx"),
    ("fees",         fees_chunks,         "fee_structure_{semester}.xlsx"),
    ("blocks_directory", blocks_chunks, "blocks_directory_{semester}.xlsx"),
    ("faculty_directory", faculty_chunks, "faculty_directory_{semester}.xlsx"),
    ("announcements",  announcements_chunks,  None),  
]

def generate(semester: str, topic: str = None) -> dict:
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = []
    errors     = []
    log_lines  = []

    for source_name, module, file_pattern in SOURCES:
        if topic and source_name != topic:
            continue

        # announcements reads from DB, not a file
        if file_pattern is None:
            source_file = None
        else:
            source_file = ROOT / "UNIdata" / file_pattern.format(semester=semester)

        log_lines.append(f"[BUILD] {source_name} ...")

        try:
            chunks = module.build(str(source_file) if source_file else None, semester=semester)
            all_chunks.extend(chunks)
            log_lines.append(f"{len(chunks)} chunks generated from {source_name}")
        except Exception as e:
            errors.append(f"{source_name}: {e}")
            log_lines.append(f"[ERROR] {source_name}: {e}")

    if not all_chunks:
        return {
            "success": False,
            "errors":  errors,
            "log":     log_lines,
        }

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "semester":     semester,
        "total_chunks": len(all_chunks),
        "chunks":       all_chunks,
    }

    out_path = CHUNKS_DIR / f"chunks_{semester}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Build summary
    by_type = {}
    for c in all_chunks:
        t = c["chunk_type"]
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "success":      True,
        "semester":     semester,
        "total_chunks": len(all_chunks),
        "by_type":      by_type,
        "errors":       errors,
        "log":          log_lines,
    }