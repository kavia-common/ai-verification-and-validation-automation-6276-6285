import json
import os
from typing import Any, Dict, List, Tuple

from ..utils import parse_csv_flex, utc_now_iso
from .llm_provider import get_llm
from .storage import Storage


def _infer_prompt(rows: List[Dict[str, Any]]) -> str:
    # Craft a simple prompt; in practice, include schema hints
    head = rows[:10]
    sample_lines = []
    for r in head:
        rid = r.get("requirement_id") or r.get("id") or r.get("req_id") or "UNKNOWN"
        desc = r.get("description") or r.get("requirement") or ""
        ac = r.get("acceptance_criteria") or r.get("criteria") or ""
        sample_lines.append(f"Requirement {rid}: {desc} | Criteria: {ac}")
    body = "\n".join(sample_lines) if sample_lines else "No content"
    prompt = (
        "You are a QA engineer. Based on the following SRS entries, produce a JSON object "
        'with key "test_cases": a list of items each having fields: id, title, steps[], expected.\n'
        f"{body}\nReturn only JSON."
    )
    return prompt


def _parse_llm_cases(text: str) -> Tuple[List[Dict[str, Any]], bool]:
    try:
        data = json.loads(text)
        items = data.get("test_cases") or data
        if isinstance(items, dict) and "test_cases" in items:
            items = items["test_cases"]
        if isinstance(items, list):
            cleaned = []
            for i in items:
                if not isinstance(i, dict):
                    continue
                cleaned.append(
                    {
                        "id": i.get("id") or i.get("requirement_id") or "UNKNOWN",
                        "title": i.get("title") or i.get("name") or "Untitled",
                        "steps": i.get("steps") or [],
                        "expected": i.get("expected") or i.get("expected_result") or "",
                    }
                )
            return cleaned, True
    except Exception:
        pass
    return [], False


def _deterministic_from_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Fallback: simple deterministic mapping from CSV
    cases = []
    for idx, r in enumerate(rows, start=1):
        rid = r.get("requirement_id") or r.get("id") or r.get("req_id") or f"REQ-{idx}"
        desc = r.get("description") or r.get("requirement") or "Behavior"
        ac = r.get("acceptance_criteria") or r.get("criteria") or "Should work as specified"
        cases.append(
            {
                "id": str(rid),
                "title": f"Validate: {desc[:60]}",
                "steps": [f"Step for {desc[:40]}"],
                "expected": ac[:120],
            }
        )
    if not cases:
        cases = [
            {"id": "REQ-1", "title": "Placeholder case", "steps": ["Do something"], "expected": "It works"},
        ]
    return cases


# PUBLIC_INTERFACE
def generate_test_cases_for_job(job_id: str) -> Dict[str, Any]:
    """Generate test cases JSON for the given job."""
    storage = Storage()
    job_meta = storage.load_job_metadata(job_id)
    if not job_meta:
        return {"error": "Job not found"}

    # Locate CSV file (assume single file per job)
    input_dir = storage.get_job_input_dir(job_id)
    csv_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".csv")]
    if not csv_files:
        return {"error": "No CSV found in job input"}
    csv_path = storage.safe_join(input_dir, csv_files[0])

    # Read CSV and craft prompt
    rows = parse_csv_flex(csv_path)
    prompt = _infer_prompt(rows)

    # Call LLM
    llm = get_llm()
    output = llm.generate_text(prompt)

    # Parse or fallback
    cases, ok = _parse_llm_cases(output)
    if not ok:
        cases = _deterministic_from_rows(rows)

    # Save to codebase/test-cases/<jobId>.json
    cases_path = storage.get_job_cases_path(job_id)
    os.makedirs(os.path.dirname(cases_path), exist_ok=True)
    with open(cases_path, "w") as f:
        json.dump({"jobId": job_id, "generated_at": utc_now_iso(), "test_cases": cases}, f, indent=2)

    # Update job metadata
    job_meta["status"] = "cases_generated"
    job_meta["paths"]["cases_json"] = cases_path
    job_meta["cases_count"] = len(cases)
    storage.save_job_metadata(job_id, job_meta)

    return {"jobId": job_id, "casesPath": cases_path, "count": len(cases)}
