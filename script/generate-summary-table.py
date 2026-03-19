#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import os
import json

def calculate_success_rate(df):
    """Calculate success rate from failure columns."""
    fail_cols = ["fails-interpreter", "fails-counterfactual", "fails-no-response", "fails-literal"]
    df['total_fails'] = df[fail_cols].sum(axis=1)
    df['success'] = (df['total_fails'] == 0).astype(int)
    return df['success'].mean()

def generate_summary_table(config_name: str, test_case_folder: str):
    """Generate a LaTeX summary table for the given configuration."""
    results_dir = Path("results")
    config_dir = results_dir / config_name
    
    if not config_dir.exists():
        raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
    
    model_dirs = [d for d in config_dir.iterdir() if d.is_dir()]
    if not model_dirs:
        raise FileNotFoundError(f"No model directories found in {config_dir}")
    
    # Generate table for each model separately
    table_files = []
    
    for model_dir in model_dirs:
        csv_path = model_dir / test_case_folder / "results.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path, delimiter=';', quotechar='"', encoding='utf-8')
            
            # Calculate success rate
            fail_cols = ["fails-interpreter", "fails-counterfactual", "fails-no-response", "fails-literal"]
            df['total_fails'] = df[fail_cols].sum(axis=1)
            df['success'] = (df['total_fails'] == 0).astype(int)
            
            # Add model name to dataframe
            df['model'] = model_dir.name
            
            # Check if we have ablation studies
            has_ablation = len(df['ablate-target-value'].unique()) > 1
            
            # Create output directory for this model
            fig_dir = os.path.join("results", config_name, model_dir.name, test_case_folder, "fig")
            os.makedirs(fig_dir, exist_ok=True)
            
            # Generate LaTeX table
            latex_table = generate_latex_table(df, config_name, has_ablation)
            
            # Write LaTeX table to file
            table_file = os.path.join(fig_dir, "summary_table.tex")
            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(latex_table)
            
            table_files.append(table_file)
            
            print(f"\n{'='*60}")
            print(f"LaTeX table generated: {table_file}")
            print(f"{'='*60}")

    return table_files

def generate_latex_table(df, config_name, has_ablation):
    """Generate the LaTeX table string."""
    
    if has_ablation:
        # Group by model and ablation target value
        summary = df.groupby(['model', 'ablate-target-value']).agg({
            'success': ['mean', 'count']
        }).round(3)
        
        summary.columns = ['success_rate', 'total_problems']
        summary = summary.reset_index()
        
        # Pivot to have ablation values as columns
        pivot_summary = summary.pivot(index='model', columns='ablate-target-value', values='success_rate')
        count_summary = summary.pivot(index='model', columns='ablate-target-value', values='total_problems')
        
        latex = "\\begin{table}[htbp]\n"
        latex += "\\centering\n"
        latex += f"\\caption{{Summary results for {config_name.replace('_', ' ').title()}}}\n"
        latex += f"\\label{{tab:summary_{config_name.replace('-', '_')}}}\n"
        
        # Determine column format
        num_cols = len(pivot_summary.columns) + 1
        col_format = "l" + "c" * (num_cols - 1)
        
        latex += f"\\begin{{tabular}}{{{col_format}}}\n"
        latex += "\\toprule\n"
        
        # Header
        ablation_labels = ["Present" if val == 1 else "Absent" for val in sorted(pivot_summary.columns)]
        header = "Model & " + " & ".join(ablation_labels) + " \\\\\n"
        latex += header
        latex += "\\midrule\n"
        
        # Data rows
        for model in pivot_summary.index:
            row_data = [model.replace('_', '\\_')]
            for col in sorted(pivot_summary.columns):
                success_rate = pivot_summary.loc[model, col]
                total_count = count_summary.loc[model, col]
                if pd.notna(success_rate):
                    row_data.append(f"{success_rate:.3f} ({int(total_count)})")
                else:
                    row_data.append("--")
            latex += " & ".join(row_data) + " \\\\\n"
        
    else:
        # Simple table without ablation
        summary = df.groupby('model').agg({
            'success': ['mean', 'count']
        }).round(3)
        
        summary.columns = ['success_rate', 'total_problems']
        summary = summary.reset_index()
        
        latex = "\\begin{table}[htbp]\n"
        latex += "\\centering\n"
        latex += f"\\caption{{Summary results for {config_name.replace('_', ' ').title()}}}\n"
        latex += f"\\label{{tab:summary_{config_name.replace('-', '_')}}}\n"
        latex += "\\begin{tabular}{lcc}\n"
        latex += "\\toprule\n"
        latex += "Model & Success Rate & Total Problems \\\\\n"
        latex += "\\midrule\n"
        
        # Data rows
        for _, row in summary.iterrows():
            model_name = row['model'].replace('_', '\\_')
            latex += f"{model_name} & {row['success_rate']:.3f} & {int(row['total_problems'])} \\\\\n"
    
    latex += "\\bottomrule\n"
    latex += "\\end{tabular}\n"
    latex += "\\end{table}\n"
    
    return latex

def main():
    parser = argparse.ArgumentParser(
        description="Generate LaTeX summary table from test results"
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
        generate_summary_table(args.config, test_case_folder)
    except FileNotFoundError as e:
        sys.exit(f"Error: {e}")
    except json.JSONDecodeError as e:
        sys.exit(f"Error parsing JSON in {settings_file}: {e}")
    except KeyError as e:
        sys.exit(f"Error: key {e} not found in settings")

if __name__ == "__main__":
    main()