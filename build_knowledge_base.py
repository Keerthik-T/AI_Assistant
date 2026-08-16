import os

import chromadb


def build_knowledge_base():
    print("Initializing FurinaOS Knowledge Base Builder...")

    # 1. Connect to our persistent ChromaDB
    memory_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_db")
    try:
        chroma_client = chromadb.PersistentClient(path=memory_dir)
        collection = chroma_client.get_or_create_collection(
            name="furina_long_term_memory"
        )
    except Exception as e:
        print(f"Failed to connect to ChromaDB: {e}")
        return

    # 2. Check the knowledge directory
    kb_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")
    if not os.path.exists(kb_dir):
        os.makedirs(kb_dir)
        print(
            f"Created '{kb_dir}' directory. Please drop your .txt or .md notes here and run this script again!"
        )
        return

    files_processed = 0
    docs = []
    ids = []

    # 3. Read and vectorize all files
    for filename in os.listdir(kb_dir):
        if filename.endswith(".txt") or filename.endswith(".md"):
            filepath = os.path.join(kb_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # We split into rough chunks if it's too large, but for simplicity, we insert by file or paragraph
                chunks = [
                    chunk.strip()
                    for chunk in content.split("\n\n")
                    if len(chunk.strip()) > 50
                ]

                for idx, chunk in enumerate(chunks):
                    doc_id = f"{filename}_chunk_{idx}"
                    docs.append(f"[KNOWLEDGE BASE - {filename}]: {chunk}")
                    ids.append(doc_id)

                files_processed += 1
                print(f"Processed {filename} ({len(chunks)} knowledge chunks).")
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    # 4. Insert into database
    if docs:
        try:
            # Overwrite if exists
            collection.upsert(documents=docs, ids=ids)
            print(
                f"Successfully vectorized {files_processed} files into Furina's brain!"
            )
        except Exception as e:
            print(f"Error vectorizing to ChromaDB: {e}")
    else:
        print("No valid content found in the knowledge directory to vectorize.")


if __name__ == "__main__":
    build_knowledge_base()
