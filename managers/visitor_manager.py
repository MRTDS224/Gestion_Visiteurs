from models.visitor import VisitorModel, db
import json
from typing import Optional, Tuple, List

class VisitorManager:
    def ajouter_visiteur(self, image_path: str, nom: str, prenom: str, phone_number: str, id_type: str, id_number: str, motif: str) -> Tuple[Optional[VisitorModel], Optional[str]]:
        """Ajoute un visiteur et le sauvegarde. Retourne le VisitorModel et un message d'erreur éventuel."""
        visitor_id = db.add_visitor(image_path, nom, prenom, phone_number, id_type, id_number, motif)
        if not visitor_id:
            return None, "Erreur lors de l'ajout du visiteur"
        return VisitorModel(visitor_id, image_path, nom, prenom, phone_number, id_type, id_number, motif), None

    def supprimer_visiteur(self, visitor_id: int) -> Tuple[bool, Optional[str]]:
        """Supprime un visiteur par son identifiant unique dans la base de données."""
        success = db.delete_visitor(visitor_id)
        if not success:
            return False, "Suppression échouée"
        return True, None

    def chercher_visiteur(self, visitor_id: int) -> Optional[VisitorModel]:
        """Recherche un visiteur par identifiant unique dans la base de données."""
        return db.get_visitor_by_id(visitor_id)

    def lister_visiteurs(self) -> List[VisitorModel]:
        """Retourne la liste de tous les visiteurs."""
        return db.get_all_visitors()

    def exporter_visiteurs(self, chemin_fichier):
        """Exporte tous les visiteurs dans un fichier JSON."""
        visiteurs = self.lister_visiteurs()
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump([v.to_dict() for v in visiteurs], f, ensure_ascii=False, indent=4)
            
    def importer_visiteurs(self, chemin_fichier):
        """Importe des visiteurs depuis un fichier JSON et les ajoute à la base."""
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            visiteurs = json.load(f)
        for v in visiteurs:
            self.ajouter_visiteur(
                v.get("image_path", ""),
                v.get("nom", ""),
                v.get("prenom", ""),
                v.get("phone_number", ""),
                v.get("id_type", ""),
                v.get("id_number", ""),
                v.get("motif", "")
            )
            
    def mettre_a_jour_visiteur(self, visitor_id, **kwargs):
        """Met à jour les informations d'un visiteur."""
        success = db.update_visitor(visitor_id, **kwargs)
        if not success:
            return False, "Aucune modification effectuée"
        
        return True, None