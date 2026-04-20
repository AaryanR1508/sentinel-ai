import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import shutil
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parent.parent
_DATASET_PATH = _ROOT_DIR / "datasets" / "final_dataset.csv"
_VECTOR_DB_PATH = _ROOT_DIR / "vector_database"

if _VECTOR_DB_PATH.exists():
    print("🧹 Removing old database for a fresh build...")
    shutil.rmtree(_VECTOR_DB_PATH)

print(f"⏳ Loading Dataset: {_DATASET_PATH}")
csv_df = pd.read_csv(_DATASET_PATH)

if "text" in csv_df.columns:
    prompts = csv_df[csv_df['label'] == 1]['text'].dropna().tolist()
    print(f"   ✅ Found {len(prompts)} malicious prompts.")
else:
    raise ValueError("Column 'text' not found in dataset")

prompts = list(set(prompts))
print(f"📊 Total Unique Malicious Prompts to Index: {len(prompts)}")

print("⏳ Initializing Vector Database...")
client = chromadb.PersistentClient(path=str(_VECTOR_DB_PATH))

emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.create_collection(
    name="jailbreak_signatures",
    embedding_function=emb_fn,
    metadata={"hnsw:space": "cosine"}
)

print("⏳ Generating embeddings and storing... (This takes a moment)")

batch_size = 200
total_batches = (len(prompts) // batch_size) + 1

for i in range(0, len(prompts), batch_size):
    batch_texts = prompts[i : i + batch_size]
    batch_ids = [f"id_{j}" for j in range(i, i + len(batch_texts))]

    collection.add(
        documents=batch_texts,
        ids=batch_ids
    )
    print(f"   Processed batch {i // batch_size + 1}/{total_batches}")

print(f"🎉 Success! Database built at '{_VECTOR_DB_PATH}' with {collection.count()} items.")