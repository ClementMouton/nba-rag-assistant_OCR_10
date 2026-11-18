# MÉTHODOLOGIE — Recalcul RAGAS du prototype documentaire
# Ce script sélectionne Q01 à Q05 dans les réponses baseline archivées,
# puis transmet question, réponse, contextes et référence au juge RAGAS.
# Il ne lance pas une nouvelle génération de réponses du prototype.
# Les cinq passages récupérés par question sont identiques et ordonnés
# de la même façon dans les deux archives comparées. Les différences
# de Context Precision/Recall entre campagnes ne démontrent donc pas
# une amélioration de la récupération documentaire.
# Le CSV de sortie est écrasé à chaque nouvelle exécution ; le modèle
# désigné par l'alias latest peut aussi évoluer entre campagnes.


import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
)
from langchain_mistralai import ChatMistralAI
from utils.config import MISTRAL_API_KEY, MODEL_NAME

BASELINE_FILE = PROJECT_ROOT / "evaluation/results/baseline_results.json"
OUTPUT_FILE = PROJECT_ROOT / "evaluation/results/ragas_baseline_comparison.csv"

def main():
    with open(BASELINE_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    # Uniquement les cinq questions documentaires
    results = [
        r for r in results
        if r["id"] in {"Q01", "Q02", "Q03", "Q04", "Q05"}
        and not r.get("error")
    ]

    samples = [
        {
            "user_input": r["question"],
            "response": r["answer"],
            "retrieved_contexts": r["contexts"],
            "reference": r["reference"],
        }
        for r in results
    ]

    print(f"Questions sélectionnées : {[r['id'] for r in results]}")
    assert len(samples) == 5, "Il faut exactement 5 questions."

    dataset = EvaluationDataset.from_list(samples)

    evaluator_llm = LangchainLLMWrapper(
        ChatMistralAI(
            model=MODEL_NAME,
            api_key=MISTRAL_API_KEY,
            temperature=0,
        )
    )

    metrics = [
        Faithfulness(),
        LLMContextPrecisionWithReference(),
        LLMContextRecall(),
    ]

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=evaluator_llm,
        raise_exceptions=False,
    )

    df = result.to_pandas()
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("\nScores moyens :")
    print(df[
        [
            "faithfulness",
            "llm_context_precision_with_reference",
            "context_recall",
        ]
    ].mean())

    print(f"\nRésultats enregistrés : {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
