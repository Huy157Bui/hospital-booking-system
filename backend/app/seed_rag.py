import os
import json
import logging
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN_WARNING"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

for logger_name in [
    "httpx", "urllib3", "chromadb", "sentence_transformers",
    "transformers", "huggingface_hub", "huggingface_hub.utils._http"
]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

import chromadb
from chromadb.utils import embedding_functions

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = BASE_DIR / "dataset" / "bachmai" / "processed" / "bachmai_rag_chunks.json"
CHROMA_DB_DIR = BASE_DIR / "database" / "chroma_db"
COLLECTION_NAME = "bachmai_knowledge"

def seed_rag_vector_db():
    print("\n" + "="*55)
    logger.info("KHOI TAO NAP DU LIEU VECTOR DB (CHROMADB)")
    print("="*55)

    if not DATASET_PATH.exists():
        logger.error(f"Loi: Khong tim thay file du lieu tai: {DATASET_PATH}")
        return

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        rag_chunks = json.load(f)

    logger.info(f"Da tai {len(rag_chunks)} RAG chunks tu file JSON.")

    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    local_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=local_ef,
        metadata={"hnsw:space": "cosine"}
    )

    documents, metadatas, ids = [], [], []
    for idx, item in enumerate(rag_chunks):
        content = item.get("text_payload", "")
        chunk_id = str(item.get("chunk_id") or f"rag_chunk_{idx + 1}")
        raw_metadata = item.get("metadata", {})

        clean_metadata = {}
        if isinstance(raw_metadata, dict):
            for k, v in raw_metadata.items():
                if isinstance(v, (dict, list)):
                    clean_metadata[k] = json.dumps(v, ensure_ascii=False)
                elif v is not None:
                    clean_metadata[k] = v

        if content and content.strip():
            documents.append(content)
            ids.append(chunk_id)
            metadatas.append(clean_metadata)

    total_items = len(ids)
    logger.info(f"Dang tao Vector Embedding cho {total_items} chunks...")

    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)

    print("="*55)
    logger.info(f"THANH CONG: Da luu tron ven {collection.count()}/{total_items} chunks vao ChromaDB.")
    print("="*55 + "\n")

if __name__ == "__main__":
    seed_rag_vector_db()