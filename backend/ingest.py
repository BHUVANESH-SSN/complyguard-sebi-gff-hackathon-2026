import os
import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="circulars")

# Initialize SentenceTransformer
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def semantic_chunking(text: str, chunk_size: int = 3000, overlap: int = 200) -> list[str]:
    """
    A custom recursive character text splitter.
    Splits by double newline, then single newline, then space.
    """
    separators = ["\n\n", "\n", " ", ""]
    
    def split_recursively(text, sep_index=0):
        if len(text) <= chunk_size:
            return [text]
            
        separator = separators[sep_index]
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)
            
        chunks = []
        current_chunk = ""
        
        for s in splits:
            if not current_chunk:
                current_chunk = s
            elif len(current_chunk) + len(separator) + len(s) <= chunk_size:
                current_chunk += separator + s
            else:
                chunks.append(current_chunk)
                current_chunk = s
                
        if current_chunk:
            chunks.append(current_chunk)
            
        # If any chunk is STILL too large, recurse with the next separator
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > chunk_size and sep_index < len(separators) - 1:
                final_chunks.extend(split_recursively(chunk, sep_index + 1))
            else:
                final_chunks.append(chunk)
                
        return final_chunks

    # Add overlap
    base_chunks = split_recursively(text)
    overlapped_chunks = []
    for i, chunk in enumerate(base_chunks):
        if i == 0:
            overlapped_chunks.append(chunk)
        else:
            # Prepend overlap from previous chunk
            prev_chunk = base_chunks[i-1]
            overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
            overlapped_chunks.append(overlap_text + " " + chunk)
            
    return overlapped_chunks

def chunk_text(text: str) -> list[str]:
    return semantic_chunking(text)

def process_and_store_document(file_path: str, filename: str) -> list[str]:
    # 1. Extract text
    text = extract_text_from_pdf(file_path)
    
    # 2. Chunk text semantically
    chunks = chunk_text(text)
    
    # 3. Embed and store
    if not chunks:
        return []

    embeddings = embedder.encode(chunks).tolist()
    
    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    
    return chunks

def query_relevant_chunks(query: str, n_results: int = 3) -> list:
    query_embedding = embedder.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    if results['documents'] and len(results['documents']) > 0:
        return results['documents'][0]
    return []
