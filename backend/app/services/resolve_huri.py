from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

import pandas as pd
import requests

from app.services.species_index import get_species_by_tax_id


URL1 = "https://rest.uniprot.org/taxonomy"

HURI_DF = pd.read_csv("../Data/HuRI/HuRI.tsv", sep="\t", header=None, names=["interactorA", "interactorB"])
HURI_INDEX: dict[str, list[str]] = defaultdict(list)

for row in HURI_DF.itertuples(index=False):
    HURI_INDEX[row.interactorA].append(row.interactorB)
    HURI_INDEX[row.interactorB].append(row.interactorA)


@lru_cache(maxsize=128)
def taxon_id_to_name(tax_id: str) -> str:
    species = get_species_by_tax_id(tax_id)
    if species is not None:
        return species["display_name"]

    tax_id_to_name_json = requests.get(f"{URL1}/{tax_id}").json()
    return tax_id_to_name_json["scientificName"]


def resolve_HuRI(input_id: str | None, tax_id: str):
    interactions = [
        {"info": {"database": "HuRI", "Input_UniProt": input_id, "organism": taxon_id_to_name(tax_id)}}
    ]

    if not input_id:
        interactions.append({"Interactors": []})
        return interactions

    interactors = []
    seen = set()
    for interactor_id in HURI_INDEX.get(input_id, []):
        if not interactor_id or interactor_id == input_id or interactor_id in seen:
            continue
        seen.add(interactor_id)
        interactors.append(
            {
                "Interactor_A": interactor_id,
                "Interactor_B": input_id,
                "Interactor_Link": f"https://interactome-atlas.org/search/{interactor_id}",
            }
        )

    interactions.append({"Interactors": interactors})
    return interactions
