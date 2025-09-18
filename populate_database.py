import os
import re
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

# ==============================================================================
# 1. SETUP & INITIALIZATION
# ==============================================================================

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Check if the credentials are set
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key must be set in the .env file.")

# Initialize the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize the Sentence Transformer model for creating embeddings
# 'all-MiniLM-L6-v2' is a great general-purpose model that creates 384-dimensional vectors.
MODEL_NAME = 'all-MiniLM-L6-v2'
print("Loading sentence-transformer model...")
model = SentenceTransformer(MODEL_NAME)
print("Model loaded successfully.")


# ==============================================================================
# 2. DATA LOADING & PREPARATION FUNCTIONS
# ==============================================================================

def load_documents_from_folder(folder_path: str) -> List[Dict[str, Any]]:
    """
    Loads all .txt files from a specified folder into a list of documents.
    """
    documents = []
    print(f"Loading documents from '{folder_path}'...")
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Each document is a dictionary with its content and metadata
                doc = {
                    "content": content,
                    "metadata": {
                        "source": filename
                    }
                }
                documents.append(doc)
    print(f"Found and loaded {len(documents)} documents.")
    return documents

def chunk_document(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Splits a document's content into smaller chunks based on paragraphs.
    This is crucial for effective semantic search.
    """
    # Splitting by double newline characters, which usually separate paragraphs.
    content_chunks = re.split(r'\n\s*\n', document["content"])
    
    chunked_documents = []
    for chunk in content_chunks:
        stripped_chunk = chunk.strip()
        if stripped_chunk:  # Only add non-empty chunks
            chunked_documents.append({
                "content": stripped_chunk,
                "metadata": document["metadata"]
            })
    return chunked_documents


# ==============================================================================
# 3. MAIN EXECUTION LOGIC
# ==============================================================================

def main():
    """
    The main function to run the entire pipeline:
    Load -> Chunk -> Embed -> Upload
    """
    # Define the folder where your health data is stored
    data_folder = 'health_data'
    
    # --- Step 1: Load the documents ---
    documents = load_documents_from_folder(data_folder)
    
    # --- Step 2: Chunk the documents into smaller pieces ---
    all_chunks = []
    print("Chunking documents...")
    for doc in documents:
        all_chunks.extend(chunk_document(doc))
    print(f"Total chunks created: {len(all_chunks)}")

    # --- Step 3: Generate embeddings and prepare for upload ---
    print("Generating embeddings for all chunks...")
    
    # Extract just the content for efficient batch embedding
    contents_to_embed = [chunk["content"] for chunk in all_chunks]
    
    # Generate embeddings in a single batch (highly efficient)
    embeddings = model.encode(contents_to_embed, show_progress_bar=True)
    
    # Prepare the final data payload for Supabase
    data_to_insert = []
    for i, chunk in enumerate(all_chunks):
        data_to_insert.append({
            'content': chunk['content'],
            'metadata': chunk['metadata'],
            'embedding': embeddings[i].tolist() # Convert numpy array to list for Supabase
        })
        
    print(f"Embeddings generated. Preparing to upload {len(data_to_insert)} records.")
    
    # --- Step 4: Insert the data into Supabase in batches ---
    batch_size = 100 # Upload in batches of 100 to avoid timeouts
    for i in range(0, len(data_to_insert), batch_size):
        batch = data_to_insert[i:i + batch_size]
        print(f"Uploading batch {i // batch_size + 1}...")
        try:
            response = supabase.table('health_knowledge_base').insert(batch).execute()
        except Exception as e:
            print(f"Error inserting batch {i // batch_size + 1}: {e}")
            # You might want to add error handling or retries here
    
    print("\n========================================================")
    print("      Data population complete! Your AI is ready.     ")
    print("========================================================")


# Run the main function when the script is executed
if __name__ == "__main__":
    main()