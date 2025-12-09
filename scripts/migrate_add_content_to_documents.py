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
                conn.execute(text("ALTER TABLE documents ADD COLUMN content TEXT;"))
                conn.commit()
                print("Column added successfully.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
