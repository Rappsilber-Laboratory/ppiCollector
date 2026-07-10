from __future__ import annotations

import io

import pandas as pd


DEFAULT_COLUMNS = [
    "#ID(s) interactor A",
    "ID(s) interactor B",
    "Taxid interactor A",
    "Taxid interactor B",
    "Source database(s)",
]


def _build_final_columns(selected_databases: list[str], selected_columns: list[str]) -> list[str]:
    final_columns = list(DEFAULT_COLUMNS)

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


def _rows_to_mitab(rows_by_db: dict[str, list[dict]], tax_id: str, selected_databases: list[str], selected_columns: list[str]) -> str:
    final_columns = _build_final_columns(selected_databases, selected_columns)
    output_rows = []

    for db_name in selected_databases:
        for interaction in rows_by_db.get(db_name, []):
            row = _base_row(final_columns, tax_id)

            if db_name in {"BioGrid", "Predictomes", "Corum"}:
                row["#ID(s) interactor A"] = f"uniprotkb:{interaction.get('Interactor_A', '-')}"
                row["ID(s) interactor B"] = f"uniprotkb:{interaction.get('Interactor_B', '-')}"
            elif db_name == "HuRI":
                row["#ID(s) interactor A"] = f"ensembl:{interaction.get('Interactor_A', '-')}"
                row["ID(s) interactor B"] = f"ensembl:{interaction.get('Interactor_B', '-')}"

            if db_name == "BioGrid":
                row["Source database(s)"] = 'psi-mi:"MI:0463"(biogrid)'
                if "BioGrid interaction detection method(s)" in final_columns:
                    row["BioGrid interaction detection method(s)"] = interaction.get("Interaction_Detection_Method", "-")
                if "Interaction type(s)" in final_columns:
                    row["Interaction type(s)"] = interaction.get("Interaction_Type", "-")
                if "Confidence value(s)" in final_columns and "Confidence_Score" in selected_columns:
                    row["Confidence value(s)"] = f"biogrid-confidence:{interaction.get('Confidence_Score', '-')}"

            elif db_name == "Predictomes":
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
                row["Source database(s)"] = 'psi-mi:"MI:0464"(corum)'
                if "Corum complex name(s)" in final_columns:
                    row["Corum complex name(s)"] = interaction.get("complex_name", "-")
                if "Corum cell line(s)" in final_columns:
                    row["Corum cell line(s)"] = interaction.get("cell_line", "-") or "-"
                if "Corum purification method(s)" in final_columns:
                    methods = interaction.get("Purification_Method", [])
                    row["Corum purification method(s)"] = "|".join(methods) if methods else "-"

            elif db_name == "HuRI":
                row["Source database(s)"] = 'psi-mi:"MI:1237"(huri)'

            output_rows.append(row)

    tsv_lines = ["\t".join(final_columns)]
    for row in output_rows:
        tsv_lines.append("\t".join(str(row.get(col, "-")) for col in final_columns))
    return "\n".join(tsv_lines)


def _rows_to_parquet(rows_by_db: dict[str, list[dict]], selected_databases: list[str]) -> bytes:
    rows = []
    for db_name in selected_databases:
        for interaction in rows_by_db.get(db_name, []):
            temp = dict(interaction)
            temp["Database"] = db_name
            rows.append(temp)

    dataframe = pd.DataFrame(rows)
    buffer = io.BytesIO()
    dataframe.to_parquet(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


def build_species_mitab(rows_by_db: dict[str, list[dict]], tax_id: str, selected_databases: list[str], selected_columns: list[str]) -> io.StringIO:
    content = _rows_to_mitab(rows_by_db, tax_id, selected_databases, selected_columns)
    return io.StringIO(content)


def build_species_parquet(rows_by_db: dict[str, list[dict]], selected_databases: list[str]) -> io.BytesIO:
    content = _rows_to_parquet(rows_by_db, selected_databases)
    buffer = io.BytesIO(content)
    buffer.seek(0)
    return buffer
