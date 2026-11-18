# MÉTHODOLOGIE — Vérification ciblée du SQL Tool
# Les contrôles exercés ici concernent les comportements définis
# dans ce script ; ils ne remplacent pas une évaluation complète
# de l'exactitude métier des réponses rédigées par le modèle.

from utils.rag_pipeline import RAGPipeline


rag = RAGPipeline()

questions = [
    # RAG
    "Quelles équipes ont impressionné les commentateurs pendant les playoffs ?",

    # SQL
    "Qui est le joueur le plus précis à trois points parmi ceux qui en ont tenté au moins 100 ?",

    # HYBRID
    (
        "Quels joueurs des Minnesota Timberwolves sont mis en avant "
        "par les commentateurs et que montrent leurs statistiques "
        "individuelles disponibles ?"
    ),
]


for question in questions:

    print("\n" + "=" * 80)

    result = rag.ask(question)

    print("QUESTION :", result["question"])
    print("ROUTE :", result["route"])
    print("SQL :", result["sql"])
    print("SQL RESULTS :", result["sql_results"])
    print("SOURCES :", result["sources"])

    print("\nRÉPONSE :")
    print(result["answer"])