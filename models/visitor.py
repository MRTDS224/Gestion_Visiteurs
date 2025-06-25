import json
from datetime import datetime, date, timezone, timedelta

class VisitorModel:
    def __init__(self, image, nom, prenom, phone_number, id_type, id_number, motif):
        self.image_path = image
        self.nom = nom
        self.prenom = prenom
        self.phone_number = phone_number
        self.id_type = id_type
        self.id_number = id_number
        self.motif = motif
        self.date = str(date.today())
        self.arrival_time = str(datetime.now().time().strftime("%H:%M"))
        self.observation = "None"
        self.exit_time = self.arrival_time

    def to_dict(self):
        """Convertit un visiteur en dictionnaire pour stockage JSON"""
        return {
            "image": self.image_path,
            "nom": self.nom,
            "prenom": self.prenom,
            "phone_number": self.phone_number,
            "id_type": self.id_type,
            "id_number": self.id_number,
            "motif": self.motif,
            "observation": self.observation,
            "date": self.date,
            "arrival_time": self.arrival_time,
            "exit_time": self.exit_time
        }

    def set_exit_time(self, time=None):
        self.exit_time = time if time else datetime.datetime.now().time().strftime("%H:%M")
    
    def set_observation(self, observation):
        self.observation = observation
    
    @staticmethod
    def save_to_file(visitor):
        """Sauvegarde un visiteur dans un fichier JSON"""
        with open("database/visiteurs.json", "r") as file:
            visitors = json.load(file)
        visitors.append(visitor.to_dict())
        with open("database/visiteurs.json", "w") as file:
            json.dump(visitors, file, indent=1)
            
    @staticmethod
    def load_all():
        """Charge tous les visiteurs enregistrés"""
        with open("database/visiteurs.json", "r", encoding="utf-8") as file:
            return json.load(file)