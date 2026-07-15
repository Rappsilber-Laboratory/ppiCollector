import requests


UNIPROT_SEARCH_API = "https://rest.uniprot.org/uniprotkb/search"


def _extract_gene_names(entry: dict) -> list[str]:
    names = []
    for gene in entry.get("genes", []):
        gene_name = gene.get("geneName", {}).get("value")
        if gene_name:
            names.append(gene_name)
        for synonym in gene.get("synonyms", []):
            value = synonym.get("value")
            if value:
                names.append(value)
    return list(dict.fromkeys(names))


def _extract_protein_name(entry: dict) -> str:
    protein = entry.get("proteinDescription", {})

    recommended = protein.get("recommendedName", {})
    full_name = recommended.get("fullName", {}).get("value")
    if full_name:
        return full_name

    submission = protein.get("submissionNames", [])
    for item in submission:
        value = item.get("fullName", {}).get("value")
        if value:
            return value

    alternatives = protein.get("alternativeNames", [])
    for item in alternatives:
        value = item.get("fullName", {}).get("value")
        if value:
            return value

    return ""


def search_gene_name_candidates(gene_name: str, tax_id: str, limit: int = 8) -> list[dict]:
    params = {
        "query": f"(gene:{gene_name}) AND (organism_id:{tax_id})",
        "format": "json",
        "size": limit,
        "fields": "accession,gene_names,protein_name,organism_name,reviewed",
    }
    response = requests.get(UNIPROT_SEARCH_API, params=params)
    response.raise_for_status()

    results = []
    for entry in response.json().get("results", []):
        organism = entry.get("organism", {})
        accession = entry.get("primaryAccession")
        if not accession:
            continue

        entry_type = entry.get("entryType", "")
        results.append(
            {
                "primary_accession": accession,
                "gene_names": _extract_gene_names(entry),
                "protein_name": _extract_protein_name(entry),
                "organism_name": organism.get("scientificName", ""),
                "tax_id": str(organism.get("taxonId", tax_id)),
                "reviewed": "reviewed" in entry_type.lower() or "swiss-prot" in entry_type.lower(),
                "entry_type": entry_type,
            }
        )

    results.sort(
        key=lambda item: (
            0 if gene_name.upper() in {name.upper() for name in item["gene_names"]} else 1,
            0 if item["reviewed"] else 1,
            item["primary_accession"],
        )
    )
    return results
