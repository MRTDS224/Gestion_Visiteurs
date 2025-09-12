from models.visitor import VisitorModel, db, VisitorShare
from managers.user_manager import UserManager
import json
from typing import Optional, Tuple, List

class VisitorManager:
    def __init__(self):
        self.session = UserManager().Session()
        
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
    
    def share_visitor(
        self, visitor, shared_by_id, shared_with_id, motif=None
    ):
        """Crée un partage en copiant les données du visitor."""
        session = self.session
        try:
            # Lire l’image sur disque
            with open(visitor.image_path, "rb") as f:
                img = f.read()

            share = VisitorShare(
                visitor_id=visitor.id,
                shared_by_user_id=shared_by_id,
                shared_with_user_id=shared_with_id,
                nom=visitor.nom,
                prenom=visitor.prenom,
                id_type=visitor.id_type,
                id_number=visitor.id_number,
                phone_number=visitor.phone_number,
                motif=motif or visitor.motif,
                image_data=img,
            )
            self.session.add(share)
            self.session.commit()
            return share.id
        except:
            session.rollback()
            raise 
        finally:
            session.close()


    def get_shares_for_user(self, user_id):
        """Liste les partages reçus par un utilisateur."""
        session = self.session
        try:
            return (
                session.query(VisitorShare)
                .filter_by(shared_with_user_id=user_id, status="active")
                .all()
            )
        finally:
            session.close()

    def revoke_share(self, share_id):
        """Révoque un partage existant."""
        session = self.session
        try:
            share = self.session.get(VisitorShare, share_id)
            if share and share.status == "active":
                share.status = "revoked"
                return True
            return False
        finally:
            session.close()


    def check_access(self, visitor_id, user_id):
        """Vérifie si un partage actif existe pour cet utilisateur."""
        session = self.session
        try:
            return (
                self.session.query(VisitorShare.id)
                .filter_by(visitor_id=visitor_id,
                        shared_with_user_id=user_id,
                        status="active")
                .first()
                is not None
            )
        finally:
            session.close()
