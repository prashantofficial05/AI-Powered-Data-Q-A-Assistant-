import os
import json
import pandas as pd
from pathlib import Path

MAX_ROWS  = int(os.getenv("MAX_ROWS_TO_SEND_LLM", 10))
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def load_csv(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path, encoding="utf-8-sig")


def get_dataframe_summary(df: pd.DataFrame) -> str:
    lines = []
    lines.append(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    lines.append(f"Columns: {', '.join(df.columns.tolist())}")
    lines.append("\\nColumn types & sample values:")

    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = int(df[col].isna().sum())

        if pd.api.types.is_numeric_dtype(df[col]):
            non_null = df[col].dropna()
            if len(non_null) > 0:
                sample = [
                    f"min={non_null.min():.2f}",
                    f"max={non_null.max():.2f}",
                    f"mean={non_null.mean():.2f}",
                ]
            else:
                sample = ["all null"]
        else:
            sample = df[col].dropna().astype(str).unique()[:5].tolist()

        lines.append(f"  • {col} ({dtype}, {nulls} nulls): {sample}")

    return "\\n".join(lines)


def dataframe_to_context(df: pd.DataFrame, question: str) -> str:
    summary = get_dataframe_summary(df)
    sample = df.head(10)

    return f"""
Dataset Shape: {df.shape[0]} rows x {df.shape[1]} columns

Columns:
{', '.join(df.columns)}

Sample Data:
{sample.to_string(index=False)}

Question:
{question}

Summary:
{summary}
"""


def _df_to_readable(df: pd.DataFrame) -> str:
    try:
        return df.head(50).to_markdown(index=False)
    except ImportError:
        return df.head(50).to_string(index=False)


def run_pandas_query(df: pd.DataFrame, code: str) -> str:
    forbidden = [
        "to_csv", "to_sql", "to_excel", "to_parquet",
        "os.", "open(", "__import__", "exec", "eval",
        "subprocess", "shutil", "pathlib",
    ]
    for kw in forbidden:
        if kw in code:
            return f"⚠ Blocked: forbidden keyword '{kw}' in generated code."

    try:
        local_ns = {"df": df, "pd": pd}
        result = eval(code, {"__builtins__": {}}, local_ns)

        if isinstance(result, pd.DataFrame):
            return _df_to_readable(result)
        elif isinstance(result, pd.Series):
            return result.head(50).to_string()
        else:
            return str(result)
    except Exception as e:
        return f"Query error: {e}"


def list_uploaded_files() -> list[dict]:
    files = []
    for f in UPLOAD_DIR.glob("*.csv"):
        try:
            df = pd.read_csv(f, nrows=1)
            files.append({
                "filename": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "columns": df.columns.tolist(),
            })
        except Exception:
            pass
    return files
