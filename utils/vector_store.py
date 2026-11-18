# MÉTHODOLOGIE — Indexation et recherche sémantique
# Les documents textuels sont segmentés avec un chevauchement configurable,
# encodés avec mistral-embed et indexés localement dans FAISS.
# Les chunks et leurs métadonnées sont conservés dans un artefact distinct :
# la correspondance entre positions de l'index et chunks est indispensable.
# La recherche restitue les passages voisins de la question vectorisée ;
# la proximité vectorielle ne garantit ni pertinence métier ni exactitude.
# L'index doit être reconstruit lorsque les sources ou paramètres changent.


# utils/vector_store.py

import logging
import os
import pickle
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from mistralai import Mistral

from .config import (
    MISTRAL_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE,
    FAISS_INDEX_FILE,
    DOCUMENT_CHUNKS_FILE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class VectorStoreManager:
    """Gère la création, le chargement et la recherche dans un index FAISS."""

    def __init__(self):

        self.index: Optional[faiss.Index] = None
        self.document_chunks: List[Dict[str, Any]] = []

        if not MISTRAL_API_KEY:
            raise ValueError(
                "La clé API Mistral (MISTRAL_API_KEY) n'est pas définie."
            )

        self.mistral_client = Mistral(
            api_key=MISTRAL_API_KEY
        )

        self._load_index_and_chunks()

    # ========================================================
    # Chargement de l'index et des chunks
    # ========================================================

    def _load_index_and_chunks(self):
        """Charge l'index FAISS et les chunks s'ils existent."""

        if (
            os.path.exists(FAISS_INDEX_FILE)
            and os.path.exists(DOCUMENT_CHUNKS_FILE)
        ):

            try:

                logging.info(
                    "Chargement de l'index FAISS depuis %s...",
                    FAISS_INDEX_FILE,
                )

                loaded_index = faiss.read_index(
                    FAISS_INDEX_FILE
                )

                logging.info(
                    "Chargement des chunks depuis %s...",
                    DOCUMENT_CHUNKS_FILE,
                )

                with open(DOCUMENT_CHUNKS_FILE, "rb") as f:
                    loaded_chunks = pickle.load(f)

                if loaded_index.ntotal != len(loaded_chunks):
                    raise ValueError(
                        "Incohérence entre le nombre de vecteurs "
                        f"({loaded_index.ntotal}) et le nombre de "
                        f"chunks ({len(loaded_chunks)})."
                    )

                self.index = loaded_index
                self.document_chunks = loaded_chunks

                logging.info(
                    "Index (%s vecteurs) et %s chunks chargés.",
                    self.index.ntotal,
                    len(self.document_chunks),
                )

            except Exception as e:

                logging.error(
                    "Erreur lors du chargement de l'index/chunks : %s",
                    e,
                )

                self.index = None
                self.document_chunks = []

        else:

            logging.warning(
                "Fichiers d'index FAISS ou de chunks non trouvés. "
                "L'index est vide."
            )

    # ========================================================
    # Découpage des documents
    # ========================================================

    def _split_documents_to_chunks(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Découpe les documents en chunks avec leurs métadonnées."""

        logging.info(
            "Découpage de %s documents en chunks "
            "(taille=%s, chevauchement=%s)...",
            len(documents),
            CHUNK_SIZE,
            CHUNK_OVERLAP,
        )

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            add_start_index=True,
        )

        all_chunks = []

        for doc_counter, doc in enumerate(documents):

            langchain_doc = Document(
                page_content=doc["page_content"],
                metadata=doc["metadata"],
            )

            chunks = text_splitter.split_documents(
                [langchain_doc]
            )

            logging.info(
                "Document '%s' découpé en %s chunks.",
                doc["metadata"].get("filename", "N/A"),
                len(chunks),
            )

            for i, chunk in enumerate(chunks):

                chunk_dict = {
                    "id": f"{doc_counter}_{i}",
                    "text": chunk.page_content,
                    "metadata": {
                        **chunk.metadata,
                        "chunk_id_in_doc": i,
                        "start_index": chunk.metadata.get(
                            "start_index",
                            -1,
                        ),
                    },
                }

                all_chunks.append(chunk_dict)

        logging.info(
            "Total de %s chunks créés.",
            len(all_chunks),
        )

        return all_chunks

    # ========================================================
    # Génération des embeddings
    # ========================================================

    def _generate_embeddings(
        self,
        chunks: List[Dict[str, Any]],
    ) -> Optional[np.ndarray]:
        """Génère les embeddings via le SDK Mistral 1.x."""

        if not MISTRAL_API_KEY:

            logging.error(
                "Impossible de générer les embeddings : "
                "MISTRAL_API_KEY manquante."
            )

            return None

        if not chunks:

            logging.warning(
                "Aucun chunk fourni pour générer les embeddings."
            )

            return None

        if EMBEDDING_BATCH_SIZE <= 0:
            raise ValueError(
                "EMBEDDING_BATCH_SIZE doit être supérieur à zéro."
            )

        logging.info(
            "Génération des embeddings pour %s chunks "
            "(modèle : %s)...",
            len(chunks),
            EMBEDDING_MODEL,
        )

        all_embeddings = []

        total_batches = (
            len(chunks) + EMBEDDING_BATCH_SIZE - 1
        ) // EMBEDDING_BATCH_SIZE

        for i in range(
            0,
            len(chunks),
            EMBEDDING_BATCH_SIZE,
        ):

            batch_num = (
                i // EMBEDDING_BATCH_SIZE
            ) + 1

            batch_chunks = chunks[
                i:i + EMBEDDING_BATCH_SIZE
            ]

            texts_to_embed = [
                chunk["text"]
                for chunk in batch_chunks
            ]

            logging.info(
                "Traitement du lot %s/%s (%s chunks)",
                batch_num,
                total_batches,
                len(texts_to_embed),
            )

            try:

                response = self.mistral_client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    inputs=texts_to_embed,
                )

                if not response.data:
                    raise RuntimeError(
                        "L'API Mistral n'a retourné aucun embedding."
                    )

                # Garantit l'ordre des embeddings dans le lot.
                ordered_data = sorted(
                    response.data,
                    key=lambda item: item.index,
                )

                batch_embeddings = [
                    data.embedding
                    for data in ordered_data
                ]

                if len(batch_embeddings) != len(texts_to_embed):
                    raise RuntimeError(
                        "Le nombre d'embeddings retournés "
                        "ne correspond pas au nombre de chunks."
                    )

                if any(
                    embedding is None or len(embedding) == 0
                    for embedding in batch_embeddings
                ):
                    raise RuntimeError(
                        "L'API Mistral a retourné un embedding vide."
                    )

                all_embeddings.extend(
                    batch_embeddings
                )

            except Exception as e:

                logging.error(
                    "Échec de génération des embeddings "
                    "pour le lot %s/%s : %s",
                    batch_num,
                    total_batches,
                    e,
                )

                # Ne pas créer d'index avec des embeddings
                # manquants ou artificiellement remplacés.
                return None

        if len(all_embeddings) != len(chunks):

            logging.error(
                "Nombre d'embeddings incohérent : "
                "%s embeddings pour %s chunks.",
                len(all_embeddings),
                len(chunks),
            )

            return None

        try:

            embeddings_array = np.asarray(
                all_embeddings,
                dtype=np.float32,
            )

            if embeddings_array.ndim != 2:
                raise ValueError(
                    "Les embeddings doivent former "
                    "une matrice à deux dimensions."
                )

            if not np.isfinite(embeddings_array).all():
                raise ValueError(
                    "Les embeddings contiennent "
                    "des valeurs non finies."
                )

            if np.any(
                np.linalg.norm(
                    embeddings_array,
                    axis=1,
                ) == 0
            ):
                raise ValueError(
                    "Les embeddings contiennent "
                    "des vecteurs nuls."
                )

        except (ValueError, TypeError) as e:

            logging.error(
                "Embeddings invalides : %s",
                e,
            )

            return None

        logging.info(
            "Embeddings générés avec succès. Shape : %s",
            embeddings_array.shape,
        )

        return embeddings_array

    # ========================================================
    # Construction de l'index FAISS
    # ========================================================

    def build_index(
        self,
        documents: List[Dict[str, Any]],
    ):
        """Construit l'index FAISS à partir des documents."""

        if not documents:

            logging.warning(
                "Aucun document fourni pour construire l'index."
            )

            return

        # 1. Découper en chunks

        new_chunks = self._split_documents_to_chunks(
            documents
        )

        if not new_chunks:

            logging.error(
                "Le découpage n'a produit aucun chunk. "
                "Impossible de construire l'index."
            )

            return

        # 2. Générer les embeddings

        embeddings = self._generate_embeddings(
            new_chunks
        )

        if (
            embeddings is None
            or embeddings.shape[0] != len(new_chunks)
        ):

            logging.error(
                "Construction annulée : les embeddings "
                "sont absents ou incomplets."
            )

            # Préserve l'index précédemment chargé.
            return

        # 3. Normaliser les embeddings

        dimension = embeddings.shape[1]

        logging.info(
            "Création de l'index FAISS "
            "avec dimension %s...",
            dimension,
        )

        faiss.normalize_L2(
            embeddings
        )

        # 4. Créer l'index

        new_index = faiss.IndexFlatIP(
            dimension
        )

        new_index.add(
            embeddings
        )

        if new_index.ntotal != len(new_chunks):
            raise RuntimeError(
                "Le nombre de vecteurs dans l'index FAISS "
                "ne correspond pas au nombre de chunks."
            )

        # 5. Remplacer l'index en mémoire

        self.index = new_index
        self.document_chunks = new_chunks

        logging.info(
            "Index FAISS créé avec %s vecteurs.",
            self.index.ntotal,
        )

        # 6. Sauvegarder

        self._save_index_and_chunks()

    # ========================================================
    # Sauvegarde
    # ========================================================

    def _save_index_and_chunks(self):
        """Sauvegarde l'index FAISS et les chunks."""

        if self.index is None or not self.document_chunks:

            logging.warning(
                "Tentative de sauvegarde d'un index "
                "ou de chunks vides."
            )

            return

        index_directory = os.path.dirname(
            FAISS_INDEX_FILE
        )

        chunks_directory = os.path.dirname(
            DOCUMENT_CHUNKS_FILE
        )

        if index_directory:
            os.makedirs(
                index_directory,
                exist_ok=True,
            )

        if chunks_directory:
            os.makedirs(
                chunks_directory,
                exist_ok=True,
            )

        try:

            logging.info(
                "Sauvegarde de l'index FAISS dans %s...",
                FAISS_INDEX_FILE,
            )

            faiss.write_index(
                self.index,
                FAISS_INDEX_FILE,
            )

            logging.info(
                "Sauvegarde des chunks dans %s...",
                DOCUMENT_CHUNKS_FILE,
            )

            with open(
                DOCUMENT_CHUNKS_FILE,
                "wb",
            ) as f:

                pickle.dump(
                    self.document_chunks,
                    f,
                )

            logging.info(
                "Index et chunks sauvegardés avec succès."
            )

        except Exception as e:

            logging.error(
                "Erreur lors de la sauvegarde "
                "de l'index/chunks : %s",
                e,
            )

    # ========================================================
    # Recherche vectorielle
    # ========================================================

    def search(
        self,
        query_text: str,
        k: int = 5,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Recherche les k chunks les plus pertinents.

        Args:
            query_text: Texte de la requête.
            k: Nombre de résultats à retourner.
            min_score: Score minimum entre 0 et 1.

        Returns:
            Liste des chunks avec scores et métadonnées.
        """

        if self.index is None or not self.document_chunks:

            logging.warning(
                "Recherche impossible : "
                "l'index FAISS est absent ou vide."
            )

            return []

        if not MISTRAL_API_KEY:

            logging.error(
                "Recherche impossible : "
                "MISTRAL_API_KEY manquante."
            )

            return []

        if not query_text or not query_text.strip():

            logging.warning(
                "Recherche impossible : requête vide."
            )

            return []

        if k <= 0:
            raise ValueError(
                "Le paramètre k doit être supérieur à zéro."
            )

        if min_score is not None and not 0 <= min_score <= 1:
            raise ValueError(
                "min_score doit être compris entre 0 et 1."
            )

        logging.info(
            "Recherche des %s chunks les plus pertinents "
            "pour : '%s'",
            k,
            query_text,
        )

        try:

            # 1. Générer l'embedding de la question

            response = self.mistral_client.embeddings.create(
                model=EMBEDDING_MODEL,
                inputs=[query_text],
            )

            if not response.data:
                raise RuntimeError(
                    "Aucun embedding retourné pour la requête."
                )

            query_embedding = np.asarray(
                [response.data[0].embedding],
                dtype=np.float32,
            )

            if (
                query_embedding.ndim != 2
                or query_embedding.shape[1] != self.index.d
            ):
                raise ValueError(
                    "Dimension de l'embedding incompatible "
                    "avec l'index FAISS."
                )

            if not np.isfinite(query_embedding).all():
                raise ValueError(
                    "L'embedding de la requête "
                    "contient des valeurs non finies."
                )

            if np.linalg.norm(query_embedding) == 0:
                raise ValueError(
                    "L'embedding de la requête est nul."
                )

            # 2. Normaliser pour la similarité cosinus

            faiss.normalize_L2(
                query_embedding
            )

            # 3. Recherche FAISS

            search_k = (
                k * 3
                if min_score is not None
                else k
            )

            search_k = min(
                search_k,
                self.index.ntotal,
            )

            scores, indices = self.index.search(
                query_embedding,
                search_k,
            )

            # 4. Construire les résultats

            results = []

            for i, idx in enumerate(indices[0]):

                if not 0 <= idx < len(self.document_chunks):

                    logging.warning(
                        "Index FAISS %s hors limites "
                        "(taille des chunks : %s).",
                        idx,
                        len(self.document_chunks),
                    )

                    continue

                chunk = self.document_chunks[idx]

                raw_score = float(
                    scores[0][i]
                )

                similarity = raw_score * 100

                min_score_percent = (
                    min_score * 100
                    if min_score is not None
                    else 0
                )

                if (
                    min_score is not None
                    and similarity < min_score_percent
                ):
                    logging.debug(
                        "Document filtré "
                        "(score %.2f%%, minimum %.2f%%).",
                        similarity,
                        min_score_percent,
                    )

                    continue

                results.append(
                    {
                        "score": similarity,
                        "raw_score": raw_score,
                        "text": chunk["text"],
                        "metadata": chunk["metadata"],
                    }
                )

            # 5. Trier et limiter

            results.sort(
                key=lambda result: result["score"],
                reverse=True,
            )

            results = results[:k]

            if min_score is not None:

                logging.info(
                    "%s chunks pertinents trouvés "
                    "(score minimum : %.2f%%).",
                    len(results),
                    min_score * 100,
                )

            else:

                logging.info(
                    "%s chunks pertinents trouvés.",
                    len(results),
                )

            return results

        except Exception as e:

            logging.exception(
                "Erreur lors de la recherche vectorielle : %s",
                e,
            )

            return []
