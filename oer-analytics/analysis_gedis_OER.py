#!/usr/bin/env python3

"""
Multilingual OER Impact Analysis Script

Analyses multilingual Open Educational Resources (OERs)
using metadata extracted from Zenodo repositories.

The script generates:
- cumulative impact indicators
- multilingual performance metrics
- downloads per OER
- downloads per month
- analytical summary datasets
- visualisations

Usage example:
    python analysis_gedis_OER.py --input gedis_stats.csv --output-dir outputs

Requirements:
    - Python 3.x
    - pandas
    - matplotlib

Author: Juan-José Boté-Vericad
Year: 2026
"""

import argparse
from pathlib import Path
from datetime import datetime
import math

import pandas as pd
import matplotlib.pyplot as plt


def safe_divide(a, b):
    if b == 0 or pd.isna(b):
        return 0
    return a / b


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_dates(df):
    df = df.copy()

    # Fechas en formato europeo dd/mm/aa
    if "publication_date" in df.columns:
        df["publication_date"] = pd.to_datetime(
            df["publication_date"],
            dayfirst=True,
            errors="coerce"
        )
    else:
        df["publication_date"] = pd.NaT

    # 'created' puede venir en ISO, pero permitimos dayfirst por seguridad
    if "created" in df.columns:
        df["created"] = pd.to_datetime(
            df["created"],
            dayfirst=True,
            errors="coerce",
            utc=True
        )
        df["created"] = df["created"].dt.tz_localize(None)
    else:
        df["created"] = pd.NaT

    # Fecha operativa para el análisis
    df["analysis_date"] = df["publication_date"].fillna(df["created"])

    return df


def prepare_dataframe(df, reference_date):
    df = df.copy()

    # Normalización de texto
    text_cols = [
        "id", "title", "language", "doi", "url", "resource_type",
        "keywords", "content_block_normalized", "event_normalized"
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    # Numéricos
    for col in ["downloads", "views"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    df = parse_dates(df)

    # Filtrar solo OERs = lesson
    if "resource_type" in df.columns:
        df["resource_type_norm"] = df["resource_type"].str.lower().str.strip()
        df = df[df["resource_type_norm"] == "lesson"].copy()
    else:
        df["resource_type_norm"] = ""

    # Eliminar filas sin fecha analizable
    df = df[~df["analysis_date"].isna()].copy()

    # Variables derivadas usando la fecha de referencia del informe
    df["days_since_publication"] = (reference_date - df["analysis_date"]).dt.days.clip(lower=0)
    df["months_since_publication"] = (df["days_since_publication"] / 30.4375).clip(lower=0.1)

    df["downloads_per_month"] = df.apply(
        lambda r: safe_divide(r["downloads"], r["months_since_publication"]), axis=1
    )
    df["views_per_month"] = df.apply(
        lambda r: safe_divide(r["views"], r["months_since_publication"]), axis=1
    )
    df["view_download_ratio"] = df.apply(
        lambda r: safe_divide(r["views"], r["downloads"]), axis=1
    )

    # Rellenar vacíos
    for col in ["language", "content_block_normalized", "event_normalized"]:
        if col in df.columns:
            df[col] = df[col].replace("", "unspecified").fillna("unspecified")
        else:
            df[col] = "unspecified"

    return df


def summarise_general(df):
    total_oers = len(df)

    if total_oers == 0:
        return {
            "total_oers_lesson": 0,
            "total_downloads": 0,
            "total_views": 0,
            "average_downloads_per_oer": 0,
            "median_downloads_per_oer": 0,
            "average_views_per_oer": 0,
            "median_views_per_oer": 0,
            "average_downloads_per_month": 0,
            "median_downloads_per_month": 0,
        }

    return {
        "total_oers_lesson": total_oers,
        "total_downloads": int(df["downloads"].sum()),
        "total_views": int(df["views"].sum()),
        "average_downloads_per_oer": round(df["downloads"].mean(), 2),
        "median_downloads_per_oer": round(df["downloads"].median(), 2),
        "average_views_per_oer": round(df["views"].mean(), 2),
        "median_views_per_oer": round(df["views"].median(), 2),
        "average_downloads_per_month": round(df["downloads_per_month"].mean(), 2),
        "median_downloads_per_month": round(df["downloads_per_month"].median(), 2),
    }


def group_summary(df, group_col):
    if df.empty:
        return pd.DataFrame()

    out = (
        df.groupby(group_col, dropna=False)
        .agg(
            oer_count=("id", "count"),
            total_downloads=("downloads", "sum"),
            total_views=("views", "sum"),
            mean_downloads=("downloads", "mean"),
            median_downloads=("downloads", "median"),
            mean_views=("views", "mean"),
            mean_downloads_per_month=("downloads_per_month", "mean"),
            mean_view_download_ratio=("view_download_ratio", "mean"),
        )
        .reset_index()
        .sort_values(["total_downloads", "total_views"], ascending=[False, False])
    )

    num_cols = [
        "mean_downloads", "median_downloads", "mean_views",
        "mean_downloads_per_month", "mean_view_download_ratio"
    ]
    for col in num_cols:
        out[col] = out[col].round(2)

    return out


def downloads_per_oer_by_language(df):
    if df.empty:
        return pd.DataFrame()

    out = (
        df.groupby("language")
        .agg(
            oer_count=("id", "count"),
            total_downloads=("downloads", "sum"),
            total_views=("views", "sum"),
        )
        .reset_index()
    )

    out["downloads_per_oer"] = out.apply(
        lambda r: safe_divide(r["total_downloads"], r["oer_count"]), axis=1
    ).round(2)

    out["views_per_oer"] = out.apply(
        lambda r: safe_divide(r["total_views"], r["oer_count"]), axis=1
    ).round(2)

    out = out.sort_values(["downloads_per_oer", "total_downloads"], ascending=[False, False])
    return out


def top_oers(df, top_n=20):
    if df.empty:
        return pd.DataFrame()

    cols = [
        "id", "title", "language", "downloads", "views",
        "downloads_per_month", "views_per_month", "view_download_ratio",
        "publication_date", "resource_type", "content_block_normalized",
        "event_normalized", "keywords", "url"
    ]
    existing = [c for c in cols if c in df.columns]

    out = (
        df[existing]
        .sort_values(["downloads", "views"], ascending=[False, False])
        .head(top_n)
        .copy()
    )

    for col in ["downloads_per_month", "views_per_month", "view_download_ratio"]:
        if col in out.columns:
            out[col] = out[col].round(2)

    return out


def save_text_summary(path, title, general, df, reference_date):
    lines = [
        title,
        "=" * len(title),
        "",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Reference date for analysis: {reference_date.strftime('%Y-%m-%d')}",
        "",
        f"Total OERs (lesson): {general['total_oers_lesson']}",
        f"Total downloads: {general['total_downloads']}",
        f"Total views: {general['total_views']}",
        f"Average downloads per OER: {general['average_downloads_per_oer']}",
        f"Median downloads per OER: {general['median_downloads_per_oer']}",
        f"Average views per OER: {general['average_views_per_oer']}",
        f"Median views per OER: {general['median_views_per_oer']}",
        f"Average downloads per month: {general['average_downloads_per_month']}",
        f"Median downloads per month: {general['median_downloads_per_month']}",
        "",
    ]

    if not df.empty:
        top = df.sort_values(["downloads", "views"], ascending=[False, False]).iloc[0]
        lines.extend([
            "Top OER by downloads:",
            f"  Title: {top.get('title', '')}",
            f"  Language: {top.get('language', '')}",
            f"  Downloads: {int(top.get('downloads', 0))}",
            f"  Views: {int(top.get('views', 0))}",
            f"  URL: {top.get('url', '')}",
            "",
        ])

    path.write_text("\n".join(lines), encoding="utf-8")


def save_bar_chart(df, category_col, value_col, title, output_path, top_n=15):
    if df.empty or category_col not in df.columns or value_col not in df.columns:
        return

    plot_df = df[[category_col, value_col]].copy().head(top_n)
    if plot_df.empty:
        return

    plt.figure(figsize=(12, 7))
    plt.barh(plot_df[category_col].astype(str), plot_df[value_col])
    plt.xlabel(value_col)
    plt.ylabel(category_col)
    plt.title(title)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()


def save_outputs(df, output_dir, prefix, reference_date):
    general = summarise_general(df)

    by_language = group_summary(df, "language")
    by_content = group_summary(df, "content_block_normalized")
    by_event = group_summary(df, "event_normalized")
    by_resource_type = group_summary(df, "resource_type")
    top_downloads = top_oers(df, top_n=20)
    dpo_lang = downloads_per_oer_by_language(df)

    save_text_summary(
        output_dir / f"{prefix}_summary_general.txt",
        f"{prefix.upper()} GEDIS OER ANALYSIS (resource_type = lesson)",
        general,
        df,
        reference_date
    )

    if not by_language.empty:
        by_language.to_csv(output_dir / f"{prefix}_summary_by_language.csv", index=False, encoding="utf-8-sig")
    if not by_content.empty:
        by_content.to_csv(output_dir / f"{prefix}_summary_by_content_block.csv", index=False, encoding="utf-8-sig")
    if not by_event.empty:
        by_event.to_csv(output_dir / f"{prefix}_summary_by_event.csv", index=False, encoding="utf-8-sig")
    if not by_resource_type.empty:
        by_resource_type.to_csv(output_dir / f"{prefix}_summary_by_resource_type.csv", index=False, encoding="utf-8-sig")
    if not top_downloads.empty:
        top_downloads.to_csv(output_dir / f"{prefix}_top_oers_by_downloads.csv", index=False, encoding="utf-8-sig")
    if not dpo_lang.empty:
        dpo_lang.to_csv(output_dir / f"{prefix}_downloads_per_oer_by_language.csv", index=False, encoding="utf-8-sig")

    if not by_language.empty:
        save_bar_chart(
            by_language,
            "language",
            "total_downloads",
            f"{prefix.upper()} - Downloads by language",
            output_dir / f"{prefix}_downloads_by_language.png"
        )
        save_bar_chart(
            by_language,
            "language",
            "total_views",
            f"{prefix.upper()} - Views by language",
            output_dir / f"{prefix}_views_by_language.png"
        )

    if not dpo_lang.empty:
        save_bar_chart(
            dpo_lang,
            "language",
            "downloads_per_oer",
            f"{prefix.upper()} - Downloads per OER by language",
            output_dir / f"{prefix}_downloads_per_oer_by_language.png"
        )

    if not by_content.empty:
        save_bar_chart(
            by_content,
            "content_block_normalized",
            "total_downloads",
            f"{prefix.upper()} - Downloads by content block",
            output_dir / f"{prefix}_downloads_by_content_block.png"
        )

    if not by_event.empty:
        by_event_non_unspecified = by_event[by_event["event_normalized"] != "unspecified"].copy()
        if not by_event_non_unspecified.empty:
            save_bar_chart(
                by_event_non_unspecified,
                "event_normalized",
                "total_downloads",
                f"{prefix.upper()} - Downloads by event",
                output_dir / f"{prefix}_downloads_by_event.png"
            )

    if not top_downloads.empty:
        plot_top = top_downloads.head(10).copy()
        plt.figure(figsize=(13, 8))
        plt.barh(plot_top["title"].astype(str), plot_top["downloads"])
        plt.xlabel("downloads")
        plt.ylabel("title")
        plt.title(f"{prefix.upper()} - Top 10 OERs by downloads")
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(output_dir / f"{prefix}_top_10_oers_downloads.png", dpi=200, bbox_inches="tight")
        plt.close()

    return general


def main():
    parser = argparse.ArgumentParser(
        description="Analiza GEDIS OERs (resource_type = lesson) con corte temporal y periodo."
    )
    parser.add_argument("--input", required=True, help="Ruta al CSV de entrada.")
    parser.add_argument("--output-dir", required=True, help="Directorio de salida.")
    parser.add_argument(
        "--cutoff",
        default="2025-12-31",
        help="Fecha de corte acumulada en formato YYYY-MM-DD."
    )
    parser.add_argument(
        "--start",
        default="2025-06-01",
        help="Fecha inicial del periodo en formato YYYY-MM-DD."
    )
    parser.add_argument(
        "--end",
        default="2025-12-31",
        help="Fecha final del periodo en formato YYYY-MM-DD."
    )
    parser.add_argument(
        "--oers-per-month",
        type=int,
        default=3,
        help="Número promedio de OER publicados por mes para la proyección."
    )
    parser.add_argument(
        "--project-end",
        default="2027-08-31",
        help="Fecha final del proyecto en formato YYYY-MM-DD."
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"No existe el CSV de entrada: {input_path}")

    df = pd.read_csv(input_path)

    cutoff = pd.to_datetime(args.cutoff)
    start = pd.to_datetime(args.start)
    end = pd.to_datetime(args.end)
    project_end = pd.to_datetime(args.project_end)

    prepared = prepare_dataframe(df, reference_date=cutoff)

    # Acumulado hasta cutoff
    cumulative_df = prepared[prepared["analysis_date"] <= cutoff].copy()

    # Periodo entre start y end
    period_df = prepared[
        (prepared["analysis_date"] >= start) &
        (prepared["analysis_date"] <= end)
    ].copy()

    cumulative_general = save_outputs(
        cumulative_df,
        output_dir,
        prefix="cumulative_to_2025_12_31",
        reference_date=cutoff
    )

    period_general = save_outputs(
        period_df,
        output_dir,
        prefix="period_2025_06_01_to_2025_12_31",
        reference_date=cutoff
    )

    print("Análisis completado correctamente.")
    print(f"CSV de entrada: {input_path.resolve()}")
    print(f"Directorio de salida: {output_dir.resolve()}")
    print("")
    print("ACUMULADO HASTA 2025-12-31")
    print(f"OERs analizados: {cumulative_general['total_oers_lesson']}")
    print(f"Descargas totales: {cumulative_general['total_downloads']}")
    print(f"Visualizaciones totales: {cumulative_general['total_views']}")
    print("")
    print("PERIODO 2025-06-01 A 2025-12-31")
    print(f"OERs analizados: {period_general['total_oers_lesson']}")
    print(f"Descargas totales: {period_general['total_downloads']}")
    print(f"Visualizaciones totales: {period_general['total_views']}")


if __name__ == "__main__":
    main()