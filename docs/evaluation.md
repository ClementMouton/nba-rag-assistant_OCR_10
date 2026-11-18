# Évaluation comparative du système RAG NBA

## 1. Objectif et périmètre

Ce document présente l'évaluation d'un prototype initial de recherche augmentée par génération (RAG) et de sa version enrichie, associant recherche documentaire, interrogation de données structurées par SQL et routage des questions.

L'objectif est de mesurer les performances observées, d'identifier les apports de l'architecture hybride et de distinguer les améliorations démontrées des limites du protocole d'évaluation.

L'évaluation porte sur **12 questions (Q01 à Q12)**. Elle constitue une validation fonctionnelle d'une preuve de concept (POC), et non une démonstration de robustesse en production.

Deux versions historiques sont comparées :

- **Prototype initial (baseline)** : architecture fondée sur la recherche documentaire FAISS et la génération de réponses.
- **Version enrichie (hybride)** : architecture associant routage, recherche documentaire FAISS et interrogation SQL des statistiques NBA.

Les appellations *baseline* et *hybride* désignent ici les deux états fonctionnels du système au moment des évaluations. Elles ne correspondent pas aux branches Git actuelles, désormais fusionnées.

Les résultats présentés proviennent des réponses et évaluations archivées dans le dépôt.

## 2. Jeu de test et méthodologie

### 2.1. Composition du jeu de test

Le jeu d'évaluation comprend quatre catégories de questions :

| Questions | Catégorie | Objectif |
|---|---|---|
| Q01–Q05 | Documentaires | Évaluer la pertinence des informations récupérées et la fidélité des réponses aux documents |
| Q06 | Hors périmètre | Vérifier la capacité du système à reconnaître une question extérieure aux sources |
| Q07–Q10 | Statistiques | Vérifier les calculs, filtres et classements issus des données NBA |
| Q11–Q12 | Hybrides | Évaluer la combinaison de commentaires documentaires et de statistiques individuelles |

Les questions et leurs références sont définies dans `evaluation/test_cases.json`.

Les réponses archivées sont conservées dans :

- `evaluation/results/baseline_results.json`
- `evaluation/results/hybrid_results.json`

Le jeu de test a été conçu pour couvrir les principales fonctionnalités du POC, notamment les requêtes documentaires complexes, les formulations bruitées, les classements statistiques et les questions combinant plusieurs sources.

**Limite :** les douze questions constituent un échantillon fonctionnel ciblé. Elles ne sont pas statistiquement représentatives de l'ensemble des requêtes possibles.

### 2.2. Métriques RAGAS

Trois métriques principales sont retenues pour l'évaluation documentaire des questions Q01 à Q05.

**Faithfulness**

Mesure la proportion des affirmations de la réponse que le juge considère comme étayées par les contextes fournis.

**Context Precision**

Évalue le positionnement des passages pertinents parmi les contextes récupérés, à partir de la réponse de référence.

**Context Recall**

Mesure dans quelle proportion les informations nécessaires à la réponse de référence sont présentes dans les contextes récupérés.

Les scores sont compris entre 0 et 1, une valeur élevée étant généralement préférable.

Ces métriques reposent sur un modèle de langage évaluateur. Elles doivent être interprétées comme des indicateurs automatiques, et non comme une validation humaine exhaustive.

La métrique `ResponseRelevancy`, présente dans une évaluation historique, a produit des valeurs `NaN`. Elle n'est pas retenue dans la comparaison principale.

### 2.3. Conditions d'évaluation

Les évaluations utilisent les réponses archivées des deux versions du système.

Pour les questions documentaires, les mêmes questions et réponses de référence sont utilisées.

Le recalcul documenté de la baseline utilise RAGAS 0.4.3 et le modèle `mistral-small-latest`.

L'alias `latest` peut évoluer dans le temps. L'identité exacte des versions du modèle et l'ensemble des paramètres des différentes campagnes ne sont pas entièrement établis.

Les scores proviennent donc de campagnes distinctes, ce qui limite leur comparabilité stricte.

Une erreur de parsing du juge RAGAS avait initialement empêché le calcul de la Faithfulness de Q01 pour la baseline.

Cette seule métrique a été recalculée avec `evaluation/retry_baseline_q01.py`, donnant un score de **0,571429**, ensuite intégré au fichier de comparaison.

## 3. Évaluation documentaire — Q01 à Q05

### 3.1. Résultats comparatifs

| Métrique | Baseline | Version hybride | Écart |
|---|---:|---:|---:|
| Faithfulness | 0,5002 | 0,8786 | +0,3784 |
| Context Precision | 0,8186 | 0,8578 | +0,0392 |
| Context Recall | 0,7000 | 0,7667 | +0,0667 |

Les écarts sont exprimés en points sur une échelle de 0 à 1.

La progression la plus importante concerne la Faithfulness.

Les réponses documentaires de la version enrichie sont davantage considérées comme étayées par les contextes fournis au juge.

En revanche, les variations de Context Precision et de Context Recall ne permettent pas de conclure à une amélioration effective du mécanisme de récupération.

### 3.2. Vérification des passages récupérés

Une comparaison des résultats archivés montre que, pour chacune des cinq questions Q01 à Q05, **les cinq passages FAISS récupérés sont exactement identiques et apparaissent dans le même ordre dans les deux versions**.

Cette observation est déterminante pour l'interprétation des résultats.

Elle signifie que :

- La version enrichie ne démontre aucune amélioration de la sélection des passages documentaires sur ces cinq questions.
- Les écarts de Context Precision et de Context Recall ne peuvent pas être attribués à une modification des passages récupérés.
- Ces écarts peuvent notamment provenir de la variabilité du modèle évaluateur ou des conditions d'évaluation.

L'amélioration de Faithfulness constitue donc une **amélioration observée de la fidélité des réponses aux contextes**, telle que mesurée par RAGAS, et non une amélioration démontrée du retrieval.

Il n'est pas possible d'attribuer causalement cette progression à une modification précise du système à partir des seules campagnes archivées.

### 3.3. Faithfulness par question

| Question | Baseline | Version hybride |
|---|---:|---:|
| Q01 | 0,5714 | 0,6154 |
| Q02 | 0,9268 | 1,0000 |
| Q03 | 0,4706 | 1,0000 |
| Q04 | 0,1111 | 0,7778 |
| Q05 | 0,4211 | 1,0000 |
| **Moyenne** | **0,5002** | **0,8786** |

Une progression est observée sur les cinq questions, particulièrement sur Q03, Q04 et Q05.

Q01 demeure la question la moins bien évaluée en Faithfulness dans la version enrichie.

### 3.4. Détail des scores documentaires de la version enrichie

| Question | Faithfulness | Context Precision | Context Recall |
|---|---:|---:|---:|
| Q01 | 0,6154 | 0,5833 | 0,6667 |
| Q02 | 1,0000 | 1,0000 | 1,0000 |
| Q03 | 1,0000 | 0,9500 | 1,0000 |
| Q04 | 0,7778 | 1,0000 | 0,6667 |
| Q05 | 1,0000 | 0,7556 | 0,5000 |

Ces résultats montrent une variabilité importante entre questions.

Ils doivent être complétés par une vérification qualitative, notamment pour détecter les erreurs d'attribution que le juge automatique peut ne pas identifier.

## 4. Évaluation fonctionnelle — Q06 à Q12

### 4.1. Questions statistiques — Q07 à Q10

Les questions statistiques portent notamment sur :

- Les pourcentages de réussite à trois points.
- Les classements de joueurs.
- Les seuils minimaux de tentatives ou de matchs joués.
- Le True Shooting Percentage et le Net Rating.

Les évaluations archivées présentent les résultats suivants :

| Indicateur | Baseline | Version hybride |
|---|---:|---:|
| Cas conformes selon le protocole utilisé | 0/4 | 4/4 |

**Ces résultats ne proviennent toutefois pas de méthodes d'évaluation strictement identiques.**

Pour la baseline, le résultat 0/4 correspond à une appréciation manuelle des réponses textuelles générées par le prototype documentaire.

Pour la version hybride, le résultat 4/4 provient de `evaluation/evaluate_sql.py`, qui compare les lignes de résultats SQL archivées aux valeurs de référence attendues.

Cette évaluation valide donc les résultats structurés retournés par SQL sur les quatre cas considérés.

Elle ne démontre pas automatiquement que les réponses finales rédigées par le modèle sont entièrement exactes.

Les valeurs 0/4 et 4/4 décrivent deux observations distinctes et ne constituent pas une mesure comparative parfaitement symétrique.

Elles soutiennent néanmoins l'intérêt de l'intégration de SQLite pour répondre à des questions nécessitant des calculs et classements statistiques.

### 4.2. Question hors périmètre — Q06

La question Q06 concerne le Ballon d'Or de football 2024, information extérieure au corpus NBA.

La version enrichie fournit un refus plus concis et mieux délimité que le prototype initial.

Cette appréciation repose sur une analyse qualitative des réponses archivées.

Aucun score quantitatif de qualité du refus n'est revendiqué.

### 4.3. Questions hybrides — Q11 et Q12

Les questions hybrides demandent de rapprocher les commentaires documentaires des statistiques de joueurs.

Elles concernent notamment les Minnesota Timberwolves et l'Orlando Magic.

La version enrichie mobilise les deux sources, mais les résultats montrent des limites importantes dans la synthèse finale.

**Q11**

La réponse combine des informations documentaires et des résultats statistiques.

Cependant, les affirmations documentaires restent insuffisamment justifiées selon les résultats RAGAS archivés.

**Q12**

Une erreur factuelle est présente dans la réponse générée.

Le système présente Paolo Banchero comme le meilleur rebondeur d'Orlando avec 345 rebonds.

Or les résultats SQL archivés indiquent que **Wendell Carter Jr. possède 490 rebonds**, contre 345 pour Paolo Banchero.

La valeur de 345 rebonds est correcte pour Banchero, mais le classement affirmé dans la réponse est incorrect.

Ce cas montre qu'un résultat SQL correct ne garantit pas une interprétation correcte par le modèle de synthèse.

### 4.4. Scores RAGAS hybrides

| Question | Faithfulness | Context Precision | Context Recall |
|---|---:|---:|---:|
| Q11 | 0,3750 | 0,0000 | 0,0000 |
| Q12 | 0,1316 | 0,0000 | 0,0000 |

Ces résultats nécessitent une précaution méthodologique importante.

Dans `evaluation/run_ragas_hybrid.py`, le juge RAGAS reçoit :

- La question utilisateur.
- La réponse complète générée par le système.
- Les passages documentaires récupérés par FAISS.
- La réponse de référence.

**Les lignes de résultats SQL ne sont pas intégrées aux contextes transmis au juge.**

Par conséquent, les affirmations statistiques présentes dans la réponse peuvent ne pas être considérées comme justifiées, même lorsqu'elles reposent sur des résultats SQLite corrects.

Les faibles scores de Faithfulness ne permettent donc pas, à eux seuls, de mesurer correctement la qualité statistique des réponses hybrides.

Ils ne doivent cependant pas être ignorés : l'erreur factuelle identifiée dans Q12 montre qu'il existe également des problèmes réels de synthèse.

Ces questions nécessitent une évaluation distincte de la récupération documentaire, de l'exactitude SQL et de la cohérence de la réponse finale.

## 5. Analyse des erreurs observées

### 5.1. Q05 — Erreur d'attribution malgré une Faithfulness maximale

La question Q05 est volontairement formulée avec des fautes :

« pk les wolves ont impressioné pendant les playoff ? »

La version enrichie obtient une Faithfulness de 1,0000.

Pourtant, la réponse attribue à tort Jaden Ivey aux Minnesota Timberwolves, alors que le joueur appartient aux Detroit Pistons.

Cette erreur illustre une limite des métriques automatiques : une réponse peut être jugée fidèle aux passages fournis tout en contenant une attribution factuelle incorrecte.

### 5.2. Q12 — Erreur de classement dans la synthèse hybride

Le cas Q12 met en évidence une erreur différente.

Les données SQL contiennent les valeurs nécessaires pour identifier le meilleur rebondeur d'Orlando.

Le modèle utilise cependant une valeur correcte pour Paolo Banchero et en tire une conclusion incorrecte sur son classement.

Cette erreur intervient au niveau de la synthèse de la réponse, et non nécessairement au niveau de l'exécution SQL.

Elle justifie l'ajout futur de contrôles de cohérence entre les lignes structurées et les affirmations générées.

### 5.3. Qualité des sources documentaires

Les PDF issus des discussions Reddit contiennent des éléments susceptibles de dégrader la qualité du système :

- Éléments d'interface et bruit d'extraction.
- Fragments de commentaires.
- Informations sans rapport direct avec les questions.
- Risques de confusion entre joueurs, équipes et discussions.

Ces problèmes peuvent affecter la segmentation, la récupération des passages et leur interprétation.

### 5.4. Enseignements

Les erreurs observées soulignent la nécessité de distinguer trois dimensions :

1. **La qualité de la récupération** : les passages nécessaires sont-ils disponibles ?
2. **L'exactitude des données structurées** : les résultats SQL correspondent-ils aux références ?
3. **La qualité de la synthèse** : la réponse finale interprète-t-elle correctement les informations fournies ?

Une amélioration sur l'une de ces dimensions ne garantit pas une amélioration sur les autres.

## 6. Limites méthodologiques

### 6.1. Taille du jeu de test

Le jeu comprend seulement douze questions.

Il permet une validation fonctionnelle ciblée, mais ne constitue pas un échantillon représentatif des usages possibles.

Les résultats ne peuvent pas être extrapolés à une utilisation en production.

### 6.2. Comparabilité des campagnes documentaires

Les évaluations ont été réalisées lors de campagnes distinctes.

Même lorsque les questions, références et passages récupérés sont identiques, les variations du juge LLM peuvent influencer les scores.

Les différences de métriques ne doivent pas être considérées comme des preuves causales de l'effet des modifications architecturales.

### 6.3. Comparabilité des évaluations SQL

La baseline a été évaluée à partir des réponses textuelles.

La version enrichie a été évaluée à partir des résultats SQL archivés.

Une comparaison rigoureuse nécessiterait d'appliquer une même grille aux réponses finales des deux versions.

### 6.4. Biais du jeu de routage

Les douze questions utilisées pour tester le routage sont identiques ou très proches de certains exemples présents dans les prompts.

De plus, plusieurs questions statistiques sont représentées dans les exemples fournis au modèle de génération SQL.

Le résultat de routage de **12/12 sur les cas connus** démontre le bon fonctionnement du système sur ces exemples, mais ne permet pas de conclure à sa capacité de généralisation sur des questions inédites.

### 6.5. Évaluation incomplète des réponses hybrides

Le juge RAGAS ne reçoit pas les lignes SQL comme contexte de justification.

Le protocole ne mesure donc pas complètement la fidélité des réponses hybrides à l'ensemble des sources utilisées.

Une évaluation plus complète devrait transmettre les résultats structurés pertinents et vérifier séparément les affirmations numériques.

### 6.6. Variabilité et absence de répétitions

Les réponses archivées ne permettent pas d'estimer la stabilité des générations sur plusieurs exécutions.

Les métriques ne sont pas accompagnées d'intervalles de confiance.

L'alias `mistral-small-latest` peut également évoluer entre deux campagnes.

### 6.7. Performances opérationnelles

L'évaluation ne couvre pas de manière systématique :

- La latence sous charge.
- Les coûts d'inférence.
- La concurrence entre utilisateurs.
- La robustesse à grande échelle.
- La résistance à des formulations inédites ou adversariales.

Ces dimensions restent hors du périmètre de la validation réalisée.

### 6.8. Scores historiques non retenus

Une évaluation antérieure de la baseline a produit les résultats suivants :

| Métrique | Score historique |
|---|---:|
| Faithfulness | 0,2864 |
| Context Precision | 0,3412 |
| Context Recall | 0,3472 |
| Answer Relevancy | NaN |

Le périmètre exact de cette campagne n'a pas été suffisamment reconstitué.

Ces résultats sont conservés pour assurer la traçabilité, mais ne sont pas utilisés dans la comparaison principale.

## 7. Perspectives d'amélioration

### 7.1. Améliorer la préparation documentaire

Un nettoyage plus approfondi des PDF pourrait réduire le bruit documentaire.

Une expérimentation sur les paramètres de chunking et l'ajout d'un reranking pourraient également être envisagés.

Ces pistes ne sont pas présentées comme des améliorations déjà démontrées.

### 7.2. Renforcer la vérification factuelle

Les erreurs Q05 et Q12 justifient des contrôles supplémentaires :

- Vérification des associations entre joueurs et équipes.
- Contrôle des classements et valeurs numériques issus de SQL.
- Vérification de la cohérence entre résultats structurés et réponse générée.
- Attribution explicite des affirmations aux sources utilisées.

### 7.3. Adapter l'évaluation hybride

Une évolution du protocole pourrait combiner :

- Des métriques documentaires RAGAS.
- Une comparaison déterministe des résultats SQL.
- Une vérification des affirmations numériques dans les réponses finales.
- Une évaluation humaine de la cohérence des synthèses hybrides.

Cette séparation permettrait d'identifier plus précisément les erreurs de récupération, d'exécution et de génération.

### 7.4. Renforcer la robustesse du protocole

Une campagne future devrait inclure davantage de questions inédites, de reformulations, de cas limites et de répétitions.

L'utilisation d'un modèle juge fixé à une version précise faciliterait également la comparaison des résultats.

## 8. Conclusion

L'évaluation met en évidence plusieurs apports de la version enrichie du système RAG NBA.

**Sur les questions documentaires**, la Faithfulness moyenne observée progresse de **0,5002 à 0,8786**.

Cette progression concerne les réponses évaluées, mais ne démontre pas une amélioration de la récupération : les cinq passages FAISS utilisés pour chaque question Q01–Q05 sont identiques dans les deux versions.

**Sur les questions statistiques**, la version enrichie obtient **4/4 résultats SQL conformes aux références** sur les cas Q07–Q10.

Ce résultat soutient l'intérêt de l'intégration de données structurées, mais il n'est pas directement comparable au 0/4 obtenu par appréciation manuelle des réponses textuelles du prototype.

**Sur les questions hybrides**, les résultats restent plus contrastés.

La combinaison de SQL et de recherche documentaire fonctionne techniquement, mais la synthèse peut produire des erreurs factuelles, comme le classement incorrect identifié dans Q12.

Le protocole RAGAS présente également une limite : les résultats SQL ne sont pas fournis au juge comme contextes justificatifs.

Le POC démontre ainsi l'intérêt d'une architecture combinant recherche documentaire et interrogation SQL, tout en mettant en évidence les besoins de vérification factuelle, de traçabilité et d'amélioration du protocole d'évaluation.

Les résultats ne permettent pas de conclure à une fiabilité générale du système ni à son aptitude immédiate à une utilisation en production.

## 9. Traçabilité et reproductibilité

Les fichiers suivants permettent de retrouver les questions, les réponses, les évaluations et les résultats archivés.

| Ressource | Rôle |
|---|---|
| `evaluation/test_cases.json` | Questions, catégories et réponses de référence |
| `evaluation/results/baseline_results.json` | Réponses archivées du prototype initial |
| `evaluation/results/hybrid_results.json` | Réponses archivées de la version enrichie |
| `evaluation/results/ragas_baseline_scores.csv` | Résultats historiques RAGAS de la baseline |
| `evaluation/results/ragas_baseline_comparison.csv` | Résultats documentaires recalculés de la baseline |
| `evaluation/results/ragas_hybrid_rag_scores.csv` | Scores RAGAS documentaires et hybrides |
| `evaluation/results/ragas_hybrid_sql_scores.csv` | Résultats archivés associés à l'évaluation SQL |
| `evaluation/results/sql_evaluation.json` | Comparaisons fonctionnelles des résultats SQL |
| `evaluation/run_ragas.py` | Script historique d'évaluation de la baseline |
| `evaluation/run_ragas_baseline_comparison.py` | Recalcul des scores documentaires Q01–Q05 |
| `evaluation/retry_baseline_q01.py` | Recalcul ciblé de Faithfulness pour Q01 |
| `evaluation/run_ragas_hybrid.py` | Évaluation RAGAS des réponses de la version enrichie |
| `evaluation/evaluate_sql.py` | Vérification des résultats SQL archivés |
| `utils/rag_pipeline.py` | Routage et orchestration des réponses |
| `utils/vector_store.py` | Indexation et recherche FAISS |
| `utils/sql_tool.py` | Génération, validation et exécution des requêtes SQL |
| `docs/Rapport_mise_en_place_evaluation_RAG_NBA.docx` | Rapport de synthèse méthodologique et critique |

### Précautions de reproduction

Les scripts d'évaluation RAGAS relisent les réponses archivées. Ils ne reproduisent pas nécessairement la génération initiale des réponses.

Certains scripts réécrivent leurs fichiers CSV ou JSON de sortie.

Il est donc recommandé de travailler sur une copie du dépôt et de conserver les résultats archivés avant toute nouvelle exécution.

Les métriques faisant intervenir un modèle juge, leur reproduction numérique exacte n'est pas garantie, notamment lorsque l'alias `mistral-small-latest` désigne une version différente du modèle.

Les résultats présentés dans ce document correspondent aux campagnes archivées et doivent être interprétés dans les limites méthodologiques décrites précédemment.