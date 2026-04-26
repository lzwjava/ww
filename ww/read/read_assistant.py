import argparse
import json
import os
from pathlib import Path

INDEX_DIR = Path.home() / ".ww" / "read_index"
CHUNKS_FILE = INDEX_DIR / "chunks.json"
INDEX_FILE = INDEX_DIR / "index.faiss"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
CHUNK_WORDS = 400
CHUNK_OVERLAP = 80


def _chunk_text(text, size=CHUNK_WORDS, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + size]))
        i += size - overlap
    return chunks


def _load_docs(directory):
    docs = []
    for ext in ("**/*.md", "**/*.txt", "**/*.rst"):
        for path in Path(directory).glob(ext):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                docs.append((str(path), text))
            except Exception:
                pass
    return docs


def _embed(texts, model):
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=True)


def _index(directory):
    import faiss  # type: ignore[import-untyped]
    from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

    print(f"Loading documents from {directory} ...")
    docs = _load_docs(directory)
    if not docs:
        print("No .md/.txt/.rst files found.")
        return

    print(f"Found {len(docs)} files. Chunking ...")
    chunks = []
    for source, text in docs:
        for chunk in _chunk_text(text):
            if chunk.strip():
                chunks.append({"text": chunk, "source": source})

    print(f"{len(chunks)} chunks. Embedding with {EMBEDDING_MODEL} ...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    vectors = _embed([c["text"] for c in chunks], model).astype("float32")

    faiss_index = faiss.IndexFlatIP(vectors.shape[1])
    faiss_index.add(vectors)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(faiss_index, str(INDEX_FILE))
    CHUNKS_FILE.write_text(json.dumps(chunks, ensure_ascii=False))
    print(f"Done. {len(chunks)} chunks saved to {INDEX_DIR}")


def _query(question, top_k=5):
    import faiss  # type: ignore[import-untyped]
    from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

    if not INDEX_FILE.exists():
        print("No index found. Run first:  ww read index <directory>")
        return

    chunks = json.loads(CHUNKS_FILE.read_text())
    faiss_index = faiss.read_index(str(INDEX_FILE))

    model = SentenceTransformer(EMBEDDING_MODEL)
    q_vec = model.encode([question], normalize_embeddings=True).astype("float32")
    _, indices = faiss_index.search(q_vec, top_k)

    context = "\n\n---\n\n".join(
        f"[{chunks[i]['source']}]\n{chunks[i]['text']}" for i in indices[0] if i >= 0
    )

    prompt = (
        "You are a helpful reading assistant. Answer the question using only the "
        "context below. Be concise.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\nAnswer:"
    )

    from ww.llm.openrouter_client import call_openrouter_api

    model_name = os.getenv("MODEL", "google/gemini-flash-1.5")
    print(call_openrouter_api(prompt, model=model_name))


def main():
    parser = argparse.ArgumentParser(description="AI reading assistant (RAG + BGE)")
    sub = parser.add_subparsers(dest="cmd")

    idx = sub.add_parser("index", help="Index documents in a directory")
    idx.add_argument("directory", help="Path to documents folder")

    qry = sub.add_parser("query", help="Ask a question over indexed documents")
    qry.add_argument("question", nargs="+", help="Question text")
    qry.add_argument(
        "--top-k", type=int, default=5, help="Chunks to retrieve (default 5)"
    )

    args = parser.parse_args()

    if args.cmd == "index":
        _index(args.directory)
    elif args.cmd == "query":
        _query(" ".join(args.question), top_k=args.top_k)
    else:
        parser.print_help()
