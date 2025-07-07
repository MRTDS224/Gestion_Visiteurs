import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
from models.user import Base, User, PasswordResetToken


class UserManager:
    """
    Gère la connexion à la base et les opérations CRUD sur les utilisateurs.
    """

    def __init__(self, 
        db_url: str = "postgresql+psycopg2://postgres:password@localhost/gestion_visiteurs",
        smtp_server: str = "smtp.exemple.com",
        smtp_port: int = 465,
        smtp_username: str = "no-reply@exemple.com",
        smtp_password: str = "votre_smtp_password"
        ):
        """
        Initialise la connexion à la base de données.
        :param db_url: URL SQLAlchemy pour PostgreSQL.
                       Exemple : postgresql://user:pwd@host:port/dbname
        """
        # --- Connexion DB ---
        # 1. Créer l'engine
        self.engine = create_engine(db_url, echo=False)

        # 2. Créer toutes les tables définies dans les modèles
        Base.metadata.create_all(self.engine)

        # 3. Créer un scoped_session pour thread‐safety
        factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.Session = scoped_session(factory)
        
        # --- Config SMTP ---
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password

    def add_user(self, nom: str, prenom: str, email: str, password: str, structure: str, role: str = "utilisateur") -> User:
        """
        Crée et enregistre un nouvel utilisateur.
        Lève ValueError si l'email existe déjà.
        """
        session = self.Session()
        try:
            # Vérifier l'unicité de l'email
            if session.query(User).filter_by(email=email).first():
                raise ValueError(f"Un utilisateur avec l'email {email} existe déjà.")

            # Instancier et remplir le modèle
            user = User(
                nom=nom,
                prenom=prenom,
                email=email,
                structure=structure,
                role=role
            )
            user.set_password(password)

            # Ajouter et commit
            session.add(user)
            session.commit()
            return user

        except IntegrityError as e:
            session.rollback()
            raise ValueError("Erreur d'intégrité en base de données.") from e

        finally:
            session.close()

    def get_user_by_email(self, email: str) -> User | None:
        """
        Retourne l'utilisateur correspondant à l'email, ou None.
        """
        session = self.Session()
        try:
            return session.query(User).filter_by(email=email).first()
        finally:
            session.close()

    def authenticate_user(self, email: str, password: str) -> bool:
        """
        Vérifie qu'un utilisateur existe et que le mot de passe est valide.
        """
        user = self.get_user_by_email(email)
        if not user:
            return False
        return user.verify_password(password)

    def list_users(self) -> list[User]:
        """
        Retourne la liste de tous les utilisateurs.
        """
        session = self.Session()
        try:
            return session.query(User).order_by(User.id).all()
        finally:
            session.close()

    def list_users_by_structure(self, structure: str) -> list[User]:
        session = self.Session()
        try:
            return session.query(User).filter_by(structure=structure).all()
        finally:
            session.close()
    
    def update_user(self, user_id: int, **fields) -> User:
        """
        Met à jour les champs fournis pour l'utilisateur d'ID donné.
        Exemple d'utilisation :
            update_user(3, nom="Dupont", role="admin")
        """
        session = self.Session()
        try:
            user = session.get(User, user_id)
            if not user:
                raise ValueError(f"Aucun utilisateur avec l'ID {user_id}.")

            # Ne pas autoriser la mise à jour directe du hash du password
            pwd = fields.pop("password", None)
            for key, value in fields.items():
                setattr(user, key, value)
            if pwd:
                user.set_password(pwd)

            session.commit()
            return user

        finally:
            session.close()

    def delete_user(self, user_id: int) -> None:
        """
        Supprime l'utilisateur d'ID donné.
        """
        session = self.Session()
        try:
            user = session.get(User, user_id)
            if not user:
                raise ValueError(f"Aucun utilisateur avec l'ID {user_id}.")
            session.delete(user)
            session.commit()
        finally:
            session.close()

    def close(self):
        """
        Ferme le scoped_session et le engine.
        À appeler si tu termines complètement la connexion à la base.
        """
        self.Session.remove()
        self.engine.dispose()

    def send_email(self, to_email: str, subject: str, body: str) -> None:
        """
        Envoie un email simple via SMTP SSL.
        """
        msg = EmailMessage()
        msg["From"] = self.smtp_username
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                smtp.login(self.smtp_username, self.smtp_password)
                smtp.send_message(msg)
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'envoi de l'email à {to_email}: {e}") from e
            
    def generate_reset_token(self, email: str) -> str:
        """
        Génère un token de réinitialisation, l'enregistre en base,
        envoie un email à l'utilisateur, et retourne le token (facultatif).
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(email=email).first()
            if not user:
                raise ValueError(f"Aucun utilisateur trouvé pour l'email {email}")

            # Créer le token et le persister
            reset = PasswordResetToken(user_id=user.id)
            session.add(reset)
            session.commit()

            # Envoyer le mail
            link = f"https://ton-domaine.com/reset-password?token={reset.token}"
            body = (
                f"Bonjour {user.prenom},\n\n"
                "Vous demandez la réinitialisation de votre mot de passe.\n"
                f"Utilisez ce code (ou lien) pour la réinitialisation :\n\n{reset.token}\n\n"
                f"Ou cliquez ici : {link}\n\n"
                "Ce code expire dans 1 heure.\n\n"
                "Si vous n'êtes pas à l'origine de cette demande, ignorez simplement ce message."
            )
            self.send_email(to_email=email, subject="Réinitialisation de votre mot de passe", body=body)

            return reset.token

        finally:
            session.close()

    def reset_password_with_token(self, token: str, new_password: str) -> None:
        """
        Vérifie le token, réinitialise le mot de passe et supprime le token.
        """
        session = self.Session()
        try:
            reset = session.query(PasswordResetToken).filter_by(token=token).first()
            if not reset or reset.expires_at < datetime.now(timezone.utc):
                raise ValueError("Token invalide ou expiré.")

            user = session.query(User).get(reset.user_id)
            if not user:
                raise ValueError("Utilisateur introuvable pour ce token.")

            # Met à jour le mot de passe
            user.set_password(new_password)

            # Supprime le token de la base
            session.delete(reset)
            session.commit()

        finally:
            session.close()