import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
REPO_SEQUENCE = [
    "dpo-ledger-tools",
    "dpo-casework",
    "dpo-admin-tools",
    "dpo-integrations",
    "dpo-automation-suite",
    "dpo-interview-suite",
    "docassemble-dpolawstack",
]


def extract_evidence_from_notebook(notebook_json):
    for cell in notebook_json.get("cells", []):
        outputs = cell.get("outputs", [])
        for output in outputs:
            text_blob = output.get("text", [])
            if not text_blob:
                continue
            body = "".join(text_blob) if isinstance(text_blob, list) else str(text_blob)
            try:
                start = body.find("{")
                if start == -1:
                    continue
                json_text = body[start:]
                evidence = json.loads(json_text)
                if {"repo_name", "gate_a_status", "gate_b_status", "approval_decision"}.issubset(evidence):
                    return evidence
            except json.JSONDecodeError:
                continue
    raise ValueError("No valid evidence JSON found in notebook output.")


def run_repo_gate(repo_name):
    repo_dir = REPO_ROOT / repo_name
    notebook_name = next((p.name for p in repo_dir.iterdir() if "production_readiness" in p.name and p.suffix == ".ipynb"), None)

    if notebook_name is None:
        raise FileNotFoundError(f"No production readiness notebook found in {repo_name}")

    notebook_path = repo_dir / notebook_name
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook does not exist: {notebook_path}")

    import subprocess

    result = subprocess.run(
        [
            "python",
            "-m",
            "nbconvert",
            "--execute",
            "--to",
            "notebook",
            "--inplace",
            str(notebook_path),
        ],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Notebook execution failed for {repo_name}:\n{result.stderr or result.stdout}")

    notebook_payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    evidence = extract_evidence_from_notebook(notebook_payload)

    required = [
        evidence.get("gate_a_status") == "PASS",
        evidence.get("gate_b_status") == "PASS",
        evidence.get("approval_decision") == "APPROVE",
    ]

    if not all(required):
        raise RuntimeError(f"Repo {repo_name} did not pass governance gates: {evidence}")

    return evidence


def run_batch():
    results = {}
    for repo_name in REPO_SEQUENCE:
        repo_dir = REPO_ROOT / repo_name
        if not repo_dir.exists():
            raise FileNotFoundError(f"Missing repo directory: {repo_name}")
        evidence = run_repo_gate(repo_name)
        results[repo_name] = evidence
    return results


if __name__ == "__main__":
    batch_results = run_batch()
    print(json.dumps(batch_results, indent=2, sort_keys=True))
