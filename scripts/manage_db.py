# scripts/manage_db.py

import sys
import argparse
from pathlib import Path
import chromadb

sys.path.append(str(Path(__file__).resolve().parent.parent))

from factcheck.utils.database import DatabaseProvider, get_vector_collection
from factcheck.utils.config_loader import config


def reset_screening_knowledge():
    print("Action: RESET 'screening_knowledge' collection")
    try:
        client = DatabaseProvider.get_chroma_client()
        collection_name = config.get('vectordb.screening_collection_name', 'screening_knowledge')

        try:
            print(f"   -> Deleting collection '{collection_name}'...")
            client.delete_collection(name=collection_name)
            print("   -> Deleted.")
        except ValueError:
            print("   -> Collection did not exist.")
        
        print(f"   -> Re-creating collection '{collection_name}'...")
        from chromadb.utils import embedding_functions
        emb_model = config.get('vectordb.embedding_model', 'intfloat/e5-base-v2')
        
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=emb_model
        )
        get_vector_collection(
            collection_name=collection_name,
            embedding_function=sentence_transformer_ef
        )
        
        print("   -> Created successfully.")
        print("\n=== RESET COMPLETE ===")
        
    except Exception as e:
        print(f"Error: An error occurred during reset: {e}")


def list_collections():
    print("Action: LIST Collections")
    try:
        client = DatabaseProvider.get_chroma_client()
        collections = client.list_collections()
        
        if not collections:
            print("   -> No collections found.")
            return
            
        print(f"   -> Found {len(collections)} collections:")
        for collection in collections:
            collection_instance = client.get_collection(collection.name)
            print(f"      - {collection.name} (Count: {collection_instance.count()})")
            
    except Exception as e:
        print(f"Error: An error occurred during listing: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FailSafe DB Management Tool")
    parser.add_argument('action', choices=['reset', 'list'], help="Action: 'reset' (screening_knowledge) or 'list' (all)")
    args = parser.parse_args()

    if args.action == 'reset':
        reset_screening_knowledge()
    elif args.action == 'list':
        list_collections()