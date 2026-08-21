import json
import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import app


CASES_PATH = Path(__file__).with_name("cases.json")
RESULTS_PATH = Path(__file__).with_name("results.json")


def main() -> None:
    os.environ.setdefault("LLM_STUB", "1")
    client = TestClient(app)
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    failures = []
    matches = 0
    for case in cases:
        response = client.post("/triage", json={"text": case["input"]})
        payload = response.json()
        actual = payload.get("category")
        expected = case["expected_category"]
        if response.status_code == 200 and actual == expected:
            matches += 1
        else:
            failures.append(
                {
                    "name": case["name"],
                    "expected_category": expected,
                    "actual_category": actual,
                    "status_code": response.status_code,
                }
            )

    result = {
        "prompt_version": "triage-v1",
        "mode": "stub" if os.getenv("LLM_STUB") == "1" else "provider",
        "matched": matches,
        "total": len(cases),
        "score_percent": round(matches / len(cases) * 100, 2),
        "failures": failures,
    }
    RESULTS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{matches}/{len(cases)} matched on category ({result['score_percent']}%)")
    if failures:
        print("Failures:")
        for failure in failures:
            print(
                f"- {failure['name']}: expected {failure['expected_category']}, "
                f"got {failure['actual_category']}"
            )


if __name__ == "__main__":
    main()
