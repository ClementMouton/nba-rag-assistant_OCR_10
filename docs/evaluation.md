# Évaluation comparative du système RAG NBA

## 1. Objectif et périmètre

Ce document présente l'évaluation du prototype initial de recherche augmentée par génération (RAG) et de sa version enrichie, associant recherche documentaire, interrogation de données structurées par SQL et routage des questions.

L'objectif est de vérifier **ce que l'évolution de l'architecture améliore réellement**, tout en distinguant la qualité des réponses documentaires de l'exactitude des réponses statistiques. L'évaluation porte sur **12 questions (Q01 à Q12)**. Elle constitue une validation de preuve de concept (POC), et non une démonstration de robustesse en production.

Les deux versions comparées sont :

- **Prototype initial (`main`)** : traitement fondé sur le RAG documentaire.
- **Version enrichie (`develop`)** : routage des requêtes et mobilisation de SQL pour les données structurées, en complément du RAG documentaire.

> **Précaution de lecture :** les résultats ci-dessous correspondent aux réponses et évaluations archivées. Ils ne doivent pas être interprétés comme des mesures en temps réel des branches Git.

## 2. Jeu de test et méthode

Le jeu d'évaluation comporte plusieurs familles de questions :

| Questions | Catégorie | Objet de l'évaluation | Méthode retenue |
|---|---|---|---|
| Q01–Q05 | Documentaires (simples, complexes, formulation bruitée) | Fidélité aux extraits, pertinence des contextes récupérés | RAGAS et examen qualitatif |
| Q06 | Hors périmètre | Capacité à signaler l'absence d'information dans les sources | Examen qualitatif |
| Q07–Q10 | Statistiques (simples et complexes) | Exactitude des résultats calculés à partir des données NBA | Comparaison aux réponses de référence |
| Q11–Q12 | Hybrides (texte et statistiques) | Croisement de commentaires et de données chiffrées | Comparaison aux références et examen des justifications |

Les questions et les réponses attendues sont définies dans `evaluation/test_cases.json`. Les réponses archivées des deux versions sont conservées dans `evaluation/results/baseline_results.json` et `evaluation/results/hybrid_results.json`.

### 2.1. Construction du jeu de test

Le jeu de test a été construit pour couvrir les comportements attendus du système et les difficultés liées aux différentes sources. Il comprend cinq questions documentaires (Q01–Q05), dont une formulation volontairement bruitée ; une question hors périmètre (Q06) ; quatre questions statistiques avec filtres, classements ou calculs (Q07–Q10) ; et deux questions croisant commentaires textuels et statistiques individuelles (Q11–Q12).

Chaque question possède une réponse de référence établie à partir des sources du projet. Il s'agit d'une **évaluation fonctionnelle ciblée**, et non d'un échantillon statistiquement représentatif de toutes les requêtes possibles.

### 2.2. Métriques RAGAS

Trois métriques sont retenues pour **Q01–Q05** :

- **Faithfulness** : proportion des affirmations de la réponse jugées étayées par les contextes récupérés.
- **Context Precision** (`llm_context_precision_with_reference`) : capacité à classer les contextes pertinents en bonne position, en utilisant la référence.
- **Context Recall** (`context_recall`) : couverture des informations de la réponse de référence par les contextes récupérés.

Les scores vont de **0 à 1** (plus le score est élevé, mieux c'est). Ce sont des jugements automatiques assistés par un modèle de langage : ils ne remplacent pas une vérification humaine de l'exactitude factuelle.

Les questions SQL et hors périmètre ne sont **pas intégrées à la moyenne documentaire RAGAS**, car ces métriques ne mesurent pas directement l'exactitude d'un calcul SQL ou la qualité d'un refus.

### 2.3. Critères de réussite fonctionnelle

- **Questions statistiques :** conformité des joueurs, de leur classement, des valeurs numériques et des filtres demandés à la réponse de référence.
- **Question hors périmètre :** capacité à signaler que la réponse n'est pas présente dans les sources, sans présenter comme fondée une information non justifiée.
- **Questions hybrides :** évaluation séparée de la conformité des statistiques et de la pertinence des affirmations issues des documents. Une réponse statistiquement correcte n'est pas nécessairement une réponse hybride entièrement satisfaisante.

### 2.4. Conditions de comparaison

Les mêmes cinq questions documentaires et leurs références sont utilisées pour calculer les moyennes ci-dessous. Toutefois, les résultats du prototype et ceux de la version enrichie proviennent de **campagnes d'évaluation distinctes**. Les variations possibles du juge LLM et des conditions d'exécution empêchent d'attribuer avec certitude l'intégralité des écarts aux seules modifications du système.

Le recalcul documenté du prototype a été réalisé avec **RAGAS 0.4.3** et `mistral-small-latest` dans le dispositif d'évaluation. Le projet utilise également `mistral-small-latest` pour la génération. L'alias `latest` peut évoluer ; l'identité exacte des versions du modèle et de tous les paramètres des deux campagnes n'est pas établie.

Le calcul du prototype a initialement rencontré une erreur de parsing pour la Faithfulness de Q01. **Cette seule métrique a été relancée**, avec un résultat de **0,571429**, puis intégrée au CSV `evaluation/results/ragas_baseline_comparison.csv`. Les moyennes présentées pour le prototype reposent ainsi sur les cinq questions, sans valeur manquante.

## 3. Résultats documentaires — Q01 à Q05

| Métrique | Prototype `main` | Version enrichie `develop` | Écart absolu |
|---|---:|---:|---:|
| Faithfulness | **0,5002** | **0,8786** | **+0,3784** |
| Context Precision | 0,8186 | 0,8578 | +0,0392 |
| Context Recall | 0,7000 | 0,7667 | +0,0667 |

*Écarts exprimés en points sur l'échelle 0–1, et non en pourcentage relatif. Valeurs arrondies à quatre décimales.*

### 3.1. Interprétation

L'écart le plus important concerne la **Faithfulness** : dans cette évaluation, les réponses de la version enrichie sont davantage soutenues par les contextes fournis au juge. Les gains de **Context Precision** et de **Context Recall** sont plus limités.

Cette dissociation est importante : une réponse peut mieux exploiter les documents sans que la sélection des passages pertinents progresse dans les mêmes proportions. Les résultats suggèrent une amélioration de la fidélité documentaire **sur cet échantillon**, sans démontrer que le mécanisme de récupération est devenu systématiquement plus performant.

### 3.2. Faithfulness par question : comparaison des deux versions

| Question | Prototype `main` | Version enrichie `develop` |
|---|---:|---:|
| Q01 | 0,5714 | 0,6154 |
| Q02 | 0,9268 | 1,0000 |
| Q03 | 0,4706 | 1,0000 |
| Q04 | 0,1111 | 0,7778 |
| Q05 | 0,4211 | 1,0000 |
| **Moyenne** | **0,5002** | **0,8786** |

La progression est observée sur les cinq questions, mais particulièrement sur Q03, Q04 et Q05. Q01 reste relativement faible dans les deux versions. Les valeurs proviennent de campagnes distinctes : il ne s'agit pas d'une mesure de causalité à conditions parfaitement contrôlées.

### 3.3. Détail de la version enrichie

| Question | Faithfulness | Context Precision | Context Recall |
|---|---:|---:|---:|
| Q01 | 0,6154 | 0,5833 | 0,6667 |
| Q02 | 1,0000 | 1,0000 | 1,0000 |
| Q03 | 1,0000 | 0,9500 | 1,0000 |
| Q04 | 0,7778 | 1,0000 | 0,6667 |
| Q05 | 1,0000 | 0,7556 | 0,5000 |

Ces résultats révèlent une variabilité entre questions. En particulier, **Q05** obtient une Faithfulness de 1,0000 malgré une confusion factuelle relevée à la lecture de la réponse (attribution de Jaden Ivey aux Timberwolves). Ce cas illustre pourquoi une métrique automatique élevée **ne garantit pas une réponse entièrement correcte**.

## 4. Résultats fonctionnels — Q06 à Q12

### 4.1. Questions statistiques — Q07 à Q10

Les quatre questions statistiques portent notamment sur les pourcentages de réussite à trois points, le True Shooting Percentage et le NETRTG, avec des contraintes de nombre minimal de tentatives ou de matchs.

| Indicateur | Prototype `main` | Version enrichie `develop` |
|---|---:|---:|
| Réponses conformes aux références (Q07–Q10) | **0 / 4** | **4 / 4** |

L'amélioration est nette sur ce sous-ensemble : le recours aux données structurées et à SQL permet de traiter des classements et des filtres numériques que le prototype documentaire ne résolvait pas correctement. **Ce résultat porte sur quatre cas de test**, et non sur l'ensemble des requêtes SQL possibles.

### 4.2. Question hors périmètre — Q06

Q06 interroge le système sur le Ballon d'Or de football 2024, information extérieure aux sources NBA fournies. L'analyse des réponses archivées indique que la version enrichie produit un **refus plus concis et mieux délimité**, tandis que le prototype avait tendance à ajouter des digressions. Cette appréciation est **qualitative** : aucun score chiffré de qualité du refus n'est revendiqué.

### 4.3. Questions hybrides — Q11 et Q12

Q11 et Q12 demandent de rapprocher les commentaires sur les **Minnesota Timberwolves** et le **Orlando Magic** de statistiques individuelles. Les réponses de la version enrichie fournissent des statistiques conformes aux références enregistrées. Il s’agit donc d’une **réussite statistique partielle au regard de la réponse hybride complète**. En revanche, l'appui documentaire des commentaires attribués aux joueurs demeure perfectible.

Les résultats RAGAS archivés pour ces deux questions doivent être interprétés avec prudence :

| Question | Faithfulness | Context Precision | Context Recall |
|---|---:|---:|---:|
| Q11 | 0,3750 | 0,0000 | 0,0000 |
| Q12 | 0,1316 | 0,0000 | 0,0000 |

Ces scores signalent une faiblesse de la justification documentaire telle qu'évaluée, **sans suffire à invalider les résultats SQL**. Ils ne sont pas agrégés aux moyennes Q01–Q05, car ces questions combinent deux types de sources et nécessitent une grille d'évaluation spécifique.

## 5. Analyse des erreurs et limites observées

### 5.1. Q05 — Faithfulness élevée et erreur d'attribution

Q05, formulée volontairement avec des fautes (« pk les wolves ont impressioné pendant les playoff ? »), obtient une Faithfulness de **1,0000** pour `develop`. Pourtant, la réponse associe à tort **Jaden Ivey aux Timberwolves**, alors que le passage documentaire concerné traite des **Pistons**. Une Faithfulness élevée ne garantit donc ni l'exactitude factuelle ni la conformité à la référence. La vérification qualitative reste indispensable.

### 5.2. Q11 et Q12 — Justification documentaire des réponses hybrides

Les réponses aux questions hybrides contiennent des statistiques conformes aux références, mais les affirmations documentaires associées sont insuffisamment justifiées. Les scores archivés sont faibles (Faithfulness **0,3750** pour Q11 et **0,1316** pour Q12 ; Context Precision et Context Recall **0,0000** pour les deux).

Ces métriques doivent être interprétées prudemment : elles ne mesurent pas nécessairement correctement une réponse mêlant SQL et documents, notamment lorsque les résultats SQL ne figurent pas parmi les contextes transmis au juge. Elles ne permettent pas, à elles seules, d'invalider les résultats numériques.

### 5.3. Qualité des sources

Les PDF issus de discussions Reddit comportent du bruit d'extraction : éléments d'interface, fragments de pages, texte mal segmenté et contenus sans rapport avec les questions. Ces défauts peuvent affecter à la fois la récupération et la génération.

### 5.4. Enseignements

Ces erreurs montrent qu'il faut distinguer **conformité à la référence**, **fidélité aux contextes récupérés** et **traçabilité des affirmations**. Le traitement SQL apporte un gain clair sur les questions structurées, mais la fiabilité documentaire demeure un axe d'amélioration prioritaire.

## 6. Limites méthodologiques

**Taille et représentativité du jeu de test.** Les douze questions couvrent les principales capacités du POC, sans constituer un échantillon représentatif des requêtes possibles. Les taux observés ne peuvent pas être généralisés à une utilisation en production.

**Variabilité des métriques automatiques.** Les métriques RAGAS font intervenir un modèle de langage juge. Les scores peuvent varier selon sa configuration et les conditions d'exécution ; une seule évaluation ne permet pas de quantifier cette variabilité.

**Comparabilité des campagnes.** Les mêmes cinq questions documentaires et leurs références sont utilisées, mais les résultats proviennent de campagnes distinctes dont l'identité complète des paramètres n'a pas été établie. Les écarts sont des **améliorations observées**, non une preuve causale de l'effet des modifications.

**Absence de répétitions.** Chaque version est représentée par une réponse archivée par question. Il n'est pas possible de mesurer la stabilité de génération ni de calculer des intervalles de confiance fiables sur ces seules observations.

**Périmètre des performances.** L'évaluation ne permet pas de conclure sur les coûts, la latence en charge, la concurrence d'utilisateurs ou la robustesse en production.

### 6.1. Scores historiques non retenus dans la comparaison principale

Une évaluation antérieure du prototype a produit **Faithfulness 0,2864**, **Context Precision 0,3412**, **Context Recall 0,3472** et **Answer Relevancy `NaN`**. Le périmètre et le protocole exacts n'ont pas été suffisamment reconstitués. Ces valeurs sont conservées pour l'historique, mais ne sont pas utilisées comme baseline dans la comparaison principale.

Pour renforcer le protocole, il conviendrait de réévaluer les deux versions lors d'une même campagne, avec un juge et une configuration identiques, plusieurs générations par question et un jeu de test élargi.

## 7. Perspectives d'amélioration

### 7.1. Améliorer la récupération documentaire

Les difficultés sur Q11 et Q12 justifient l'expérimentation d'un **reranking**, d'une meilleure segmentation des documents et d'un nettoyage plus approfondi des PDF. Ces pistes restent à tester et ne sont pas présentées comme des améliorations déjà obtenues.

### 7.2. Renforcer la vérification factuelle et la traçabilité

L'erreur de Q05 appelle un contrôle plus strict des associations entre joueurs, équipes et commentaires. Les réponses pourraient distinguer explicitement les informations provenant de **SQL** de celles provenant des **documents**, en rattachant chaque affirmation aux sources qui la soutiennent.

### 7.3. Renforcer le protocole d'évaluation

Un jeu de test élargi devrait couvrir davantage de reformulations, d'ambiguïtés et de cas limites. Une campagne comparative commune aux deux versions, idéalement répétée, ainsi que l'automatisation de l'évaluation faciliteraient le suivi des performances après chaque modification.

## 8. Conclusion

Sur le jeu de test retenu, la version enrichie présente une **amélioration observée de la Faithfulness documentaire** (**0,5002 → 0,8786** sur Q01–Q05) et un **gain fonctionnel marqué sur les questions statistiques** (**0/4 → 4/4 réponses conformes** sur Q07–Q10). Le routage et l'interrogation SQL constituent les apports les plus directement démontrables de l'évolution architecturale.

Les gains de récupération documentaire sont plus modestes et des erreurs factuelles ou d'attribution subsistent, en particulier dans les réponses hybrides. L'évaluation soutient l'intérêt du POC, mais ne démontre ni une fiabilité générale ni une aptitude immédiate à la production.

## 9. Traçabilité et reproductibilité

| Ressource | Rôle |
|---|---|
| `evaluation/test_cases.json` | Questions, catégories et réponses de référence |
| `evaluation/results/baseline_results.json` | Réponses archivées du prototype |
| `evaluation/results/hybrid_results.json` | Réponses archivées de la version enrichie |
| `evaluation/results/ragas_baseline_comparison.csv` | Scores documentaires recalculés du prototype, Q01–Q05 (à conserver dans le dépôt) |
| `evaluation/results/ragas_hybrid_rag_scores.csv` | Scores RAGAS archivés de la version enrichie, dont Q01–Q05 et Q11–Q12 |
| `evaluation/run_ragas_baseline_comparison.py` | Script de recalcul de la baseline documentaire |
| `evaluation/retry_baseline_q01.py` | Recalcul ciblé de la Faithfulness de Q01 |

**Reproductibilité :** les moyennes du tableau principal doivent pouvoir être recalculées à partir des CSV archivés. Le fichier `ragas_baseline_comparison.csv` a été mis à jour localement après le recalcul de Q01 ; vérifier sa présence dans le dépôt avant publication de ce document.

Les réponses et scores archivés permettent de retracer les calculs, sans garantir une reproduction strictement identique : le juge LLM et l’alias `mistral-small-latest` peuvent évoluer.
