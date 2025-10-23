# script/manage_db.py
import chromadb
import argparse


def reset_screening_knowledge(db_path="./chroma_db"):
    """Deletes and recreates the screening_knowledge collection."""
    try:
        print(f"Connecting to ChromaDB at '{db_path}'...")
        client = chromadb.PersistentClient(path=db_path)

        try:
            print("Attempting to delete 'screening_knowledge' collection...")
            client.delete_collection(name="screening_knowledge")
            print("-> Collection 'screening_knowledge' deleted successfully.")
        except ValueError:
            print("-> Collection 'screening_knowledge' does not exist, skipping deletion.")
        
        # (Tùy chọn) Tạo lại collection ngay lập tức
        # Điều này đảm bảo ứng dụng sẽ không bị lỗi khi khởi động nếu collection chưa có
        print("Creating 'screening_knowledge' collection...")
        from chromadb.utils import embedding_functions
        # Cần đảm bảo bạn có sentence-transformers đã cài đặt
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name='intfloat/e5-base-v2'
        )
        client.create_collection(
            name="screening_knowledge",
            embedding_function=sentence_transformer_ef
        )
        print("-> Collection 'screening_knowledge' created successfully.")
        print("\nReset complete!")
    except chromadb.errors.ChromaError as e:
        print(f"\nA ChromaDB error occurred: {e}")
    except ImportError as e:
        print(f"\nMissing dependency: {e}")
    except (OSError, IOError) as e:
        print(f"\nAn OS / IO error occurred: {e}")
    except RuntimeError as e:
        print(f"\nA runtime error occurred: {e}")


def list_collections(db_path="./chroma_db"):
    """Lists all collections in the database."""
    try:
        print(f"Connecting to ChromaDB at '{db_path}'...")
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        if not collections:
            print("No collections found.")
            return
            
        print("Available collections:")
        for collection in collections:
            print(f"- {collection.name} (Count: {collection.count()})")
    
    except (chromadb.errors.ChromaError, IOError) as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChromaDB Management Tool for FailSafe")
    parser.add_argument('action', choices=['reset', 'list'], help="Action to perform: 'reset' or 'list'.")
    args = parser.parse_args()

    if args.action == 'reset':
        reset_screening_knowledge()
    elif args.action == 'list':
        list_collections()