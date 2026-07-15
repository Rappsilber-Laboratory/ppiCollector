import requests


UNIPROT_ENTRY_API = "https://rest.uniprot.org/uniprotkb"


def get_uniprot_taxonomy_id(uniprot_id: str) -> str | None:
    response = requests.get(f"{UNIPROT_ENTRY_API}/{uniprot_id}.json")
    if not response.ok:
        return None

    response_json = response.json()
    organism = response_json.get("organism", {})
    taxon_id = organism.get("taxonId")
    if taxon_id is None:
        return None
    return str(taxon_id)
