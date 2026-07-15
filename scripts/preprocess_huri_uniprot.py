from __future__ import annotations

import csv
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
HURI_PATH = ROOT / "Data" / "HuRI" / "HuRI.tsv"
OUTPUT_PATH = ROOT / "Data" / "HuRI" / "HuRI_uniprot.tsv"
MAPPING_PATH = ROOT / "Data" / "HuRI" / "HuRI_ensembl_uniprot_mapping.tsv"
UNIPROT_ID_MAPPING_API = "https://rest.uniprot.org/idmapping"
POLL_INTERVAL_SECONDS = 3
REQUEST_TIMEOUT_SECONDS = 30


def read_huri_edges() -> list[tuple[str, str]]:
    edges = []
    with HURI_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row in reader:
            if len(row) < 2:
                continue
            ensembl_a = row[0].strip()
            ensembl_b = row[1].strip()
            if ensembl_a and ensembl_b:
                edges.append((ensembl_a, ensembl_b))
    return edges


def submit_mapping_job(ensembl_ids: list[str]) -> str:
    response = requests.post(
        f"{UNIPROT_ID_MAPPING_API}/run",
        data={"from": "Ensembl", "to": "UniProtKB", "ids": ",".join(ensembl_ids)},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    job_id = response.json().get("jobId")
    if not job_id:
        raise RuntimeError(f"UniProt did not return a jobId: {response.text[:500]}")
    return job_id


def wait_for_mapping_job(job_id: str) -> None:
    status_url = f"{UNIPROT_ID_MAPPING_API}/status/{job_id}"
    while True:
        response = requests.get(status_url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
        if payload.get("jobStatus") == "RUNNING":
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        if payload.get("jobStatus") in {"NEW", "PENDING"}:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        if payload.get("jobStatus") in {"FAILED", "ERROR"}:
            raise RuntimeError(f"UniProt mapping job failed: {payload}")
        return


def get_mapping_results(job_id: str) -> list[dict]:
    results = []
    next_url = f"{UNIPROT_ID_MAPPING_API}/uniprotkb/results/{job_id}?size=500"

    while next_url:
        response = requests.get(next_url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
        results.extend(payload.get("results", []))
        next_url = payload.get("next")
        if not next_url:
            link_header = response.headers.get("Link", "")
            for link_part in link_header.split(","):
                if 'rel="next"' not in link_part:
                    continue
                next_url = link_part.split(";", 1)[0].strip().strip("<>")
                break

    return results


def choose_best_mappings(results: list[dict]) -> dict[str, str]:
    mappings: dict[str, tuple[int, str]] = {}

    for result in results:
        source_id = str(result.get("from", "")).strip()
        target = result.get("to", {})
        if not source_id or not isinstance(target, dict):
            continue

        accession = target.get("primaryAccession")
        if not accession:
            continue

        entry_type = target.get("entryType", "")
        score = 0 if "reviewed" in entry_type.lower() else 1
        current = mappings.get(source_id)
        if current is None or score < current[0]:
            mappings[source_id] = (score, accession)

    return {source_id: accession for source_id, (_, accession) in mappings.items()}


def write_outputs(edges: list[tuple[str, str]], mappings: dict[str, str]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with MAPPING_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["Ensembl_Gene_ID", "UniProt_ID"])
        for ensembl_id in sorted(mappings):
            writer.writerow([ensembl_id, mappings[ensembl_id]])

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "Interactor_A_Ensembl",
                "Interactor_B_Ensembl",
                "Interactor_A_UniProt",
                "Interactor_B_UniProt",
            ]
        )
        for ensembl_a, ensembl_b in edges:
            writer.writerow([ensembl_a, ensembl_b, mappings.get(ensembl_a, ""), mappings.get(ensembl_b, "")])


def main() -> None:
    edges = read_huri_edges()
    ensembl_ids = sorted({ensembl_id for edge in edges for ensembl_id in edge})
    print(f"Read {len(edges):,} HuRI edges with {len(ensembl_ids):,} unique Ensembl IDs")

    job_id = submit_mapping_job(ensembl_ids)
    print(f"Submitted UniProt mapping job {job_id}")
    wait_for_mapping_job(job_id)
    results = get_mapping_results(job_id)
    mappings = choose_best_mappings(results)
    write_outputs(edges, mappings)

    print(f"Mapped {len(mappings):,} / {len(ensembl_ids):,} Ensembl IDs")
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {MAPPING_PATH}")


if __name__ == "__main__":
    main()
