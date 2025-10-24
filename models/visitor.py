import sqlite3
from datetime import datetime
import os
from sqlalchemy import (
    create_engine, Column, Integer, String, LargeBinary,
    ForeignKey, DateTime, func, Text
)
from sqlalchemy.orm import relationship
from models.user import Base
from helpers import resource_path

def get_user_db_path():
    # Windows : APPDATA ou fallback sur user home
    base = os.getenv('APPDATA') or os.path.expanduser("~")
    appdir = os.path.join(base, "GestionVisiteurs")
    os.makedirs(appdir, exist_ok=True)
    return os.path.join(appdir, "gestion_visiteurs.db")

DB_PATH = resource_path(os.path.join("database", "visiteurs.db"))
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
# --- IMPORTANT : s'assurer que les tables SQLAlchemy existent dans la DB ---
Base.metadata.create_all(ENGINE)


class VisitorModel:
    def __init__(
        self, id, image_path, nom, prenom, phone_number, date_of_birth, place_of_birth, id_type, id_number, motif,
        date=None, arrival_time=None, exit_time="", observation=""
    ):
        self.id = id
        self.image_path = image_path
        self.nom = nom
        self.prenom = prenom
        self.phone_number = phone_number
        self.date_of_birth = date_of_birth
        self.place_of_birth = place_of_birth
        self.id_type = id_type
        self.id_number = id_number
        self.motif = motif
        self.date = date if date else datetime.now().date().isoformat()
        self.arrival_time = arrival_time if arrival_time else datetime.now().strftime("%H:%M")
        self.exit_time = exit_time
        self.observation = observation

    def to_dict(self):
        """Convertit un visiteur en dictionnaire pour stockage JSON"""
        return {
            "id": self.id,
            "image_path": self.image_path,
            "nom": self.nom,
            "prenom": self.prenom,
            "phone_number": self.phone_number,
            "date_of_birth": self.date_of_birth,
            "place_of_birth": self.place_of_birth,
            "id_type": self.id_type,
            "id_number": self.id_number,
            "motif": self.motif,
            "observation": self.observation,
            "date": self.date,
            "arrival_time": self.arrival_time,
            "exit_time": self.exit_time
        }
        
    def set_exit_time(self, time):
        self.exit_time = time

    def set_observation(self, observation):
        self.observation = observation

class VisitorDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_table()

    def create_table(self):
        """Crée la table visiteurs si elle n'existe pas."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visiteurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                place_of_birth TEXT NOT NULL,
                id_type TEXT NOT NULL,
                id_number TEXT NOT NULL,
                motif TEXT NOT NULL,
                date TEXT NOT NULL,
                arrival_time TEXT NOT NULL,
                exit_time TEXT, 
                observation TEXT 
            )
        ''')
        self.conn.commit()

    def add_visitor(self, image_path, nom, prenom, phone_number, date_of_birth, place_of_birth, id_type, id_number, motif, date=None, arrival_time=None):
        """Ajoute un visiteur avec date et heure d'arrivée automatiques si non fournis."""
        if date is None:
            date = datetime.now().date().isoformat()
        if arrival_time is None:
            arrival_time = datetime.now().strftime("%H:%M")
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO visiteurs (image_path, nom, prenom, phone_number, date_of_birth, place_of_birth, id_type, id_number, motif, date, arrival_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (image_path, nom, prenom, phone_number, date_of_birth, place_of_birth, id_type, id_number, motif, date, arrival_time)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def update_visitor(self, visitor_id, **kwargs):
        updates = []
        params = []
        for key, value in kwargs.items():
            updates.append(f"{key} = ?")
            params.append(value)
        if not updates:
            return False
        params.append(visitor_id)
        query = f"UPDATE visiteurs SET {', '.join(updates)} WHERE id = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close(self):
        self.conn.close()
    
    def delete_visitor(self, visitor_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM visiteurs WHERE id = ?', (visitor_id,))
        self.conn.commit()
        return cursor.rowcount > 0
            
    def get_visitor_by_id(self, id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM visiteurs WHERE id = ?', (id,))
        
        row = cursor.fetchone()
        if row:
            return VisitorModel(*row)
        
        return None
    
    def get_all_visitors(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM visiteurs')
        rows = cursor.fetchall()
        return [VisitorModel(*row) for row in rows]

db = VisitorDatabase()

class VisitorShare(Base):
    __tablename__ = "visitor_shares"
    id                   = Column(Integer, primary_key=True)
    visitor_id           = Column(Integer, nullable=False, index=True)
    shared_by_user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_user_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    nom                  = Column(String, nullable=False)
    prenom               = Column(String, nullable=False)
    date_of_birth        = Column(String, nullable=False)
    place_of_birth       = Column(String, nullable=False)
    id_type              = Column(String, nullable=False)
    id_number            = Column(String, nullable=False)
    phone_number         = Column(String, nullable=False)
    motif                = Column(Text)
    image_data           = Column(LargeBinary, nullable=False)
    shared_at            = Column(DateTime(timezone=True), server_default=func.now())
    status               = Column(String, default="active", nullable=False)

    shared_by  = relationship("User", back_populates="shares_sent",
                              foreign_keys=[shared_by_user_id])
    shared_with = relationship("User", back_populates="shares_received",
                               foreign_keys=[shared_with_user_id])
