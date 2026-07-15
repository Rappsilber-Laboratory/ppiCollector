from __future__ import annotations

import io
from typing import Iterator

import pandas as pd

from app.services.species_ppi_remote import iter_intact_species_rows, iter_string_species_rows


DEFAULT_COLUMNS = [
    "#ID(s) interactor A",
    "ID(s) interactor B",
    "Taxid interactor A",
    "Taxid interactor B",
    "Source database(s)",
]


def _build_final_columns(selected_databases: list[str], selected_columns: list[str]) -> list[str]:
    final_columns = list(DEFAULT_COLUMNS)

    if "String" in selected_databases:
        if any(
            col in selected_columns
            for col in [
                "combined_score",
                "experimental_score",
                "coexpression_score",
                "textmining_score",
                "database_score",
                "gene_neighbourhood_score",
                "gene_fusion_score",
                "phylogenetic_profile_score",
            ]
        ):
            final_columns.append("Confidence value(s)")

    if "IntAct" in selected_databases:
        if "PubMed_Ids" in selected_columns:
            final_columns.append("Publication Identifier(s)")
        if "Unique_Identification_Methods" in selected_columns:
            final_columns.append("Participant identification method(s)")
        if any(
            col in selected_columns
            for col in [
                "Interaction_Score_Intact",
                "Num_Interaction_IntAct",
                "Minimum_feature_count",
                "Maximum_feature_count",
            ]
        ) and "Confidence value(s)" not in final_columns:
            final_columns.append("Confidence value(s)")

    if "BioGrid" in selected_databases:
        if "Interaction_Detection_Method" in selected_columns:
            final_columns.append("BioGrid interaction detection method(s)")
        if "Interaction_Type" in selected_columns:
            final_columns.append("Interaction type(s)")
        if "Confidence_Score" in selected_columns and "Confidence value(s)" not in final_columns:
            final_columns.append("Confidence value(s)")

    if "Predictomes" in selected_databases:
        if any(col in selected_columns for col in ["spoc_score", "kirc_score", "num_unique_contacts"]):
            if "Confidence value(s)" not in final_columns:
                final_columns.append("Confidence value(s)")

    if "Corum" in selected_databases:
        if "complex_name" in selected_columns:
            final_columns.append("Corum complex name(s)")
        if "cell_line" in selected_columns:
            final_columns.append("Corum cell line(s)")
        if "Purification_Method" in selected_columns:
            final_columns.append("Corum purification method(s)")

    return final_columns


def _base_row(final_columns: list[str], tax_id: str) -> dict:
    row = {column: "-" for column in final_columns}
    row["Taxid interactor A"] = f"taxid:{tax_id}"
    row["Taxid interactor B"] = f"taxid:{tax_id}"
    return row


def _iter_species_rows(db_name: str, db_data) -> Iterator[dict]:
    if isinstance(db_data, dict):
        if db_data.get("kind") == "string_species_bundle":
            yield from iter_string_species_rows(db_data)
            return
        if db_data.get("kind") == "intact_species_bundle":
            yield from iter_intact_species_rows(db_data)
            return

    for row in db_data or []:
        yield row


def _format_interactor(interaction: dict, side: str, fallback_prefix: str) -> str:
    value = interaction.get(f"Interactor_{side}") or "-"
    prefix = interaction.get(f"Interactor_{side}_Prefix", fallback_prefix)
    return f"{prefix}:{value}"


def _rows_to_mitab(rows_by_db: dict[str, list[dict] | dict], tax_id: str, selected_databases: list[str], selected_columns: list[str]) -> str:
    final_columns = _build_final_columns(selected_databases, selected_columns)
    output_rows = []

    for db_name in selected_databases:
        for interaction in _iter_species_rows(db_name, rows_by_db.get(db_name, [])):
            row = _base_row(final_columns, tax_id)

            if db_name == "String":
                row["#ID(s) interactor A"] = _format_interactor(interaction, "A", "stringdb")
                row["ID(s) interactor B"] = _format_interactor(interaction, "B", "stringdb")
                row["Source database(s)"] = 'psi-mi:"MI:1201"(string)'
                if "Confidence value(s)" in final_columns:
                    scores = []
                    if "combined_score" in selected_columns:
                        scores.append(f"string-score:{interaction.get('combined_score', '-')}")
                    if "experimental_score" in selected_columns:
                        scores.append(f"string-experimental-score:{interaction.get('experimental_score', '-')}")
                    if "coexpression_score" in selected_columns:
                        scores.append(f"string-coexpression-score:{interaction.get('coexpression_score', '-')}")
                    if "textmining_score" in selected_columns:
                        scores.append(f"string-textmining-score:{interaction.get('textmining_score', '-')}")
                    if "database_score" in selected_columns:
                        scores.append(f"string-database-score:{interaction.get('database_score', '-')}")
                    if "gene_neighbourhood_score" in selected_columns:
                        scores.append(f"string-gene-neighbourhood-score:{interaction.get('gene_neighbourhood_score', '-')}")
                    if "gene_fusion_score" in selected_columns:
                        scores.append(f"string-gene-fusion-score:{interaction.get('gene_fusion_score', '-')}")
                    if "phylogenetic_profile_score" in selected_columns:
                        scores.append(f"string-phylogenetic-profile-score:{interaction.get('phylogenetic_profile_score', '-')}")
                    if scores:
                        row["Confidence value(s)"] = "|".join(scores)

            elif db_name == "IntAct":
                row["#ID(s) interactor A"] = _format_interactor(interaction, "A", "uniprotkb")
                row["ID(s) interactor B"] = _format_interactor(interaction, "B", "uniprotkb")
                row["Source database(s)"] = 'psi-mi:"MI:0469"(intact)'
                taxid_a = interaction.get("Taxid_A")
                taxid_b = interaction.get("Taxid_B")
                if taxid_a:
                    row["Taxid interactor A"] = f"taxid:{taxid_a}"
                if taxid_b:
                    row["Taxid interactor B"] = f"taxid:{taxid_b}"
                if "Publication Identifier(s)" in final_columns:
                    identifiers = interaction.get("PubMed_Ids", [])
                    row["Publication Identifier(s)"] = "|".join(identifiers) if identifiers else "-"
                if "Participant identification method(s)" in final_columns:
                    methods = interaction.get("Unique_Identification_Methods", [])
                    row["Participant identification method(s)"] = "|".join(methods) if methods else "-"
                if "Confidence value(s)" in final_columns:
                    scores = []
                    if "Interaction_Score_Intact" in selected_columns and interaction.get("Interaction_Score_Intact"):
                        scores.append(f"intact-miscore:{interaction.get('Interaction_Score_Intact', '-')}")
                    if "Num_Interaction_IntAct" in selected_columns:
                        scores.append(f"intact-interaction-count:{interaction.get('Num_Interaction_IntAct', '-')}")
                    if "Minimum_feature_count" in selected_columns:
                        scores.append(f"minimum-feature-count:{interaction.get('Minimum_feature_count', '-')}")
                    if "Maximum_feature_count" in selected_columns:
                        scores.append(f"maximum-feature-count:{interaction.get('Maximum_feature_count', '-')}")
                    if scores:
                        row["Confidence value(s)"] = "|".join(scores)

            elif db_name == "BioGrid":
                row["#ID(s) interactor A"] = f"uniprotkb:{interaction.get('Interactor_A', '-')}"
                row["ID(s) interactor B"] = f"uniprotkb:{interaction.get('Interactor_B', '-')}"
                row["Source database(s)"] = 'psi-mi:"MI:0463"(biogrid)'
                if "BioGrid interaction detection method(s)" in final_columns:
                    row["BioGrid interaction detection method(s)"] = interaction.get("Interaction_Detection_Method", "-")
                if "Interaction type(s)" in final_columns:
                    row["Interaction type(s)"] = interaction.get("Interaction_Type", "-")
                if "Confidence value(s)" in final_columns and "Confidence_Score" in selected_columns:
                    row["Confidence value(s)"] = f"biogrid-confidence:{interaction.get('Confidence_Score', '-')}"

            elif db_name == "Predictomes":
                row["#ID(s) interactor A"] = f"uniprotkb:{interaction.get('Interactor_A', '-')}"
                row["ID(s) interactor B"] = f"uniprotkb:{interaction.get('Interactor_B', '-')}"
                row["Source database(s)"] = "predictomes"
                if "Confidence value(s)" in final_columns:
                    scores = []
                    if "spoc_score" in selected_columns:
                        scores.append(f"spoc-score:{interaction.get('spoc_score', '-')}")
                    if "kirc_score" in selected_columns:
                        scores.append(f"kirc-score:{interaction.get('kirc_score', '-')}")
                    if "num_unique_contacts" in selected_columns:
                        scores.append(f"unique-contacts:{interaction.get('num_unique_contacts', '-')}")
                    if scores:
                        row["Confidence value(s)"] = "|".join(scores)

            elif db_name == "Corum":
                row["#ID(s) interactor A"] = f"uniprotkb:{interaction.get('Interactor_A', '-')}"
                row["ID(s) interactor B"] = f"uniprotkb:{interaction.get('Interactor_B', '-')}"
                row["Source database(s)"] = 'psi-mi:"MI:0464"(corum)'
                if "Corum complex name(s)" in final_columns:
                    row["Corum complex name(s)"] = interaction.get("complex_name", "-")
                if "Corum cell line(s)" in final_columns:
                    row["Corum cell line(s)"] = interaction.get("cell_line", "-") or "-"
                if "Corum purification method(s)" in final_columns:
                    methods = interaction.get("Purification_Method", [])
                    row["Corum purification method(s)"] = "|".join(methods) if methods else "-"

            elif db_name == "HuRI":
                interactor_a_uniprot = interaction.get("Interactor_A_UniProt")
                interactor_b_uniprot = interaction.get("Interactor_B_UniProt")
                interactor_a_ensembl = interaction.get("Interactor_A_Ensembl")
                interactor_b_ensembl = interaction.get("Interactor_B_Ensembl")
                row["#ID(s) interactor A"] = (
                    f"uniprotkb:{interactor_a_uniprot}"
                    if interactor_a_uniprot
                    else f"ensembl:{interactor_a_ensembl or interaction.get('Interactor_A', '-')}"
                )
                row["ID(s) interactor B"] = (
                    f"uniprotkb:{interactor_b_uniprot}"
                    if interactor_b_uniprot
                    else f"ensembl:{interactor_b_ensembl or interaction.get('Interactor_B', '-')}"
                )
                row["Source database(s)"] = 'psi-mi:"MI:1237"(huri)'

            output_rows.append(row)

    tsv_lines = ["\t".join(final_columns)]
    for row in output_rows:
        tsv_lines.append("\t".join(str(row.get(col, "-")) for col in final_columns))
    return "\n".join(tsv_lines)


def _rows_to_parquet(rows_by_db: dict[str, list[dict] | dict], selected_databases: list[str]) -> bytes:
    rows = []
    for db_name in selected_databases:
        for interaction in _iter_species_rows(db_name, rows_by_db.get(db_name, [])):
            temp = dict(interaction)
            temp["Database"] = db_name
            rows.append(temp)

    dataframe = pd.DataFrame(rows)
    buffer = io.BytesIO()
    dataframe.to_parquet(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


def build_species_mitab(rows_by_db: dict[str, list[dict] | dict], tax_id: str, selected_databases: list[str], selected_columns: list[str]) -> io.StringIO:
    content = _rows_to_mitab(rows_by_db, tax_id, selected_databases, selected_columns)
    return io.StringIO(content)


def build_species_parquet(rows_by_db: dict[str, list[dict] | dict], selected_databases: list[str]) -> io.BytesIO:
    content = _rows_to_parquet(rows_by_db, selected_databases)
    buffer = io.BytesIO(content)
    buffer.seek(0)
    return buffer
