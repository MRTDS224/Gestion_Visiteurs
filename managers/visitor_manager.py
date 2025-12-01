from models.visitor import Visitor
from models.user import VisitorShare
from managers.user_manager import UserManager
from datetime import datetime
import json
from typing import Optional, Tuple, List
import os
from helpers import resource_path

# db n'existe plus en tant qu'objet global, on utilise UserManager pour la session
class VisitorManager:
    def __init__(self):
        self.session = UserManager().Session()
    
    """ 
    Méthodes pour gérer les visiteurs dans la base de données.
    """
    
    def ajouter_visiteur(self, image_path: str, phone_number: str, place_of_birth: str, motif: str) -> Tuple[Optional[Visitor], Optional[str]]:
        """Ajoute un visiteur. Retourne le Visitor et un message d'erreur éventuel."""
        session = self.session
        try:
            visiteur = Visitor(
                image_path=image_path,
                phone_number=phone_number,
                place_of_birth=place_of_birth,
                motif=motif
            )
            session.add(visiteur)
            session.commit()
            return visiteur, None
        except Exception as e:
            session.rollback()
            return None, str(e)
        finally:
            session.close()
    
    def chercher_visiteur(self, visitor_id: int) -> Optional[Visitor]:
        """Recherche un visiteur par identifiant unique dans la base de données."""
        session = self.session
        try:
            return session.get(Visitor, visitor_id)
        finally:
            session.close()

    def lister_visiteurs(self) -> List[Visitor]:
        """Retourne la liste de tous les visiteurs."""
        session = self.session
        try:
            return session.query(Visitor).order_by(Visitor.id).all()
        finally:
            session.close()
    
    def mettre_a_jour_visiteur(self, visitor_id, **kwargs):
        """Met à jour les informations d'un visiteur."""
        session = self.session
        try:
            visitor = session.get(Visitor, visitor_id)
            if not visitor:
                return False, "Visiteur non trouvé."
            
            for key, value in kwargs.items():
                if hasattr(visitor, key):
                    setattr(visitor, key, value)
            
            session.commit()
            return True, None
        
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()
            
    def supprimer_visiteur(self, visitor_id: int) -> Tuple[bool, Optional[str]]:
        """Supprime un visiteur par son identifiant unique dans la base de données."""
        session = self.session
        try:
            visiteur = session.get(Visitor, visitor_id)
            if not visiteur:
                return False, "Visiteur non trouvé."
            session.delete(visiteur)
            session.commit()
            return True, None
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    """
    Méthodes pour l'import/export des visiteurs.
    """
    
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
                v.get("phone_number", ""),
                v.get("motif", "")
            )
    
    """
    Méthodes pour gérer le partage des visiteurs.
    """

    def accept_share(self, share_id):
        """Accepte un partage et ajoute le visiteur à la liste."""
        session = self.session
        try:
            share = self.session.get(VisitorShare, share_id)
            if not share or share.status != "active":
                return False
            
            # Générer un nom de fichier unique
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            image_dir = resource_path(os.path.join("pictures", "ID"))
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, f"imported_image_{share_id}_{timestamp}.jpg")
            
            visitor = Visitor(
                id=None,
                image_path=image_path,
                phone_number=share.phone_number,
                place_of_birth=share.place_of_birth,
                motif=share.motif,
            )
            # Sauvegarder l'image sur disque
            with open(visitor.image_path, "wb") as f:
                f.write(share.image_data)
            
            session.add(visitor)
            
            share.status = "accepted"
            session.commit()
            return True
        except:
            session.rollback()
            raise
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
    
    def edit_share_status(self, share: VisitorShare):
        """
        Met à jour le statut d'un partage en notified

        Args:
            share : Est un objet VisitorShare
        """
        session = self.session
        try:
            share.status = "notified"
            session.commit()
        finally:
            session.close()
          
    def get_active_shares_for_user(self, user_id):
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
    
    def get_shares_for_user(self, user_id):
        return (
            self.session.query(VisitorShare)
            .filter(
                VisitorShare.shared_with_user_id == user_id,
                VisitorShare.status != "revoked"
            )
            .all()
        )
        
    def revoke_share(self, share_id):
        """Révoque un partage existant."""
        session = self.session
        try:
            share = self.session.get(VisitorShare, share_id)
            if share and share.status == "active":
                share.status = "revoked"
                session.commit()
                return True
            return False
        finally:
            session.close()
            
    def share_visitor(self, visitor, shared_by_id, shared_with_id, motif=None):
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
                place_of_birth=visitor.place_of_birth,
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
