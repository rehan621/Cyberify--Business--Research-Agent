import os
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from docx import Document as DocxDocument
from dotenv import load_dotenv

load_dotenv()

# ── ChromaDB Client ───────────────────────────────────────────────────────────
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH,
    settings=Settings(anonymized_telemetry=False)
)

embeddings = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-3-small"
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)


# ── Document Reading ──────────────────────────────────────────────────────────

def read_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"[PDF Error] {e}")
        return ""


def read_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        doc = DocxDocument(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        print(f"[DOCX Error] {e}")
        return ""


def read_txt(file_path: str) -> str:
    """Read content from a TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[TXT Error] {e}")
        return ""


def extract_text(file_path: str, file_type: str) -> str:
    """Extract text based on the specified file type."""
    ft = file_type.lower()
    if ft == "pdf":
        return read_pdf(file_path)
    elif ft in ("docx", "doc"):
        return read_docx(file_path)
    elif ft == "txt":
        return read_txt(file_path)
    return ""


# ── ChromaDB Operations ───────────────────────────────────────────────────────

def get_or_create_collection(user_id: int):
    """Get or create a dedicated ChromaDB collection for a user."""
    collection_name = f"user_{user_id}_docs"
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


def add_document_to_chroma(
    user_id: int,
    doc_id: int,
    file_path: str,
    file_type: str,
    filename: str,
) -> str:
    """Add a document to ChromaDB after text extraction and chunking."""
    # Extract text
    text = extract_text(file_path, file_type)
    if not text.strip():
        raise ValueError("No text found in the document.")

    # Generate chunks
    chunks = text_splitter.split_text(text)
    print(f"[RAG] {filename} — {len(chunks)} chunks")

    # Generate embeddings
    chunk_embeddings = embeddings.embed_documents(chunks)

    # Store in ChromaDB
    collection = get_or_create_collection(user_id)
    chroma_doc_id = f"doc_{doc_id}"

    collection.add(
        ids=[f"{chroma_doc_id}_chunk_{i}" for i in range(len(chunks))],
        embeddings=chunk_embeddings,
        documents=chunks,
        metadatas=[{
            "doc_id":   doc_id,
            "filename": filename,
            "chunk":    i,
        } for i in range(len(chunks))],
    )

    return chroma_doc_id


def search_documents(user_id: int, query: str, top_k: int = 5) -> list[dict]:
    """Search and retrieve relevant document chunks matching the query."""
    try:
        collection = get_or_create_collection(user_id)

        # Return empty list if collection is empty
        if collection.count() == 0:
            return []

        query_embedding = embeddings.embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for i, doc in enumerate(results["documents"][0]):
            output.append({
                "content":  doc,
                "filename": results["metadatas"][0][i].get("filename", ""),
                "score":    1 - results["distances"][0][i],  # similarity score
            })

        return output

    except Exception as e:
        print(f"[RAG Search Error] {e}")
        return []


def delete_document_from_chroma(user_id: int, doc_id: int):
    """Delete all associated chunks of a document from ChromaDB."""
    try:
        collection = get_or_create_collection(user_id)
        # Delete all chunks related to the doc_id
        results = collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            collection.delete(ids=results["ids"])
            print(f"[RAG] Deleted {len(results['ids'])} chunks for doc_{doc_id}")
    except Exception as e:
        print(f"[RAG Delete Error] {e}")