from __future__ import annotations

import csv
import gzip
import io
from functools import lru_cache
from pathlib import Path
import zipfile
from typing import Callable, Iterator

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_ROOT = PROJECT_ROOT / "Data" / "SpeciesPPICache"
STRING_CACHE_DIR = CACHE_ROOT / "String" / "v12.0"
INTACT_CACHE_DIR = CACHE_ROOT / "IntAct" / "current" / "psimitab" / "species"

STRING_LINKS_URL_TEMPLATE = "https://stringdb-downloads.org/download/protein.links.full.v12.0/{tax_id}.protein.links.full.v12.0.txt.gz"
STRING_INFO_URL_TEMPLATE = "https://stringdb-downloads.org/download/protein.info.v12.0/{tax_id}.protein.info.v12.0.txt.gz"
STRING_ALIASES_URL_TEMPLATE = "https://stringdb-downloads.org/download/protein.aliases.v12.0/{tax_id}.protein.aliases.v12.0.txt.gz"
INTACT_SPECIES_URL_TEMPLATE = "https://ftp.ebi.ac.uk/pub/databases/intact/current/psimitab/species/{filename}.zip"

INTACT_FILENAME_BY_TAX_ID = {
    "9606": "human",
    "559292": "yeast",
    "7227": "drome",
    "6239": "caeel",
    "3702": "arath",
    "10090": "mouse",
    "83333": "ecoli",
    "192222": "camje",
    "10116": "rat",
    "243276": "trepa",
    "1111708": "syny3",
    "36329": "plaf7",
    "85962": "helpy",
    "284812": "schpo",
    "224308": "bacsu",
    "2697049": "SARS-CoV-2",
}


class SpeciesJobCancelled(Exception):
    pass


class SpeciesRemoteDataNotFound(Exception):
    pass


def _check_cancel(cancel_requested: Callable[[], bool] | None) -> None:
    if cancel_requested and cancel_requested():
        raise SpeciesJobCancelled("Species PPI job was cancelled")


def _download_to_cache(url: str, destination: Path, cancel_requested: Callable[[], bool] | None = None) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".part")
    if temp_path.exists():
        temp_path.unlink()

    try:
        with requests.get(url, stream=True, timeout=120) as response:
            if response.status_code == 404:
                raise SpeciesRemoteDataNotFound(f"Remote species file was not found: {url}")
            response.raise_for_status()
            with temp_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    _check_cancel(cancel_requested)
                    if chunk:
                        handle.write(chunk)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

    temp_path.replace(destination)


def _count_gzip_lines(path: str) -> int:
    line_count = 0
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        next(handle, None)
        for _ in handle:
            line_count += 1
    return line_count


def _count_intact_zip_rows(path: str) -> int:
    with zipfile.ZipFile(path) as archive:
        file_name = archive.namelist()[0]
        with archive.open(file_name) as handle:
            line_count = 0
            for raw_line in handle:
                line = raw_line.decode("utf-8").rstrip("\n")
                if not line:
                    continue
                line_count += 1
    return max(0, line_count - 1)


def ensure_string_species_bundle(tax_id: str, cancel_requested: Callable[[], bool] | None = None) -> dict:
    links_path = STRING_CACHE_DIR / f"{tax_id}.protein.links.full.v12.0.txt.gz"
    info_path = STRING_CACHE_DIR / f"{tax_id}.protein.info.v12.0.txt.gz"
    aliases_path = STRING_CACHE_DIR / f"{tax_id}.protein.aliases.v12.0.txt.gz"

    _download_to_cache(STRING_LINKS_URL_TEMPLATE.format(tax_id=tax_id), links_path, cancel_requested)
    _check_cancel(cancel_requested)
    _download_to_cache(STRING_INFO_URL_TEMPLATE.format(tax_id=tax_id), info_path, cancel_requested)
    _check_cancel(cancel_requested)
    _download_to_cache(STRING_ALIASES_URL_TEMPLATE.format(tax_id=tax_id), aliases_path, cancel_requested)
    _check_cancel(cancel_requested)

    return {
        "kind": "string_species_bundle",
        "tax_id": tax_id,
        "links_path": str(links_path),
        "info_path": str(info_path),
        "aliases_path": str(aliases_path),
        "pair_count": _count_gzip_lines(str(links_path)),
    }


def ensure_intact_species_bundle(tax_id: str, cancel_requested: Callable[[], bool] | None = None) -> dict:
    filename = INTACT_FILENAME_BY_TAX_ID.get(tax_id)
    if not filename:
        raise FileNotFoundError(f"No IntAct species archive is configured for taxonomy ID {tax_id}")

    zip_path = INTACT_CACHE_DIR / f"{filename}.zip"
    _download_to_cache(INTACT_SPECIES_URL_TEMPLATE.format(filename=filename), zip_path, cancel_requested)
    _check_cancel(cancel_requested)

    return {
        "kind": "intact_species_bundle",
        "tax_id": tax_id,
        "filename": filename,
        "zip_path": str(zip_path),
        "pair_count": _count_intact_zip_rows(str(zip_path)),
    }


def _extract_first_token(raw_value: str, preferred_prefix: str | None = None) -> tuple[str, str] | tuple[None, None]:
    for token in (raw_value or "").split("|"):
        token = token.strip()
        if not token:
            continue
        if preferred_prefix and token.startswith(preferred_prefix):
            prefix, value = token.split(":", 1)
            return prefix, value
    token = (raw_value or "").split("|")[0].strip()
    if not token or ":" not in token:
        return None, None
    prefix, value = token.split(":", 1)
    return prefix, value


def _extract_gene_name_from_aliases(raw_value: str) -> str | None:
    for token in (raw_value or "").split("|"):
        if "(gene name)" in token and ":" in token:
            return token.split(":", 1)[1].split("(", 1)[0]
    for token in (raw_value or "").split("|"):
        if "(display_short)" in token and ":" in token:
            return token.split(":", 1)[1].split("(", 1)[0]
    return None


def _extract_display_name(raw_value: str) -> str:
    if raw_value.startswith('psi-mi:"') and "(" in raw_value and raw_value.endswith(")"):
        return raw_value.split("(", 1)[1][:-1]
    return raw_value


def _extract_confidence_value(raw_value: str, prefix: str) -> str | None:
    for token in (raw_value or "").split("|"):
        if token.startswith(prefix):
            return token.split(":", 1)[1]
    return None


def _feature_count(raw_value: str) -> int:
    if not raw_value or raw_value == "-":
        return 0
    return sum(1 for token in raw_value.split("|") if token and token != "-")


@lru_cache(maxsize=16)
def _load_string_metadata(info_path: str, aliases_path: str) -> dict[str, dict]:
    metadata: dict[str, dict] = {}

    with gzip.open(info_path, "rt", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            string_id = row["#string_protein_id"]
            metadata[string_id] = {
                "preferred_name": row.get("preferred_name") or None,
                "annotation": row.get("annotation") or None,
                "uniprot_ac": None,
                "gene_name": row.get("preferred_name") or None,
            }

    with gzip.open(aliases_path, "rt", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            string_id = row["#string_protein_id"]
            entry = metadata.setdefault(
                string_id,
                {"preferred_name": None, "annotation": None, "uniprot_ac": None, "gene_name": None},
            )
            source = row.get("source") or ""
            alias = row.get("alias") or ""

            if source == "UniProt_AC" and not entry["uniprot_ac"]:
                entry["uniprot_ac"] = alias
            elif source == "UniProt_GN_Name" and not entry["gene_name"]:
                entry["gene_name"] = alias
            elif source == "UniProt_GN_OrderedLocusNames" and not entry["gene_name"]:
                entry["gene_name"] = alias

    return metadata


def iter_string_species_rows(bundle: dict) -> Iterator[dict]:
    metadata = _load_string_metadata(bundle["info_path"], bundle["aliases_path"])

    with gzip.open(bundle["links_path"], "rt", encoding="utf-8") as handle:
        header = next(handle).strip().split()
        for line in handle:
            parts = line.strip().split()
            if len(parts) != len(header):
                continue
            row = dict(zip(header, parts))

            string_id_a = row["protein1"]
            string_id_b = row["protein2"]
            info_a = metadata.get(string_id_a, {})
            info_b = metadata.get(string_id_b, {})
            uniprot_a = info_a.get("uniprot_ac")
            uniprot_b = info_b.get("uniprot_ac")

            yield {
                "Database": "String",
                "String_Id_A": string_id_a,
                "String_Id_B": string_id_b,
                "Interactor_A": uniprot_a or string_id_a,
                "Interactor_B": uniprot_b or string_id_b,
                "Interactor_A_Prefix": "uniprotkb" if uniprot_a else "stringdb",
                "Interactor_B_Prefix": "uniprotkb" if uniprot_b else "stringdb",
                "Interactor_Gene_Name_A": info_a.get("gene_name") or info_a.get("preferred_name"),
                "Interactor_Gene_Name_B": info_b.get("gene_name") or info_b.get("preferred_name"),
                "preferred_name_A": info_a.get("preferred_name"),
                "preferred_name_B": info_b.get("preferred_name"),
                "annotation_A": info_a.get("annotation"),
                "annotation_B": info_b.get("annotation"),
                "combined_score": row.get("combined_score"),
                "gene_neighbourhood_score": row.get("neighborhood"),
                "gene_fusion_score": row.get("fusion"),
                "phylogenetic_profile_score": row.get("cooccurence"),
                "experimental_score": row.get("experiments"),
                "coexpression_score": row.get("coexpression"),
                "textmining_score": row.get("textmining"),
                "database_score": row.get("database"),
            }


def iter_intact_species_rows(bundle: dict) -> Iterator[dict]:
    with zipfile.ZipFile(bundle["zip_path"]) as archive:
        file_name = archive.namelist()[0]
        with archive.open(file_name) as raw_handle:
            text_handle = io.TextIOWrapper(raw_handle, encoding="utf-8")
            reader = csv.DictReader(text_handle, delimiter="\t")
            for row in reader:
                prefix_a, interactor_a = _extract_first_token(row.get("#ID(s) interactor A", ""), "uniprotkb:")
                prefix_b, interactor_b = _extract_first_token(row.get("ID(s) interactor B", ""), "uniprotkb:")
                if not interactor_a or not interactor_b:
                    continue

                methods = [
                    _extract_display_name(token)
                    for token in (row.get("Interaction detection method(s)") or "").split("|")
                    if token and token != "-"
                ]
                publication_ids = [
                    token for token in (row.get("Publication Identifier(s)") or "").split("|") if token and token != "-"
                ]
                tax_id_a = _extract_first_token(row.get("Taxid interactor A", ""), "taxid:")[1]
                tax_id_b = _extract_first_token(row.get("Taxid interactor B", ""), "taxid:")[1]

                yield {
                    "Database": "IntAct",
                    "Interactor_A": interactor_a,
                    "Interactor_B": interactor_b,
                    "Interactor_A_Prefix": prefix_a or "uniprotkb",
                    "Interactor_B_Prefix": prefix_b or "uniprotkb",
                    "Interactor_Gene_Name_A": _extract_gene_name_from_aliases(row.get("Alias(es) interactor A", "")),
                    "Interactor_Gene_Name_B": _extract_gene_name_from_aliases(row.get("Alias(es) interactor B", "")),
                    "Taxid_A": tax_id_a,
                    "Taxid_B": tax_id_b,
                    "Unique_Identification_Methods": methods,
                    "PubMed_Ids": publication_ids,
                    "Interaction_Score_Intact": _extract_confidence_value(row.get("Confidence value(s)", ""), "intact-miscore"),
                    "Num_Interaction_IntAct": 1,
                    "Minimum_feature_count": min(
                        _feature_count(row.get("Feature(s) interactor A", "")),
                        _feature_count(row.get("Feature(s) interactor B", "")),
                    ),
                    "Maximum_feature_count": max(
                        _feature_count(row.get("Feature(s) interactor A", "")),
                        _feature_count(row.get("Feature(s) interactor B", "")),
                    ),
                    "Interaction_Type": _extract_display_name(row.get("Interaction type(s)") or "-"),
                    "Source_Database": row.get("Source database(s)"),
                    "Publication_Identifiers_Raw": row.get("Publication Identifier(s)"),
                }
