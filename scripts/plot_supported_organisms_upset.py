
from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec


DATABASE_FILES = {
    "STRING": "AllSpeciesString.csv",
    "BioGRID": "AllSpeciesBioGrid.csv",
    "IntAct": "AllSpeciesIntact.csv",
    "CORUM": "AllSpeciesCorum.csv",
    "HuRI": "AllSpeciesHuRI.csv",
    "Predictomes": "AllSpeciesPredictomes.csv",
}


def read_taxon_ids(path: Path) -> set[str]:
    df = pd.read_csv(path, dtype=str)
    taxon_columns = [column for column in df.columns if column.lower() == "taxon_id"]
    if not taxon_columns:
        raise ValueError(f"No Taxon_id column found in {path}")

    taxon_column = taxon_columns[0]
    return {
        value
        for value in df[taxon_column].dropna().astype(str).str.strip()
        if value
    }


def build_memberships(supported_dir: Path) -> tuple[dict[str, set[str]], dict[str, tuple[str, ...]]]:
    database_taxa = {
        database: read_taxon_ids(supported_dir / filename)
        for database, filename in DATABASE_FILES.items()
    }

    taxon_memberships: dict[str, tuple[str, ...]] = {}
    for database, taxon_ids in database_taxa.items():
        for taxon_id in taxon_ids:
            current = list(taxon_memberships.get(taxon_id, ()))
            current.append(database)
            taxon_memberships[taxon_id] = tuple(
                database_name for database_name in DATABASE_FILES if database_name in current
            )

    return database_taxa, taxon_memberships


def write_summary(
    database_taxa: dict[str, set[str]],
    taxon_memberships: dict[str, tuple[str, ...]],
    output_prefix: Path,
) -> None:
    set_summary = output_prefix.with_suffix(".set_sizes.tsv")
    with set_summary.open("w", encoding="utf-8") as handle:
        handle.write("database\tsupported_organisms\n")
        for database in DATABASE_FILES:
            handle.write(f"{database}\t{len(database_taxa[database])}\n")
        handle.write(f"Union\t{len(taxon_memberships)}\n")

    intersection_counts: dict[tuple[str, ...], int] = {}
    for membership in taxon_memberships.values():
        intersection_counts[membership] = intersection_counts.get(membership, 0) + 1

    intersection_summary = output_prefix.with_suffix(".intersections.tsv")
    with intersection_summary.open("w", encoding="utf-8") as handle:
        handle.write("membership\tsupported_organisms\n")
        for membership, count in sorted(
            intersection_counts.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            handle.write(f"{'+'.join(membership)}\t{count}\n")


def make_plot(taxon_memberships: dict[str, tuple[str, ...]], output_prefix: Path) -> None:
    intersection_counts: dict[tuple[str, ...], int] = {}
    for membership in taxon_memberships.values():
        intersection_counts[membership] = intersection_counts.get(membership, 0) + 1

    intersections = sorted(
        intersection_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    databases = list(DATABASE_FILES)
    set_sizes = {
        database: sum(database in membership for membership in taxon_memberships.values())
        for database in databases
    }

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )

    teal = "#2f6f73"
    grey = "#d8dee2"
    dark = "#172026"
    x_positions = list(range(len(intersections)))

    figure = plt.figure(figsize=(8.2, 5.2), constrained_layout=False)
    grid = GridSpec(
        nrows=2,
        ncols=2,
        figure=figure,
        width_ratios=[1.9, 5.0],
        height_ratios=[3.0, 2.0],
        hspace=0.04,
        wspace=0.04,
    )
    ax_empty = figure.add_subplot(grid[0, 0])
    ax_bars = figure.add_subplot(grid[0, 1])
    ax_sets = figure.add_subplot(grid[1, 0])
    ax_matrix = figure.add_subplot(grid[1, 1])

    ax_empty.axis("off")

    counts = [count for _, count in intersections]
    ax_bars.bar(x_positions, counts, color=teal, width=0.72)
    ax_bars.set_yscale("log")
    ax_bars.set_ylabel("Intersection size (log10)")
    ax_bars.set_xticks([])
    ax_bars.spines[["top", "right"]].set_visible(False)
    ax_bars.grid(axis="y", color="#e8ecef", linewidth=0.8)
    ax_bars.set_axisbelow(True)

    for x_position, count in zip(x_positions, counts):
        ax_bars.text(
            x_position,
            count * 1.12,
            f"{count:,}",
            ha="center",
            va="bottom",
            fontsize=7,
            rotation=90 if count < 100 else 0,
        )

    y_positions = list(range(len(databases)))
    y_lookup = {database: y for y, database in zip(y_positions, databases)}
    for x_position, (membership, _) in zip(x_positions, intersections):
        present_y = [y_lookup[database] for database in membership]
        ax_matrix.scatter(
            [x_position] * len(databases),
            y_positions,
            s=26,
            color=grey,
            edgecolor="none",
            zorder=1,
        )
        if present_y:
            ax_matrix.plot(
                [x_position, x_position],
                [min(present_y), max(present_y)],
                color=dark,
                linewidth=1.2,
                zorder=2,
            )
            ax_matrix.scatter(
                [x_position] * len(present_y),
                present_y,
                s=34,
                color=dark,
                edgecolor="none",
                zorder=3,
            )

    ax_matrix.set_xlim(-0.6, len(intersections) - 0.4)
    ax_matrix.set_ylim(-0.6, len(databases) - 0.4)
    ax_matrix.set_xticks([])
    ax_matrix.set_yticks(y_positions)
    ax_matrix.set_yticklabels([])
    ax_matrix.invert_yaxis()
    ax_matrix.spines[["top", "right", "bottom", "left"]].set_visible(False)
    ax_matrix.tick_params(axis="y", length=0)

    set_size_values = [set_sizes[database] for database in databases]
    ax_sets.barh(y_positions, set_size_values, color="#77858c", height=0.62)
    ax_sets.set_xscale("log")
    ax_sets.set_xlim(0.8, max(set_size_values) * 2.4)
    ax_sets.set_xlabel("Set size (log10)")
    ax_sets.set_yticks(y_positions)
    ax_sets.set_yticklabels(databases)
    ax_sets.invert_yaxis()
    ax_sets.spines[["top", "right", "left"]].set_visible(False)
    ax_sets.grid(axis="x", color="#e8ecef", linewidth=0.8)
    ax_sets.set_axisbelow(True)
    ax_sets.tick_params(axis="y", length=0)

    for y_position, value in zip(y_positions, set_size_values):
        label_inside_bar = value >= 100
        ax_sets.text(
            value / 1.12 if label_inside_bar else value * 1.08,
            y_position,
            f"{value:,}",
            va="center",
            ha="right" if label_inside_bar else "left",
            color="white" if label_inside_bar else dark,
            fontsize=7,
        )

    #figure.suptitle("Supported Organism Coverage Across KlinkPPI Resources", y=0.98)
    figure.subplots_adjust(left=0.16, right=0.98, top=0.88, bottom=0.12)

    for suffix in (".pdf", ".svg", ".png"):
        figure.savefig(output_prefix.with_suffix(suffix), dpi=600, bbox_inches="tight")

    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an UpSet plot of supported organisms across KlinkPPI resources."
    )
    parser.add_argument(
        "--supported-dir",
        type=Path,
        default=Path("Supported_Organisms"),
        help="Directory containing AllSpecies*.csv files.",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("manuscript_figures/supported_organisms_upset"),
        help="Output prefix. The script writes PDF, SVG, PNG, and TSV summaries.",
    )
    args = parser.parse_args()

    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    database_taxa, taxon_memberships = build_memberships(args.supported_dir)
    write_summary(database_taxa, taxon_memberships, args.output_prefix)
    make_plot(taxon_memberships, args.output_prefix)

    print("Supported organism counts:")
    for database in DATABASE_FILES:
        print(f"  {database}: {len(database_taxa[database]):,}")
    print(f"  Union: {len(taxon_memberships):,}")
    print(f"Wrote {args.output_prefix}.pdf/.svg/.png")
    print(f"Wrote {args.output_prefix}.set_sizes.tsv")
    print(f"Wrote {args.output_prefix}.intersections.tsv")


if __name__ == "__main__":
    main()
