import argparse
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os
import json

def count_problems_per_category(df):
    # Explode categories categories (format: "[Category1,Category2]")
    df_exploded = df.copy()
    df_exploded['categories'] = df_exploded['categories'].astype(str)
    df_exploded['categories'] = df_exploded['categories'].str.strip('[]').str.split(',')
    df_exploded = df_exploded.explode('categories')
    df_exploded['categories'] = df_exploded['categories'].str.strip()
    
    return (
        df_exploded
            .drop_duplicates(["test-case", "problem-no", "categories"])
            .groupby("categories")
            .size()
    )

def generate_aggregated_plot(df, plot, fig_dir):
    # esplodo le categorie
    df['categories'] = df['categories'].astype(str).str.strip('[]').str.split(',')
    df_exploded = df.explode('categories')
    df_exploded['categories'] = df_exploded['categories'].str.strip()

    summary = (
        df_exploded.groupby(["categories", "ablate-target-value"])
        .agg(success_rate=("success", "mean"),
             count=("success", "size"))
        .reset_index()
    )

    plt.figure(figsize=(6,6))
    label_map = {
        1: "Present",
        0: "Absent"
    }
    summary["target_label"] = summary["ablate-target-value"].map(label_map)

    ax = sns.barplot(
        data=summary,
        x="categories",
        y="success_rate",
        hue="target_label",
        palette="Set2"
    )
    ax.legend(title="Target value")

    for p in ax.patches:
        h = p.get_height()
        ax.annotate(f"{h:.2f}",
                    (p.get_x() + p.get_width()/2., h),
                    ha='center', va='bottom', fontsize=8)

    plt.title("Success Rate by Linguistic Category")
    plt.xlabel("Category")
    plt.ylabel("Average Success Rate")
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0,1.1)
    plt.tight_layout()
    plt.savefig(f"{fig_dir}/success_rate_by_category.png")
    plt.close()

def generate_aggregated_boxplot(df, plot, fig_dir):
    # Use the reusable function to count problems per category BEFORE exploding df
    category_counts = count_problems_per_category(df)
    
    df['categories'] = df['categories'].astype(str).str.strip('[]').str.split(',')
    df_exploded = df.explode('categories')
    df_exploded['categories'] = df_exploded['categories'].str.strip()

    summary = (
        df_exploded.groupby(["run", "categories", "ablate-target-value"])
        .agg(success_rate=("success", "mean"))
        .reset_index()
    )
    
    # labels for  ablate-target-value
    plt.figure(figsize=(8,6))
    label_map = {
        1: "Present",
        0: "Absent"
    }
    summary["target_label"] = summary["ablate-target-value"].map(label_map)

    ax = sns.boxplot(
        data=summary,
        x="categories",
        y="success_rate",
        hue="target_label",
        palette="Set2",
        order=sorted(summary['categories'].unique())
    )
    ax.legend(title="Target value", loc='lower right', bbox_to_anchor=(1.0, -0.25))

    # Use categories from summary for iteration
    categories = sorted(summary['categories'].unique())
    target_values = sorted(summary['ablate-target-value'].unique())
    
    for i, category in enumerate(categories):
        # Get problem count for this category from category_counts
        # category_counts already contains the total unique problems (not per run)
        if category in category_counts.index:
            count = int(category_counts[category])
        else:
            count = 0
        
        for j, target_val in enumerate(target_values):
            x_offset = -0.2 if j == 0 else 0.2
            mask = (summary['categories'] == category) & (summary['ablate-target-value'] == target_val)
            if mask.sum() > 0:
                median_y = summary[mask]['success_rate'].median()
            else:
                median_y = 0.5  
            
            # Always add the label
            ax.text(i + x_offset, median_y, f'n={count}', 
                    ha='center', va='center', 
                    fontsize=8, color='black', weight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

    # plt.title("Success Rate by Linguistic Category")
    plt.xlabel("Category")
    plt.ylabel("Success Rate")
    plt.xticks(rotation=45, ha="right")
    plt.ylim(-0.05,1.1)
    plt.tight_layout()
    plt.savefig(f"{fig_dir}/success_rate_by_category_boxplot.png")
    plt.close()


def generate_success_rate_by_category_count(df, plot, fig_dir):
    df['category_count'] = df['categories'].str.len()

    summary = (
        df.groupby(["category_count", "ablate-target-value"])
        .agg(
            success_rate=("success", "mean"),
            count=("success", "size")
        )
        .reset_index()
    )

    summary["label"] = summary["category_count"].astype(str)

    plt.figure(figsize=(6, 6))
    label_map = {
        1: "Present",
        0: "Absent"
    }
    summary["target_label"] = summary["ablate-target-value"].map(label_map)

    ax = sns.barplot(
        data=summary,
        x="label",
        y="success_rate",
        hue="target_label",
        palette="Set2"
    )
    ax.legend(title="Target value")
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.2f}",
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=8)

    #plt.title("Success Rate by Complexity")
    plt.xlabel("Complexity")
    plt.ylabel(f"Average Success Rate over {df['run'].nunique()} runs")
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0, 1.1)
    plt.tight_layout()
    plt.savefig(f"{fig_dir}/success_rate_by_complexity.png")
    plt.close()

def process_csv_file(csv_file):
    """Process a single CSV file and generate charts in the corresponding subdirectory."""
    # Get the subdirectory name (e.g., "config/model/test-suite" from "results/config/model/test-suite/file.csv")
    rel_path = os.path.relpath(csv_file, "results")
    subdir = os.path.dirname(rel_path)
    
    # Create output directory in results/config/dataset/fig
    path_parts = subdir.split('/')
    if len(path_parts) >= 2:
        config_dataset = os.path.join(path_parts[0], path_parts[1])  # e.g., "test-mock/dataset"
    else:
        config_dataset = path_parts[0]
    fig_dir = os.path.join("results", config_dataset, "fig")
    os.makedirs(fig_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Processing: {csv_file}")
    print(f"Output directory: {fig_dir}")
    print(f"{'='*60}")
    
    df = pd.read_csv(csv_file, delimiter=';', quotechar='"', encoding='utf-8')
    fail_cols = [
        "fails-interpreter", "fails-counterfactual", "fails-no-response", "fails-literal"
    ]

    df["fails"] = df[fail_cols].sum(axis=1)
    df["success"] = (df["fails"] == 0).astype(int)
    df["ablate-target-value"] = df["ablate-target-value"].astype(int)
    df["test-case-short"] = df["test-case"].apply(
        lambda x: os.path.join(os.path.basename(os.path.dirname(str(x))), os.path.basename(str(x)))
    )
    
    # Print the number of problems per linguistic category
    category_counts = count_problems_per_category(df)
    print("\nNumber of problems per linguistic category:")
    for category, count in category_counts.items():
        print(f"  {category}: {count}")
    print()
    
    sns.set_style("whitegrid")
    generate_aggregated_plot(df, plt, fig_dir)
    generate_success_rate_by_category_count(df, plt, fig_dir)
    
    print(f"Charts saved in {fig_dir}")

def generate_charts(config_name: str, test_case_folder: str):
    results_dir = Path("results")
    config_dir = results_dir / config_name
    
    # Find the model directory by scanning subdirectories
    if not config_dir.exists():
        raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
    
    model_dirs = [d for d in config_dir.iterdir() if d.is_dir()]
    if not model_dirs:
        raise FileNotFoundError(f"No model directories found in {config_dir}")
    
    # Use the first model directory found (or you could search for one with test_case_folder)
    for model_dir in model_dirs:
        csv_path = model_dir / test_case_folder / "results.csv"
        if csv_path.exists():
            print(f"Processing CSV file: {csv_path}")
            process_csv_file(str(csv_path))
            print(f"\n{'='*60}")
            print("Charts generated successfully.")
            print(f"{'='*60}")
            return
    
    raise FileNotFoundError(f"No results.csv found for test case folder: {test_case_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate charts from test suite specified via settings file"
    )
    parser.add_argument(
        "config",
        help="Name of settings file (e.g. 'test-mock' loads settings/test-mock.json)"
    )

    args = parser.parse_args()
    settings_file = Path("settings") / f"{args.config}.json"

    try:
        with open(settings_file, encoding="utf-8") as f:
            settings = json.load(f)
        test_case_folder = settings["test-case-folder"]
        generate_charts(args.config, test_case_folder)
    except FileNotFoundError as e:
        sys.exit(f"{e}")
    except json.JSONDecodeError as e:
        sys.exit(f"Error parsing JSON in {settings_file}: {e}")
    except KeyError as e:
        sys.exit(f"Error: key {e} not found")
