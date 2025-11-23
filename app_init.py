import os
import subprocess
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def init_database():
    """Vérifie que PostgreSQL est accessible et crée les tables si nécessaire."""
    db_url = os.getenv("GESTION_DB_URL")
    
    if not db_url:
        raise SystemExit("GESTION_DB_URL non défini dans .env")
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Connexion à PostgreSQL réussie!")
        
    except Exception as e:
        print(f"❌ Erreur de connexion PostgreSQL: {e}")
        print("Tentative de création de la base de données...")
        
        # Exécuter le script SQL
        try:
            sql_script = os.path.join(os.path.dirname(__file__), "init_db.sql")
            subprocess.run(
                ["psql", "-U", "postgres", "-f", sql_script],
                env={**os.environ, "PGPASSWORD": os.getenv("POSTGRES_PASSWORD", "PostgreSQL_Secure_Pass_2024")},
                check=True
            )
            print("✅ Tables créées avec succès!")
        except Exception as e:
            print(f"❌ Erreur création tables: {e}")
            raise

if __name__ == "__main__":
    init_database()