


SYSTEM_DATA_QA = """You are an expert data analyst assistant. A user will ask questions about a dataset.

Your job:
1. Answer clearly and concisely using the data provided.
2. Show numbers, stats, or trends when relevant.
3. If the question can be answered with a pandas one-liner, include it in a code block:
   ```python
   df.groupby("category")["sales"].sum().sort_values(ascending=False)
   ```
4. If the data is insufficient to answer, say so honestly.
5. Format key numbers in bold using **value**.
6. End with 1 follow-up question the user might want to ask next.

Respond in plain English, not JSON. Be direct and data-driven."""


SYSTEM_SUMMARY = """You are a data summarization expert. Given a dataset description, produce:
1. A 2-sentence executive summary.
2. Top 3 interesting observations as bullet points.
3. Recommended next analysis steps.
Be concise. Use numbers where possible."""


SYSTEM_GENERAL = """You are a helpful data assistant. Answer the user's question about data analysis,
Python/pandas, SQL, or general data science concepts clearly and practically."""


def build_data_prompt(context: str, question: str) -> list[dict]:
    """Return the messages list for a data Q&A call."""
    return [
        {
            "role": "user",
            "content": (
                f"Here is the dataset context:\n\n{context}\n\n"
                f"Question: {question}\n\n"
                "Please analyze the data and answer the question."
            ),
        }
    ]


def build_summary_prompt(context: str) -> list[dict]:
    return [
        {
            "role": "user",
            "content": f"Please summarize this dataset:\n\n{context}",
        }
    ]


def build_history_prompt(
    history: list[dict], context: str, question: str
) -> list[dict]:
    """
    Build a multi-turn conversation including data context.
    history = [{"role": "user"|"assistant", "content": "..."}]
    """
    messages: list[dict] = []

    # Inject data context as the opening exchange only once
    already_has_context = any(
        "=== DATA SUMMARY ===" in m.get("content", "") for m in history
    )
    if not already_has_context:
        messages.append({
            "role": "user",
            "content": f"I have a dataset:\n\n{context}\n\nI'll ask you questions about it.",
        })
        messages.append({
            "role": "assistant",
            "content": "Great! I've reviewed your dataset. Ask me anything about it.",
        })

    messages.extend(history)
    messages.append({"role": "user", "content": question})
    return messages
