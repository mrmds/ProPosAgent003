"""Utility functions for text processing and Supabase operations."""

import os
import json
from typing import List, Dict, Any, Optional
import asyncio

from supabase import create_client, Client

# Function to get Supabase client
def get_supabase_client() -> Client:
    """Get a Supabase client using environment variables.
    
    Returns:
        A Supabase Client
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    
    return create_client(supabase_url, supabase_key)


async def add_documents_to_supabase(
    client: Client,
    table_name: str,
    documents: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    batch_size: int = 100,
) -> List[Dict[str, Any]]:
    """Add documents to a Supabase table in batches.
    
    Args:
        client: Supabase client
        table_name: Name of the table
        documents: List of document texts
        metadatas: Optional list of metadata dictionaries for each document
        batch_size: Size of batches for adding documents
        
    Returns:
        List of insertion results
    """
    # Create default metadata if none provided
    if metadatas is None:
        metadatas = [{}] * len(documents)
    
    # Initialize results
    results = []
    
    # Process documents in batches
    for i in range(0, len(documents), batch_size):
        batch_documents = documents[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        
        # Prepare data for insertion
        data = []
        for j, (doc, meta) in enumerate(zip(batch_documents, batch_metadatas)):
            # Convert metadata to JSON string if needed
            meta_json = json.dumps(meta) if isinstance(meta, dict) else meta
            
            data.append({
                "content": doc,
                "metadata": meta_json,
                "embedding": None  # Will be filled by Supabase Edge Function or trigger
            })
        
        # Insert the batch
        response = client.table(table_name).insert(data).execute()
        results.extend(response.data)
    
    return results


async def query_supabase_collection(
    client: Client,
    table_name: str,
    query_text: str,
    n_results: int = 5,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Query a Supabase table for similar documents using vector similarity.
    
    Args:
        client: Supabase client
        table_name: Name of the table
        query_text: Text to search for
        n_results: Number of results to return
        filters: Optional filters to apply to the query
        
    Returns:
        Query results containing documents, metadatas, and similarity scores
    """
    # Generate embedding for query_text via Ollama or similar
    # This is a placeholder; in a real implementation, you'd generate an embedding
    
    # Build RPC call to Supabase function that performs vector search
    # This is a simplified example; actual implementation would depend on your Supabase setup
    response = client.rpc(
        'search_documents',
        {
            'query_text': query_text,
            'match_count': n_results,
            'table_name': table_name,
            'filters': json.dumps(filters) if filters else '{}'
        }
    ).execute()
    
    if response.error:
        raise Exception(f"Error querying Supabase: {response.error.message}")
    
    # Process results into a format similar to ChromaDB for compatibility
    results = {
        "documents": [[item['content'] for item in response.data]],
        "metadatas": [[json.loads(item['metadata']) for item in response.data]],
        "distances": [[1 - item['similarity'] for item in response.data]],
        "ids": [[str(item['id']) for item in response.data]]
    }
    
    return results


def format_results_as_context(query_results: Dict[str, Any]) -> str:
    """Format query results as a context string for the agent.
    
    Args:
        query_results: Results from a Supabase query
        
    Returns:
        Formatted context string
    """
    context = "CONTEXT INFORMATION:\n\n"
    
    for i, (doc, metadata, distance) in enumerate(zip(
        query_results["documents"][0],
        query_results["metadatas"][0],
        query_results["distances"][0]
    )):
        # Add document information
        context += f"Document {i+1} (Relevance: {1 - distance:.2f}):\n"
        
        # Add metadata if available
        if metadata:
            for key, value in metadata.items():
                context += f"{key}: {value}\n"
        
        # Add document content
        context += f"Content: {doc}\n\n"
    
    return context
