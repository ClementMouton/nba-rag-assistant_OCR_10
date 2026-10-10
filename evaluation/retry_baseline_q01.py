
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness
from langchain_mistralai import ChatMistralAI
from utils.config import MISTRAL_API_KEY, MODEL_NAME

baseline_file = ROOT / "evaluation/results/baseline_results.json"
scores_file = ROOT / "evaluation/results/ragas_baseline_comparison.csv"

with open(baseline_file, encoding="utf-8") as f:
    results = json.load(f)

q01 = next(r for r in results if r["id"] == "Q01")

dataset = EvaluationDataset.from_list([{
    "user_input": q01["question"],
    "response": q01["answer"],
    "retrieved_contexts": q01["contexts"],
    "reference": q01["reference"],
}])

llm = LangchainLLMWrapper(
    ChatMistralAI(
        model=MODEL_NAME,
        api_key=MISTRAL_API_KEY,
        temperature=0,
    )
)

result = evaluate(
    dataset=dataset,
    metrics=[Faithfulness()],
    llm=llm,
    raise_exceptions=False,
)

score = result.to_pandas()["faithfulness"].iloc[0]

print(f"Faithfulness Q01 : {score}")

if pd.notna(score):
    df = pd.read_csv(scores_file)

    # Q01 correspond à la première ligne du CSV
    df.loc[0, "faithfulness"] = score

    df.to_csv(
        scores_file,
        index=False,
        encoding="utf-8-sig",
    )

    print("CSV mis à jour.")
    print("\nNouvelles moyennes :")
    print(df[
        [
            "faithfulness",
            "llm_context_precision_with_reference",
            "context_recall",
        ]
    ].mean())
else:
    print("Échec du recalcul : CSV non modifié.")
