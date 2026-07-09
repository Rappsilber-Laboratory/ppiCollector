from __future__ import annotations

from collections import defaultdict

import pandas as pd


PREDICTOMES_DF = pd.read_csv("../Data/Predictomes/Predictomes.csv")
PREDICTOMES_INDEX: dict[str, list[dict]] = defaultdict(list)

for row in PREDICTOMES_DF.itertuples(index=False):
    interaction = row.uniprot_ids.split(":")
    if len(interaction) != 2:
        continue

    uniprot_a = interaction[0].strip()
    uniprot_b = interaction[1].strip()
    entry_ab = {
        "Interactor_A": uniprot_b,
        "Interactor_B": uniprot_a,
        "spoc_score": float(row.spoc_score),
        "kirc_score": float(row.kirc_score),
        "num_unique_contacts": int(row.num_unique_contacts),
        "Interactor_Link": f"https://predictomes.org/hp/?pid={uniprot_b}",
    }
    entry_ba = {
        "Interactor_A": uniprot_a,
        "Interactor_B": uniprot_b,
        "spoc_score": float(row.spoc_score),
        "kirc_score": float(row.kirc_score),
        "num_unique_contacts": int(row.num_unique_contacts),
        "Interactor_Link": f"https://predictomes.org/hp/?pid={uniprot_a}",
    }
    PREDICTOMES_INDEX[uniprot_a].append(entry_ab)
    PREDICTOMES_INDEX[uniprot_b].append(entry_ba)


def resolve_predictomes(input_id: str, tax_id: str):
    interactions = [{"info": {"database": "Predictomes", "Input_UniProt": input_id, "organism": "Human"}}]

    interactors_list = sorted(
        [item for item in PREDICTOMES_INDEX.get(input_id, []) if item["spoc_score"] > 0.0],
        key=lambda item: item["spoc_score"],
        reverse=True,
    )

    if len(interactors_list) == 0:
        return "The input doesn't exist on Predictomes"

    interactions.append({"Interactors": interactors_list})
    return interactions
