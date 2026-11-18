# NBA Analyst AI — Assistant NBA RAG + SQL

**Projet 10 — Parcours Data Scientist / Machine Learning, OpenClassrooms**

Assistant conversationnel NBA développé avec **Python, Mistral AI, FAISS, SQLite et Streamlit**. Le projet fait évoluer un prototype de RAG documentaire vers un système capable de répondre à des questions textuelles, statistiques ou combinant les deux.

> **Statut : preuve de concept (POC).** Les résultats d'évaluation sont issus de campagnes archivées sur un jeu de test ciblé. Ils ne constituent pas une validation pour la production.

## Fonctionnement

Le routeur Mistral sélectionne une des quatre voies selon la question :

| Route | Source | Exemple |
|---|---|---|
| `rag` | Discussions NBA indexées dans FAISS | Pourquoi les Wolves ont-ils impressionné pendant les playoffs ? |
| `sql` | Statistiques de joueurs dans SQLite | Quels joueurs ont le meilleur NETRTG avec au moins 50 matchs ? |
| `hybrid` | FAISS + SQLite | Quels joueurs des Timberwolves sont commentés et quelles sont leurs statistiques ? |
| `out_of_scope` | Aucune | Question sans rapport avec la NBA |

```text
Question utilisateur
        |
        v
  Routeur Mistral
        |
        +--- RAG --------> Embeddings -> FAISS -> Extraits Reddit ---+
        |                                                           |
        +--- SQL --------> Génération SQL -> Validation -> SQLite ---+--> Mistral --> Réponse
        |                                                           |
        +--- HYBRID -----> FAISS + SQL ------------------------------+
        |
        +--- OUT_OF_SCOPE --> Refus contextualisé
```

**Distinction des sources :** les données chiffrées proviennent des lignes SQLite ; les commentaires et opinions proviennent des documents. Le prompt demande au modèle de ne pas attribuer les chiffres d'un joueur à un autre, de ne pas confondre saison régulière et playoffs et de signaler les informations absentes. Ces consignes ne garantissent pas à elles seules l'absence d'erreurs dans la réponse finale.

## Données et préparation

**Corpus documentaire :** discussions NBA issues de PDF, avec extraction de texte et recours à **EasyOCR** lorsque nécessaire. Les documents sont nettoyés, découpés en chunks, transformés en embeddings `mistral-embed`, puis indexés avec FAISS.

**Données structurées :** `inputs/regular NBA.xlsx`, importé dans `database/nba.db` (table `player_stats`) via `load_excel_to_db.py`. Les colonnes utilisées incluent notamment les joueurs, équipes, matchs, points, rebonds, passes, tentatives et réussite à trois points, TS% et NETRTG.

Configuration par défaut dans `utils/config.py` :

| Paramètre | Valeur |
|---|---|
| Modèle de génération | `mistral-small-latest` |
| Embeddings | `mistral-embed` |
| `CHUNK_SIZE` | `1500` |
| `CHUNK_OVERLAP` | `150` |
| `SEARCH_K` | `5` |

Les modèles identifiés par un alias `latest` peuvent évoluer indépendamment du code.

## Installation et exécution

Prérequis : Python compatible avec `requirements.txt`, accès à l'API Mistral et données d'entrée du projet.

```powershell
git clone https://github.com/ClementMouton/nba-rag-assistant_OCR_10.git
cd nba-rag-assistant_OCR_10
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Créer `.env` à partir de `.env.example`, puis renseigner :

```dotenv
MISTRAL_API_KEY=VOTRE_CLE_API
```

Préparer les données si les artefacts ne sont pas déjà disponibles :

```powershell
python load_excel_to_db.py
python indexer.py
```

Lancer l'interface :

```powershell
python -m streamlit run MistralChat.py
```

L'indexation peut nécessiter plusieurs minutes et des appels à l'API Mistral. Ne pas versionner le fichier `.env` ni sa clé API.

## Sécurité et observabilité

Le SQL Tool valide les requêtes générées avant exécution : lecture seule, instruction unique et tables autorisées. Les opérations de modification (`INSERT`, `UPDATE`, `DELETE`, `DROP`, etc.) sont rejetées. Cette validation limite le risque d'exécution de SQL non autorisé, sans garantir la pertinence métier de chaque requête.

Des traces **Logfire** sont intégrées au pipeline pour suivre notamment le routage, la récupération documentaire, l'interrogation SQL et la génération de réponse.

## Évaluation

L'évaluation compare le **prototype documentaire initial** et la **version enrichie RAG + SQL**, à partir de **12 questions archivées** : Q01–Q05 documentaires, Q06 hors périmètre, Q07–Q10 statistiques et Q11–Q12 hybrides.

### Questions documentaires — Q01 à Q05

| Métrique RAGAS | Prototype | Version enrichie |
|---|---:|---:|
| Faithfulness | 0,5002 | **0,8786** |
| Context Precision | 0,8186 | 0,8578 |
| Context Recall | 0,7000 | 0,7667 |

**Interprétation :** la Faithfulness mesurée augmente sur les réponses archivées. Toutefois, **les cinq passages récupérés sont identiques et dans le même ordre entre les deux versions, pour chacune des cinq questions**. Les différences de Context Precision et Context Recall ont donc été produites par des campagnes de notation distinctes sur les mêmes contextes : **elles ne prouvent pas une amélioration du retrieval**.

Le juge RAGAS peut également manquer une erreur factuelle : Q05 obtient une Faithfulness de `1,0000` malgré une mauvaise attribution de Jaden Ivey aux Timberwolves.

### SQL et routage

| Contrôle | Résultat archivé | Portée |
|---|---|---|
| Réponses statistiques du prototype, Q07–Q10 | **0/4** | Lecture des réponses textuelles |
| Résultats SQL de la version enrichie, Q07–Q10 | **4/4** | Comparaison automatique des lignes SQL aux valeurs attendues |
| Routage | **12/12** | Questions connues, reprises ou très proches des exemples du prompt |

Ces résultats montrent une **validation fonctionnelle sur les cas étudiés**, pas une performance généralisable à des questions inédites. Le `4/4` SQL ne garantit pas que la synthèse textuelle reproduit toujours les données correctement.

### Questions hybrides — Q11 et Q12

| Question | Faithfulness | Context Precision | Context Recall |
|---|---:|---:|---:|
| Q11 | 0,3750 | 0,0000 | 0,0000 |
| Q12 | 0,1316 | 0,0000 | 0,0000 |

Le juge reçoit **la réponse complète, mais seulement les passages FAISS comme contexte**, sans les lignes SQL. Les chiffres issus de SQLite peuvent donc être pénalisés à tort. En parallèle, une erreur de synthèse est bien observée : sur Q12, la réponse présente Banchero comme meilleur rebondeur d'Orlando avec 345 rebonds alors que les lignes SQL indiquent **490 rebonds pour Wendell Carter Jr.**

Les scores hybrides ne sont pas agrégés aux moyennes documentaires.

### Tests et reproductibilité

```powershell
python -m pytest -v
python evaluation/evaluate_sql.py
```

Un résultat de **25 tests passés** a été obtenu lors des vérifications du projet ; il ne constitue pas un résultat de CI actualisé à chaque commit.

Les scripts RAGAS présents dans `evaluation/` **réévaluent des réponses archivées** et peuvent **écraser les CSV de sortie**. Ils ne constituent pas à eux seuls une nouvelle génération des réponses. Les scores peuvent varier selon le juge, ses paramètres et l'évolution des modèles.

**Documentation et artefacts :**
- [Rapport d'évaluation (DOCX)](docs/Rapport_mise_en_place_evaluation_RAG_NBA.docx)
- [Protocole et résultats détaillés](docs/evaluation.md)
- [Cas de test](evaluation/test_cases.json)
- [Résultats archivés](evaluation/results/)
- [Script de vérification SQL](evaluation/evaluate_sql.py)

## Organisation du dépôt

```text
.
├── MistralChat.py              # Interface Streamlit
├── indexer.py                  # Préparation / indexation documentaire
├── load_excel_to_db.py         # Import Excel vers SQLite
├── inputs/                     # Documents et statistiques d'entrée
├── database/                   # Base SQLite
├── vector_db/                  # Index FAISS et chunks
├── utils/
│   ├── config.py               # Configuration
│   ├── rag_pipeline.py         # Routage, retrieval et génération
│   ├── sql_tool.py             # Génération et validation SQL
│   ├── vector_store.py         # Recherche vectorielle
│   └── observability.py        # Instrumentation
├── evaluation/                 # Jeux de test, scripts et archives
├── tests/                      # Tests automatisés
├── docs/
│   ├── evaluation.md
│   └── Rapport_mise_en_place_evaluation_RAG_NBA.docx
├── requirements.txt
├── .env.example
└── README.md
```

## Limites et perspectives

Le POC présente plusieurs limites : corpus documentaire bruité, recherche sémantique parfois peu pertinente sur les questions hybrides, erreurs possibles de synthèse malgré des lignes SQL correctes, évaluation sur un petit ensemble de questions connues, dépendance aux quotas et à la disponibilité de Mistral.

Les améliorations prioritaires seraient une **récupération documentaire plus ciblée** (reformulation, filtrage, reranking), une **vérification explicite des associations joueur–équipe–statistiques**, une **évaluation hybride séparant preuves SQL et preuves documentaires**, et un protocole de test avec questions inédites, répétitions et paramètres de juge contrôlés.

---

**Auteur :** Clément Mouton — Projet OpenClassrooms, parcours Data Scientist / Machine Learning.
