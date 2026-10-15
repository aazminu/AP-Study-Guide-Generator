# compute_kappa.py

import pandas as pd
from sklearn.metrics import cohen_kappa_score
import csv

# --- Configuration ---
MODEL_CSV = "llm_metrics.csv"
HUMAN_CSV = "human_metrics.csv"  # must have same columns: id + RUBRIC_CATEGORIES
RUBRIC_CATEGORIES = [
    "Clarity",
    "Coverage of Essential Topics",
    "Factual Accuracy",
    "Organization",
    "Usefulness",
]

def load_and_merge(model_path, human_path):
    """Load both CSVs and merge on 'id'."""
    df_model = pd.read_csv(model_path)
    df_human = pd.read_csv(human_path)
    return df_model.merge(df_human, on="id", suffixes=("_model", "_human"))

def round_to_int(df, categories):
    """Round float scores to nearest int for both model and human columns."""
    for cat in categories:
        df[f"{cat}_model_int"] = df[f"{cat}_model"].round().astype(int)
        df[f"{cat}_human_int"] = df[f"{cat}_human"].round().astype(int)
    return df

def compute_kappas(df, categories):
    """
    Compute quadratic‑weighted Cohen's κ per category.
    Returns a dict {category: kappa}.
    """
    kappas = {}
    for cat in categories:
        kappas[cat] = cohen_kappa_score(
            df[f"{cat}_human_int"],
            df[f"{cat}_model_int"],
            weights="quadratic"
        )
    return kappas
def write_kappas_to_csv(kappas, output_path):
    """Write the kappa dict out to a CSV with columns Category,Kappa."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Category", "Kappa"])
        for cat, k in kappas.items():
            writer.writerow([cat, f"{k:.3f}"])
    print(f"Wrote κ results to '{output_path}'")

if __name__ == "__main__":
    df = load_and_merge(MODEL_CSV, HUMAN_CSV)
    df = round_to_int(df, RUBRIC_CATEGORIES)
    kappas = compute_kappas(df, RUBRIC_CATEGORIES)
    write_kappas_to_csv(kappas, "kappa.csv")
