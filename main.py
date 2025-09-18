import os
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI
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

# Load the sentence-transformer model
# This is done once when the API starts up, so it's ready for all requests.
print("Loading sentence-transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully.")

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

    # --- Step 1: Generate an embedding for the user's query ---
    # The .tolist() is important to convert the numpy array into a regular list for the API call
    query_embedding = model.encode(query).tolist()

    # --- Step 2: Call the Supabase database function ---
    # We are calling the 'match_health_documents' function we created in the Supabase SQL Editor.
    response = supabase.rpc('match_health_documents', {
        'query_embedding': query_embedding,
        'match_threshold': 0.70,  # Adjust this for more/less strict matching
        'match_count': 3          # Get the top 3 most relevant chunks
    }).execute()

    # --- Step 3: Process the results and create the context ---
    context = ""
    sources = []
    
    if response.data:
        # Combine the content of the matched documents into a single string
        context = "\n\n---\n\n".join([item['content'] for item in response.data])
        
        # Collect the unique sources from the metadata
        sources = list(set([item['metadata']['source'] for item in response.data]))

    return {"context": context, "sources": sources}


# Optional: Add a root endpoint for a simple health check
@app.get("/")
def read_root():
    return {"status": "API is running."}