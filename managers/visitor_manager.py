from models.visitor import VisitorModel
import json

class VisitorManager:
    def __init__(self):
        self.visiteurs = VisitorModel.load_all()

    def ajouter_visiteur(self, image, nom, prenom, phone_number, id_type, id_number, motif):
        """Ajoute un visiteur et le sauvegarde"""
        new_visitor = VisitorModel(image, nom, prenom, phone_number, id_type, id_number, motif)
        VisitorModel.save_to_file(new_visitor)
        self.visiteurs.append(new_visitor.to_dict())
        return new_visitor

    def supprimer_visiteur(self, id_number):
        """Supprime un visiteur par son ID"""
        self.visiteurs = [v for v in self.visiteurs if v["id_number"] != id_number]

    def chercher_visiteur(self, id_number):
        """Recherche un visiteur par son numéro d'identité"""
        return next((v for v in self.visiteurs if v["id_number"] == id_number), None)
    
    def lister_visiteurs(self):
        """Retourne la liste de tous les visiteurs"""
        return self.visiteurs

    def exporter_visiteurs(self, chemin_fichier):
        """Exporte tous les visiteurs dans un fichier JSON."""
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(self.lister_visiteurs(), f, ensure_ascii=False, indent=2)

    def importer_visiteurs(self, chemin_fichier):
        """Importe des visiteurs depuis un fichier JSON et les ajoute à la base."""
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            visiteurs = json.load(f)
        for v in visiteurs:
            # Ajoute chaque visiteur (adapte selon ta logique d'unicité)
            self.ajouter_visiteur(
                v.get("image", ""),
                v.get("nom", ""),
                v.get("prenom", ""),
                v.get("phone_number", ""),
                v.get("id_type", ""),
                v.get("id_number", ""),
                v.get("motif", ""),
                v.get("observation", ""),
                v.get("date", ""),
                v.get("arrival_time", ""),
                v.get("exit_time", "")
            )
            
    def mettre_a_jour_sortie(self, id_number, exit_time, observation):
        # Mets à jour la ligne correspondante dans le fichier JSON
        visiteur = self.chercher_visiteur(id_number)
        if visiteur:
            visiteur["exit_time"] = exit_time
            visiteur["observation"] = observation
            # Sauvegarde les modifications dans le fichier JSON
            with open("database/visiteurs.json", "w", encoding="utf-8") as file:
                json.dump(self.visiteurs, file, ensure_ascii=False, indent=2)
            return True
        return False
        
    