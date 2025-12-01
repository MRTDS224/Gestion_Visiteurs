from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text
)
from models.user import Base
       
class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_path = Column(Text, nullable=False)
    phone_number = Column(String, nullable=False)
    place_of_birth = Column(String, nullable=False)
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
            "phone_number": self.phone_number,
            "place_of_birth": self.place_of_birth,
            "motif": self.motif,
            "date": self.date,
            "arrival_time": self.arrival_time,
            "exit_time": self.exit_time,
            "observation": self.observation
        }
        
    def set_exit_time(self, time):
        self.exit_time = time

    def set_observation(self, observation):
        self.observation = observation