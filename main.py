import os
import requests
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# ==============================================================================
# 1. SETUP & INITIALIZATION
# ==============================================================================

# Load environment variables from the .env file
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key must be set in the .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO)

# Configure Hugging Face Inference API for embeddings (free-tier friendly)
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

if not HF_API_TOKEN:
    logging.warning("HF_API_TOKEN not set. Set it to use Hugging Face Inference API for embeddings.")

def generate_text_embedding(text: str) -> List[float]:
    """Generate an embedding using Hugging Face Inference API to avoid heavy local models."""
    if not HF_API_TOKEN:
        raise ValueError("HF_API_TOKEN must be set to generate embeddings via Hugging Face Inference API.")

    # Use the models endpoint (recommended)
    api_url = f"https://api-inference.huggingface.co/models/{HF_EMBEDDING_MODEL}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}", "Accept": "application/json"}
    try:
        response = requests.post(api_url, json={"inputs": text, "truncate": True}, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.HTTPError as http_err:
        status = getattr(http_err.response, "status_code", None)
        if status == 401:
            logging.error("HF Inference API unauthorized. Check HF_API_TOKEN permissions.")
        elif status == 404:
            logging.error("HF model not found at Inference API. Verify HF_EMBEDDING_MODEL: %s", HF_EMBEDDING_MODEL)
        else:
            logging.exception("HF Inference API HTTP error")
        raise
    except Exception as exc:
        logging.exception("Embedding API request failed")
        raise

    # The API returns nested lists: [token_embeddings] or [sentence_embedding]
    # For sentence-transformers models with pooling, it returns a single vector.
    # If it's token-level, average pool across tokens.
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
        # If first element is itself a list of floats, assume sentence vector
        if all(isinstance(x, (int, float)) for x in data[0]):
            # Heuristic: if shape is [dim] return as-is; if [tokens][dim], average
            if all(isinstance(x, (int, float)) for x in data):
                return [float(x) for x in data]
            # Average across tokens
            token_vectors = data
            dim = len(token_vectors[0])
            sums = [0.0] * dim
            for vec in token_vectors:
                for i, val in enumerate(vec):
                    sums[i] += float(val)
            return [s / max(1, len(token_vectors)) for s in sums]

    # If response format unexpected, raise
    raise RuntimeError("Unexpected embedding format from Hugging Face Inference API")

# Initialize the FastAPI app
app = FastAPI(
    title="SIH Health Chatbot API",
    description="An API to find relevant health information from a vector database.",
    version="1.0.0"
)


# ==============================================================================
# 2. Pydantic Models (for Request and Response Data Validation)
# ==============================================================================

# This defines the structure of the JSON we expect in the POST request body
class SearchQuery(BaseModel):
    query: str

# This defines the structure of the JSON response we will send back
class SearchResponse(BaseModel):
    context: str
    sources: List[str]


# ==============================================================================
# 3. API ENDPOINT DEFINITION
# ==============================================================================

@app.post("/search", response_model=SearchResponse)
async def search_knowledge_base(search_query: SearchQuery):
    """
    Receives a user's query, generates an embedding, and searches the Supabase
    vector database for the most relevant content chunks.
    """
    query = search_query.query

    # --- Step 1: Generate an embedding for the user's query (via HF Inference API) ---
    try:
        query_embedding = generate_text_embedding(query)
    except ValueError as ve:
        # Likely missing HF_API_TOKEN
        raise HTTPException(status_code=503, detail=f"Embedding unavailable: {str(ve)}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to generate embedding from provider")

    # --- Step 2: Call the Supabase database function ---
    # We are calling the 'match_health_documents' function we created in the Supabase SQL Editor.
    try:
        response = supabase.rpc('match_health_documents', {
            'query_embedding': query_embedding,
            'match_threshold': 0.70,
            'match_count': 3
        }).execute()
    except Exception as exc:
        logging.exception("Supabase RPC call failed")
        raise HTTPException(status_code=502, detail="Vector search failed")

    # --- Step 3: Process the results and create the context ---
    context = ""
    sources = []
    
    if getattr(response, 'data', None):
        # Combine the content of the matched documents into a single string
        context = "\n\n---\n\n".join([item['content'] for item in response.data])
        
        # Collect the unique sources from the metadata
        sources = list(set([item['metadata']['source'] for item in response.data]))
    else:
        logging.info("No matches returned from Supabase for query")

    return {"context": context, "sources": sources}


# Optional: Add a root endpoint for a simple health check
@app.get("/")
def read_root():
    return {"status": "API is running."}