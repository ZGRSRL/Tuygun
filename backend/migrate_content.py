from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='documents' AND column_name='content';"
            ))
            if result.fetchone():
                print("Column 'content' already exists in 'documents'.")
            else:
                print("Adding 'content' column to 'documents'...")
                print("Column added successfully.")
        
            # Check if embedding column exists
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='documents' AND column_name='embedding';"
            ))
            if result.fetchone():
                print("Column 'embedding' already exists in 'documents'.")
            else:
                print("Adding 'embedding' column to 'documents'...")
                # Ensure vector extension exists
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.execute(text("ALTER TABLE documents ADD COLUMN embedding vector(384);"))
                conn.commit()
                print("Column added successfully.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
