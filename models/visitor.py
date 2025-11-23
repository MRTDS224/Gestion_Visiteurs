from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text
)
from sqlalchemy.orm import declarative_base
from models.user import Base


class VisitorModel(Base):
    __tablename__ = "visiteurs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_path = Column(Text, nullable=False)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    place_of_birth = Column(String, nullable=False)
    id_type = Column(String, nullable=False)
    id_number = Column(String, nullable=False)
    motif = Column(String, nullable=False)
    date = Column(String, nullable=False, default=datetime.now().date().isoformat())
    arrival_time = Column(String, nullable=False, default=datetime.now().strftime("%H:%M"))
    exit_time = Column(String, nullable=True)
    observation = Column(Text, nullable=True)

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