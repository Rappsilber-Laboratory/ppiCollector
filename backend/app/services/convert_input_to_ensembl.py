from functools import lru_cache

import requests


UNIPROT_ENTRY_API = "https://rest.uniprot.org/uniprotkb"


@lru_cache(maxsize=2048)
def convert_to_ensemble(input_id: str):
    try:
        response = requests.get(f"{UNIPROT_ENTRY_API}/{input_id}.json")
    except requests.RequestException:
        return None

    if not response.ok:
        return None

    response_json = response.json()
    for reference in response_json.get("uniProtKBCrossReferences", []):
        if reference.get("database") != "Ensembl":
            continue

        reference_id = reference.get("id")
        if isinstance(reference_id, str) and reference_id.startswith("ENSG"):
            return reference_id

        for prop in reference.get("properties", []):
            value = prop.get("value")
            if isinstance(value, str) and value.startswith("ENSG"):
                return value

    return None
