import pandas as pd


def compute_averages(path: str) -> pd.Series:
    """
    Load a CSV file and compute the mean of each metric column, assuming 'id' is non-metric.
    """
    df = pd.read_csv(path)
    metrics = [c for c in df.columns if c != 'id']
    return df[metrics].mean()


def main():
    # Define file paths
    files = [
        r"eval metrics\human_metrics.csv",
        r"eval metrics\llm_metrics.csv"
    ]

    # Process each file and print averages
    for file_path in files:
        means = compute_averages(file_path)
        print(f"\nAverages for {file_path}:")
        for metric, avg in means.items():
            print(f"  {metric:30s}: {avg:.2f}")


if __name__ == "__main__":
    main()
