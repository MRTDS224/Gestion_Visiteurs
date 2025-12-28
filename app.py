import contextlib
import os
os.environ['KIVY_GL_BACKEND'] = 'sdl2'

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import (
    MDDialog, MDDialogHeadlineText,
    MDDialogButtonContainer, MDDialogContentContainer
)
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon, MDIconButton
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText, MDTextFieldLeadingIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.menu import MDDropdownMenu

from kivymd.uix.appbar import MDActionTopAppBarButton
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.fitimage import FitImage
from kivymd.uix.card import MDCard
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import (
    MDList, MDListItem, MDListItemLeadingIcon,
    MDListItemHeadlineText, MDListItemSupportingText,
    MDListItemTertiaryText
)
from kivy.uix.screenmanager import SlideTransition
from kivymd.uix.tooltip import MDTooltip
from managers import DocumentManager, UserManager, VisitorManager
from models import User
from helpers import resource_path, setup_logger
import sys
from datetime import datetime, timezone
from PIL import Image
from pathlib import Path
import tempfile
from plyer import filechooser, notification
import tkinter as _tk
from tkinter import filedialog as _fd
import time
import webbrowser
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy.orm import make_transient

from kivy.factory import Factory

__version__ = "1.0.0"

logger = setup_logger()

class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.menu = None
        self.icon = None
        
    def accept_share(self, share_id):
        """Accepte un partage de visiteur. Et ajoute le visiteur à la liste."""
        app = MDApp.get_running_app()
        try:
            response = app.visitor_manager.accept_share(share_id)
            if not response:
                app.show_error_dialog("Le partage est déjà révoqué ou n'existe pas.")
                return
        except Exception as e:
            app.show_error_dialog("Erreur lors de l'acceptation du partage")
            logger.error(f"L'erreur suivante vient de se produire {e}")
            return
        
        if self.menu:
            self.menu.dismiss()
            
        self.dialog.dismiss()
        app.show_info_snackbar("Partage accepté. Le visiteur ajouté à votre liste.", str(share_id))
        app.afficher_heros_visiteurs()
        
    def open_share_menu(self, share_id):
        """Ouvre le menu contextuel pour un partage donné."""
        if self.menu:
            self.menu.dismiss()
        
        items = [
            {
                "text": "Accepter",
                "on_release": lambda *args: self.accept_share(share_id)
            },
            {
                "text": "Refuser",
                "on_release": lambda *args: self.refuse_share(share_id)
            },
        ]
        
        self.menu = MDDropdownMenu(
            caller=self.icon,
            items=items,
            width=dp(150),
            position="center",
        )
        self.menu.open()
        
    def open_notifications(self):
        """Ouvre un dialogue listant les notifications par ordre d’arrivée."""
        app = MDApp.get_running_app()
        user_id = app.user.id
        shares = app.visitor_manager.get_active_shares_for_user(user_id)
        shares_sorted = sorted(shares, key=lambda s: s.shared_at)
        
        def format_share(share):
            shared_by_user = MDApp.get_running_app().user_manager.get_user_by_id(share.shared_by_user_id)
            ts = share.shared_at.strftime("%d/%m/%Y %H:%M")
            content =  MDListItem(
                MDListItemLeadingIcon(
                    icon="account",
                ),
                MDListItemHeadlineText(
                    text="Vous avez un nouveau partage",
                ),
                MDListItemSupportingText(
                    text=f"De la part de {shared_by_user.nom} {shared_by_user.prenom} le {ts}",
                ),
                divider = True,
                theme_bg_color="Custom",
                md_bg_color=self.theme_cls.transparentColor
            )
            icon = MDIconButton(
                    icon="dots-vertical",
                    on_release=lambda x, share_id=share.id: self.open_share_menu(share_id)
                )
            self.icon = icon
            content.add_widget(icon)
            return content
        
        app.open_share_dialog("Visiteur partagé avec vous", shares_sorted, format_share)
        
    def refuse_share(self, share_id):
        """Refuse un partage de visiteur."""
        app = MDApp.get_running_app()
        try:
            response = app.visitor_manager.revoke_share(share_id)
            if not response:
                app.show_error_dialog("Le partage est déjà révoqué ou n'existe pas.")
                return
        except Exception as e:
            app.show_error_dialog("Erreur lors du refus du partage")
            logger.error(f"L'erreur suivante vient de se produire {e}")
            return
        
        self.menu.dismiss()
        self.dialog.dismiss()
        
        app.show_info_snackbar("Partage refusé.", str(share_id))
        
class DetailScreen(MDScreen):
    def on_leave(self, *args):
        self.ids.image.source = ""
        self.ids.phone_number.text = ""
        self.ids.place_of_birth.text = ""
        self.ids.motif.text = ""
        self.ids.date.text = ""
        self.ids.arrival_time.text = ""
        self.ids.exit_time.text = ""
        self.ids.observation.text = ""
        
        self.ids.btn_delete.disabled = False
        self.ids.btn_share.disabled = False
        
        app = MDApp.get_running_app()
        app.selected_image_path = ""
        app.visiteur = None
        app.afficher_heros_visiteurs()
   
class AccountScreen(MDScreen):
    def enable_butons(self):
        self.ids.btn_save.disabled = False
        self.ids.btn_cancel.disabled = False

    def on_enter(self):
        self.populate_fields()

    def populate_fields(self, user=None):
        app = MDApp.get_running_app()
        user = app.user
        
        self.ids.account_last_name.text = user.nom or ""
        self.ids.account_first_name.text = user.prenom or ""
        self.ids.account_email.text = user.email or ""
        self.ids.account_password_first.text = ""
        self.ids.account_password_second.text = ""
        self.ids.account_role.text = user.role or ""
        
        self.ids.btn_save.disabled = True
        self.ids.btn_cancel.disabled = True

    def update_user(self):
        nom     = self.ids.account_last_name.text.strip()
        prenom  = self.ids.account_first_name.text.strip()
        email   = self.ids.account_email.text.strip()
        pwd1    = self.ids.account_password_first.text.strip()
        pwd2    = self.ids.account_password_second.text.strip()
        role    = self.ids.account_role.text.strip()
        
        
        if pwd1 or pwd2:
            if pwd1 != pwd2:
                return app.show_error_dialog("Les mots de passe doivent être identiques.")
            if len(pwd1) < 8:
                return app.show_error_dialog("Le mot de passe doit faire au moins 8 caractères.")
        
        params = {}
        app = MDApp.get_running_app()
        user = app.user
        
        if nom and nom != user.nom:
            params["nom"] = nom
        if prenom and prenom != user.prenom:
            params["prenom"] = prenom
        if email and email != user.email:
            params["email"] = email
        if pwd1:
            params["password"] = pwd1
        if role and role != user.role:
            params["role"] = role
        
        if not params:
            self.populate_fields()
            return app.show_error_dialog("Aucune modification détectée.")

        # Appel au UserManager (décompactage des kwargs)
        try:
            app.user_manager.update_user(user.id, **params)
            app.user = app.user_manager.get_user_by_email(email)
            app.show_info_snackbar("Profil mis à jour avec succès.", str(user.id))
            
            # On recharge l’affichage et on désactive à nouveau
            self.populate_fields()
        except ValueError as e:
            app.show_error_dialog("Une erreur s'est produite")
            logger.error(f"L'erreur suivante vient de se produire {e}")
    
    def annuler_modification_utilisateur(self):
        self.populate_fields()

    def on_leave(self, *args):
        self.ids.account_last_name.text = ""
        self.ids.account_first_name.text = ""
        self.ids.account_email.text = ""
        self.ids.account_password_first.text = ""
        self.ids.account_password_second.text = ""
        self.ids.account_role.text = ""

class LoginScreen(MDScreen):
    show_login_password = BooleanProperty(True)
    def login(self):
        email = self.ids.login_email.text.rstrip()
        password = self.ids.login_password.text.rstrip()
        
        if not email or not password:
            MDApp.get_running_app().show_error_dialog("Tous les champs sont obligatoires.")
            return
        
        MDApp.get_running_app().login(email, password)
    
    def on_leave(self, *args):
        self.ids.login_email.text = ""
        self.ids.login_password.text = ""
        
class SignupScreen(MDScreen):
    def signup(self):
        last_name = self.ids.signup_last_name.text.rstrip()
        first_name = self.ids.signup_last_name.text.rstrip()
        email = self.ids.signup_email.text.rstrip()
        password_first = self.ids.signup_password_first.text.rstrip()
        password_second = self.ids.signup_password_second.text.rstrip()
        role = self.ids.signup_role.text.rstrip().lower()
        
        if not all([last_name, first_name, email, password_first, password_second, role]):
            MDApp.get_running_app().show_error_dialog("Tous les champs sont obligatoires.")
            return
            
        if password_second != password_first:
            MDApp.get_running_app().show_error_dialog("Les deux mots de passes doivent être identiques.")
            return
        
        if len(password_first) < 8:
            MDApp.get_running_app().show_error_dialog("La longueur minimale du mot de passe est de 8 caractères.")
            return
        
        if role not in ["huissier", "autre"]:
            MDApp.get_running_app().show_error_dialog("Les rôles autorisés pour le moment sont soit Huissier ou soit Autre.")
            return
        
        MDApp.get_running_app().signup(last_name, first_name, email, password_first, role.capitalize())

    def on_leave(self, *args):
        self.ids.signup_last_name.text = ""
        self.ids.signup_first_name.text = ""
        self.ids.signup_email.text = ""
        self.ids.signup_password_first.text = ""
        self.ids.signup_password_second.text = ""
        self.ids.signup_role.text = ""

class ResetPasswordScreen(MDScreen):
    def on_leave(self, *args):
        self.ids.reset_email.text = ""

class CodeInputScreen(MDScreen):
    def on_leave(self, *args):
        self.ids.reset_code.text = ""

class NewPasswordScreen(MDScreen):
    def on_leave(self, *args):
        self.ids.new_password_first.text = ""
        self.ids.new_password_second.text = ""

class TooltipMDIconButton(MDTooltip, MDIconButton):
    '''Implements a button with tooltip behavior.'''

    texte = StringProperty()
    icon = StringProperty()

class ToolMDActionButton(MDTooltip, MDActionTopAppBarButton):
    texte = StringProperty()
        
class Gestion(MDApp):
    visiteur = ObjectProperty(None, allownone=True)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.visitor_manager = VisitorManager()
        self.user_manager = UserManager()
        self.document_manager = DocumentManager()
        self.icon = resource_path("pictures/logo1.jpg")
        self.title = "GestionVisiteurs"
        self.dialog = None
        self.user = None
        self.file_manager_mode = None
        self.selected_document_path = ""
        self.selected_image_path = ""
        self.menu = MDDropdownMenu(
            position="bottom",
            width=dp(300),
        )
        self._notified_share_ids = set()
        self._notified_doc_ids = set()
        self._notify_poll_interval = 10
        
    def activer_boutons_modification(self):
        screen = self.root.get_screen("screen B")
        screen.ids.btn_cancel.disabled = False
        screen.ids.btn_save.disabled = False
    
    def afficher_heros_visiteurs(self, visiteurs=None):
        box = self.root.get_screen("screen A").ids.box
        box.clear_widgets()
        
        if visiteurs is None:
            visiteurs = self.visitor_manager.lister_visiteurs()
        
        box.add_widget(   
            MDCard(
                FitImage(
                    source=resource_path("pictures/add-user-icon.jpg"),
                    size_hint_y=None,
                    height=dp(200)
                ),
                MDLabel(
                    text="Ajouter un visiteur",
                    halign="center",
                    size_hint_y=None,
                    height=dp(30),
                    font_size='12sp',
                ),
                orientation="vertical",
                padding=10,
                ripple_behavior=True,
                size_hint_y=None,
                height=dp(250),
                size_hint_x=0.2,
                on_release=lambda x: self.show_visitor_details()
            )
        )
            
        for visiteur in visiteurs:
            layout = MDCard(
                orientation="vertical",
                padding=10,
                size_hint_y=None,
                height=dp(250),
                size_hint_x=0.2,
                on_release=lambda x, v=visiteur: self.show_visitor_details(v)
            )
            layout.add_widget(FitImage(
                source=visiteur.image_path,
                size_hint_y=None,
                height=dp(200)
            ))
            layout.add_widget(MDLabel(
                text=f"Visiteur {visiteur.id} - N° {visiteur.phone_number}",
                halign="left",
                font_size='12sp',
                size_hint_y=None,
                height=dp(30),
            ))
            
            box.add_widget(layout)
                
    def animer_bouton(self, bouton):
        anim = Animation(opacity=0.5, duration=0.1) + Animation(opacity=1, duration=0.1)
        anim.start(bouton)
        
    def annuler_modifications(self):
        self.remplir_champs()
        
        screen = self.root.get_screen("screen B")
        screen.ids.btn_save.disabled = True
        screen.ids.btn_cancel.disabled = True
        
    def build(self):        
        return Builder.load_file(resource_path("main.kv"))
    
    def check_code(self):
        token = self.root.get_screen("code_input").ids.reset_code.text
        
        if not token:
            self.show_error_dialog("Veillez entrez le code reçu par mail.")
            return
        
        if token != self.token:
            self.show_error_dialog("Le code saisi est incorrecte. Veuillez réessayer.")
            return
        
        self.root.current = "new_password"
        self.root.get_screen("code_input").ids.reset_code.text = ""

    def create_text_field(self, hint, icon=None, required=True):
        field = MDTextField(
            MDTextFieldHintText(text=hint),
            required=required,
            mode="outlined",
            size_hint_x=None,
            width="300dp",
        )
        
        if icon:
            field.add_widget(MDTextFieldLeadingIcon(icon=icon))

        return field
        
    def creer_bouton(self, texte, style="text", icone=None, on_release=None):
        """Crée un bouton MDButton avec texte, style, icône et callback."""
        elements = []
        if icone:
            elements.append(MDButtonIcon(icon=icone))
        elements.append(MDButtonText(text=texte))
        kwargs = {"style": style, "size_hint": (None, None), "height": dp(40)}

        def _on_release(instance):
            self.animer_bouton(instance)
            if on_release:
                on_release(instance)

        if on_release is not None:
            kwargs["on_release"] = _on_release

        return MDButton(
            *elements,
            **kwargs
        )
       
    def creer_dialogue(self, titre, content, actions):
        dialog = MDDialog(
            MDDialogHeadlineText(text=titre, halign="left"),
            MDDialogContentContainer(content),
        )
        dialog.adaptive_height = True
        
        if actions:
            dialog.add_widget(
                MDDialogButtonContainer(
                    *actions,
                    spacing="10dp"
                )
            )
            dialog.auto_dismiss = False
            
        dialog.open()
        return dialog
    
    def delete_visitor(self):
        def annuler_suppression():
            self.dialog.dismiss()
            return
        
        def confirmer_suppression():
            vis_id = self.visiteur.id
            succes, error = self.visitor_manager.supprimer_visiteur(vis_id)
            if error:
                self.show_error_dialog(error)
                return
            
            self.dialog.dismiss()
            self.show_info_snackbar("Visiteur supprimé avec succès.", str(vis_id))
            
            self.root.current = "screen A"
            self.afficher_heros_visiteurs()
        
        # Ouvrir un dialgue de confirmation
        content = MDLabel(
            text="Etes vous sûr de vouloir supprimer ce visiteur. Cette action est irréversible.",
            halign="center",
            size_hint_y=None,
            height=dp(30),
        )
        actions = [
            Widget(),
            self.creer_bouton(
                "Annuler",
                style="text",
                on_release=lambda x: annuler_suppression()
            ),
            self.creer_bouton(
                "Supprimer",
                style="elevated",
                on_release=lambda x: confirmer_suppression()
            ),
        ]
        self.dialog = self.creer_dialogue("Confirmer la suppression", content, actions)
    
    def demander_numero(self):
        # Demander le numéro via tkinter dialog
        try:
            import tkinter as tk
            from tkinter import simpledialog
            root = tk.Tk()
            root.withdraw()
            phone = simpledialog.askstring("WhatsApp", "Numéro destinataire (format +CCNNNN..., ex: +2126******06) :")
            root.destroy()
        except Exception as e:
            self.show_error_dialog("Erreur lors de la saisie du numéro.")
            logger.error(f"L'erreur suivante vient de se produire {e}")
            phone = None
        
        return phone
        
    def enregistrer_modifications(self):
        try:
            screen = self.root.get_screen("screen B")

            if self.selected_image_path:
                image_path = self.selected_image_path
            elif self.visiteur and self.visiteur.image_path:
                image_path = self.visiteur.image_path
            else:
                image_path = ""

            phone_number = screen.ids.phone_number.text
            place_of_birth = screen.ids.place_of_birth.text
            motif = screen.ids.motif.text
            date = screen.ids.date.text
            arrival_time = screen.ids.arrival_time.text
            exit_time = screen.ids.exit_time.text
            observation = screen.ids.observation.text

            if self.visiteur is None:
                self.enregistrer_visiteur(
                    image_path=image_path,
                    phone_number=phone_number,
                    place_of_birth=place_of_birth,
                    motif=motif
                )
                return self.masquer_bouttons(screen)
            if not all([phone_number, place_of_birth, motif, date, arrival_time, exit_time, observation]):
                return self.show_error_dialog("Tous les champs doivent être remplis pour enregistrer les modifications.")

            success, error = self.visitor_manager.mettre_a_jour_visiteur(
                self.visiteur.id, image_path=image_path,
                phone_number=phone_number,
                place_of_birth=place_of_birth, motif=motif,
                date=date, arrival_time=arrival_time,
                exit_time=exit_time, observation=observation
            )

            if not success:
                self.show_error_dialog(error or "Erreur lors de la mise à jour du visiteur.")
                return

            screen.ids.btn_save.disabled = True
            screen.ids.btn_cancel.disabled = True
            self.show_info_snackbar("Modifications enregistrées avec succès!", str(self.visiteur.id))

            # Rafraîchir l'affichage
            self.visiteur = self.visitor_manager.chercher_visiteur(self.visiteur.id)
            self.remplir_champs()
            self.afficher_heros_visiteurs()

            self.selected_image_path = ""

        except Exception as e:
            self.show_error_dialog("Erreur lors de la modification.")
            logger.error(f"L'erreur suivante vient de se produire {e}")
            
    def enregistrer_visiteur(self, image_path, phone_number, place_of_birth, motif):
        try:
            if erreur := self.valider_champs(phone_number, place_of_birth, motif):
                self.show_error_dialog(erreur)
                return

            self.visitor_manager.ajouter_visiteur(image_path, phone_number, place_of_birth, motif)
            self.show_info_snackbar("Visiteur ajouté avec succès!")
            self.root.current = "screen A"

        except Exception as e:
            self.show_error_dialog("Erreur lors de l'ajout.")
            logger.error(f"L'erreur suivante vient de se produire {e}")

    def envoyer_image_visiteur_whatsapp(self, *args):
        """
        Envoi via WhatsApp Web avec pywhatkit.
        - Texte + image obligatoires ensemble.
        - Lève une erreur si l'image manque.
        - Demande le numéro destinataire via dialog.
        """
        try:
            import pywhatkit as pw
        except Exception as e:
            logger.error(f"Une erreur s'est produite {e}")
            self.show_error_dialog("Désolé il faut être connecté à internet pour pouvoir faire ce partage.")
            return

        if not self.visiteur:
            self.show_error_dialog("Aucun visiteur sélectionné.")
            return

        lignes = [
            f"Téléphone : {self.visiteur.phone_number}",
            f"Motif : {self.visiteur.motif}",
            f"Date : {self.visiteur.date}"
        ]
        texte = "\n".join(lignes)

        # Vérifier que l'image existe — c'est obligatoire
        if not self.visiteur.image_path or not os.path.exists(self.visiteur.image_path):
            self.show_error_dialog("Impossible d'envoyer : l'image de la pièce d'identité est manquante.")
            return

        phone = self.demander_numero()
        
        if not phone:
            self.show_error_dialog("Aucun numéro fourni. Envoi annulé.")
            return

        # Envoyer via pywhatkit
        try:
            self.show_info_snackbar("Préparation de l'envoi WhatsApp... Veuillez patienter.")

            pw.sendwhats_image(
                receiver=phone,
                img_path=self.visiteur.image_path,
                caption=texte,
                wait_time=15,
                tab_close=True,
                close_time=10
            )

            self.show_info_snackbar("Envoi WhatsApp lancé avec succès. Veuillez vérifier votre navigateur.")

        except FileNotFoundError as fe:
            self.show_error_dialog("Erreur : le fichier image est introuvable.")
            logger.error(f"L'erreur suivante vient de se produire {fe}")
        except Exception as e:
            self.show_error_dialog("Erreur lors de l'envoi WhatsApp.")
            logger.error(f"L'erreur suivante vient de se produire {e}")
               
    def exit_file_manager(self, *args):
        self.file_manager.close()
    
    def filtrer(self, year, month, day):
        visiteurs = self.visitor_manager.lister_visiteurs()
        result = []
        for v in visiteurs:
            try:
                d = datetime.strptime(v.date, "%Y-%m-%d")
            except Exception as e:
                logger.error(f"L'erreur suivante vient de se produire {e}")
            if year and str(d.year) != year:
                continue
            if month and str(d.month).zfill(2) != month.zfill(2):
                continue
            if day and str(d.day).zfill(2) != day.zfill(2):
                continue
            result.append(v)
        
        if not result:
            box = self.root.get_screen("screen A").ids.box
            box.clear_widgets()
            box.add_widget(MDLabel(
                text=f"Aucun visiteur ne correspond aux critères de recherche, le {day} / {month} / {year}. Veuillez réessayer.",
                halign="center",
                size_hint_y=None,
                height=dp(70)
            ))
            return
            
        self.afficher_heros_visiteurs(result)
    
    def get_field(self, field_name):
        """Retourne le champ de date correspondant au nom."""
        
        screen = self.root.get_screen("screen A")
        if "day" in field_name:
            return screen.ids.day_filter
        elif "month" in field_name:
            return screen.ids.month_filter
        elif "year" in field_name:
            return screen.ids.year_filter
        else:
            raise ValueError(f"Champ inconnu : {field_name}")
    
    def login(self, email, password):
        if not email or not password:
            self.show_error_dialog("Tous les champs sont obligatoires.")
            return
        
        try:
            user, error = self.user_manager.authenticate_user(email, password)
        except Exception as e:
            self.show_error_dialog("Erreur lors de l'authentification.")
            logger.error(f"L'erreur suivante vient de se produire {e}")
            return
        
        if error:
            self.show_error_dialog(error)
            return
        
        # Détache l'utilisateur de la session pour éviter les problèmes plus tard
        make_transient(user)
        
        self.user = user
        self.root.current = "screen A"
        self.show_info_snackbar("Connexion réussie!", str(self.user.id))  
    
    def notify_new_items(self, manager, item_type: str):
        """Poll les nouveaux items et envoie des notifications."""
        try:
            # Utilise la session du manager pour les requêtes
            with manager.Session() as session:
                items = manager.get_shares_for_user(self.user.id)
                for item in items:
                    # Recharge l'item dans la session active
                    item = session.merge(item)
                    shared_by_user = self.user_manager.get_user_by_id(item.shared_by_user_id)
                    self.notify_new_share(shared_by_user, item_type)
                    manager.edit_share_status(item)
        except Exception as e:
            logger.error(f"L'erreur suivante vient de se produire {e}")
      
    def notify_new_share(self, shared_by_user: User, share_type: str):
        try:
            notification.notify(
                title=f"Nouveau {share_type} reçu",
                message=f"Vous avez reçu un {share_type} de la part de {shared_by_user.prenom} {shared_by_user.nom}.",
                app_name="GestionVisiteurs",
                app_icon=resource_path("pictures/icone.ico"),
                timeout=5
            )
        except Exception as e:
            logger.error(f"L'erreur suivante vient de se produire {e}")
             
    def on_start(self):
        logger.info("Lancement de l'application")
        
        work_dir = os.path.join(os.path.expanduser("~"), "Documents", "GestionVisiteur")
        os.makedirs(work_dir, exist_ok=True)
        os.chdir(work_dir)
        
        logger.info(f"Répertoire de travail défini sur : {os.getcwd()}")
        
        self.afficher_heros_visiteurs()
        Clock.schedule_interval(self._poll_for_new_items, self._notify_poll_interval)
    
    def _poll_for_new_items(self, dt):
        """Poll périodique : récupère les partages/documents actifs et notifie."""
        if not self.user:
            return

        # visitors
        with contextlib.suppress(Exception):
            shares = self.visitor_manager.get_active_shares_for_user(self.user.id)
            for s in shares:
                if s.id not in self._notified_share_ids:
                    shared_by_user = self.user_manager.get_user_by_id(s.shared_by_user_id)
                    self.notify_new_share(shared_by_user, "visiteur")
                    # marque comme traité (ton manager semble proposer cette méthode)
                    with contextlib.suppress(Exception):
                        self.visitor_manager.edit_share_status(s)
                    self._notified_share_ids.add(s.id)
        # documents
        with contextlib.suppress(Exception):
            docs = self.document_manager.get_active_shares_for_user(self.user.id)
            for d in docs:
                if d.id not in self._notified_doc_ids:
                    shared_by_user = self.user_manager.get_user_by_id(d.shared_by_user_id)
                    self.notify_new_share(shared_by_user, "document")
                    with contextlib.suppress(Exception):
                        self.document_manager.edit_share_status(d)
                    self._notified_doc_ids.add(d.id)

    def open_document(self, document):
        blob, filename = self.document_manager.get_document_blob(document.id)
        # créer un fichier temporaire
        suffix = "." + filename.split(".")[-1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(blob)
        tmp.close()
        # l’ouvrir dans le navigateur/application par défaut
        webbrowser.open(tmp.name)
        
        # supprimer le fichier temporaire après un délai
        Clock.schedule_once(lambda dt: os.remove(tmp.name), 300)

    def open_document_dialog(self):
        """_summary_: ouvre un dialogue contenant les documents partagés avec l'utilisateur.
        """
        user_id = self.user.id
        documents = self.document_manager.get_shares_for_user(user_id)
        
        if not documents:
            self.show_info_snackbar("Aucun document partagé avec vous pour le moment.")
            return
        
        def format_document(doc):
            shared_by_user = self.user_manager.get_user_by_id(doc.shared_by_user_id)
            ts = doc.shared_at.strftime("%d/%m/%Y %H:%M")
            item =  MDListItem(
                MDListItemLeadingIcon(
                    icon="file",
                ),
                MDListItemHeadlineText(
                    text=f"Document ID: {doc.id}",
                ),
                MDListItemSupportingText(
                    text=f"Partagé par {shared_by_user.nom} {shared_by_user.prenom} le {ts}",
                ),
                MDListItemTertiaryText(
                    text=f"Type: {doc.document_type.upper()}",
                ),
                divider = True,
                theme_bg_color="Custom",
                md_bg_color=self.theme_cls.transparentColor
            )
            item.add_widget(MDIconButton(
                    icon="eye-outline",
                    on_release=lambda x, d=doc:self.open_document(d)
                )
            )
            return item
        
        self.open_share_dialog(
            title="Documents partagés avec vous",
            items=documents,
            formatter=format_document
        )
    
    def open_share_dialog(self, title: str, items: list, formatter: callable):
        """
        Affiche un MDDialog contenant une liste scrollable d'éléments formatés.
        
        :param title: Titre du dialogue
        :param items: Liste des objets à afficher
        :param formatter: Fonction qui retourne un widget formaté pour chaque objet
        """
        if not items:
            self.show_info_snackbar("Aucun élément à afficher pour le moment.")
            return

        content = MDList(spacing=10, size_hint_y=None, adaptive_height=True)
        for item in items:
            content.add_widget(formatter(item))

        content.bind(minimum_height=content.setter('height'))
        scroll = ScrollView(
            size_hint_y=None,
            height=dp(400),
            bar_width=dp(4),
            scroll_type=['bars', 'content'],
            do_scroll_x=False
        )
        scroll.add_widget(content)

        self.dialog = self.creer_dialogue(title, scroll, actions=[])
    
    def _tk_file_dialog(self, filetypes, multiple=False):
        """Fallback tkinter file dialog returning a list like plyer."""
        try:
            root = _tk.Tk()
            root.withdraw()
            if multiple:
                paths = list(_fd.askopenfilenames(parent=root, filetypes=filetypes))
            else:
                p = _fd.askopenfilename(parent=root, filetypes=filetypes)
                paths = [p] if p else []
            root.destroy()
            return paths
        except Exception as e:
            logger.error(f"L'erreur suivante vient de se produire {e}")
          
    def open_document_filechooser(self):
        self.file_manager_mode = "document"
        try:    
            filechooser.open_file(
                filters=["*", "(;*.pdf;*.txt;*.doc;*.docx;*.xls;*.xlsx;*.ppt;*.pptx)", "(;*.png;*.jpg;*.jpeg;*.bmp;*.gif)"],
                on_selection=self.select_file,
                multiple=True
            )
        except NotImplementedError as e:
            logger.error(f"L'erreur suivante vient de se produire {e}")
            logger.info("Lancement du filechooser avec TKINTER")
            types = ["*", ("Documents", ("*.pdf", "*.txt", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx"))]
            if sel:= self._tk_file_dialog(types, multiple=True):
                self.select_file(sel)
                
    def open_image_filechooser(self):
        self.file_manager_mode = "image"
        try:
            filechooser.open_file(
                filters=["(;*.png;*.jpg;*.jpeg;*.bmp;*.gif)", "(;*.pdf;*.txt;*.doc;*.docx;*.xls;*.xlsx;*.ppt;*.pptx)"],
                on_selection=self.select_file,
                multiple=True
            )
        except NotImplementedError as e:
            logger.error(f"L'erreur suivante vient de se produire {e}")
            logger.info("Lancement du filechooser avec TKINTER")
            types = [("Images", ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"))]
            if sel:= self._tk_file_dialog(types, multiple=True):
                self.select_file(sel)

    def open_menu(self, field_name):
        screen_ids = self.root.get_screen("screen B").ids
        if field_name == "id":
            items = [
                {"text": "Passeport", "on_release": lambda x="Passeport": self.set_text(x, "id")},
                {"text": "Carte", "on_release": lambda x="Carte": self.set_text(x, "id")},
            ]
            
            self.menu.caller=screen_ids.id_type
            self.menu.items=items
            
        elif field_name == "motif":
            items = [
                {"text": "Consulat", "on_release": lambda x="Consulat": self.set_text(x, "motif")},
                {"text": "Attestation de couverture", "on_release": lambda x="Attestation de couverture": self.set_text(x, "motif")},
                {"text": "Demande de prise en charge", "on_release": lambda x="Demande de prise en charge": self.set_text(x, "motif")},
                {"text": "Légalisation", "on_release": lambda x="Légalisation": self.set_text(x, "motif")},
            ]
            self.menu.caller=screen_ids.motif
            self.menu.items=items
            
        else:
            months = ["Janvier", "Février", "Mars", "Avril", "May", "Juin",
                "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
            days_items = [
                {
                    "text": f"{i}",
                    "on_release": lambda x=f"{i}": self.set_item(x, "day_filter"),
                } for i in range(1, 32)]
            months_items = [
                {
                    "text": months[i],
                    "on_release": lambda x=str(i+1): self.set_item(x, "month_filter"),
                } for i in range(len(months))]
            years_items = [
                {
                    "text": str(year),
                    "on_release": lambda x=str(year): self.set_item(x, "year_filter"),
                } for year in range(2024, datetime.now(timezone.utc).year + 1)
            ]
            if "day" in field_name:
                items = days_items
            elif "month" in field_name:
                items = months_items
            elif "year" in field_name:
                items = years_items
            else:
                return
            
            self.menu.items = items
            self.menu.caller = self.get_field(field_name)
            self.menu.width = dp(100)
        
        self.menu.open()
            
    def ouvrir_dialogue_partager(self):
        email_button = self.creer_bouton(
            "Envoyer par mail",
            style="outlined",
            icone="email",
            on_release=lambda x: self.envoyer_par_mail()
        )
        whatsapp_button  = self.creer_bouton(
            "Envoyer par whatsapp",
            style="outlined",
            icone="whatsapp",
            on_release=lambda x: self.envoyer_image_visiteur_whatsapp()
        )
        
        content = MDGridLayout(cols=2, spacing=10, size_hint_y=None, adaptive_height=True)
        content.add_widget(email_button)
        content.add_widget(whatsapp_button)
        for user in self.user_manager.list_users():
            if user.id != self.user.id:
                button = self.creer_bouton(
                    f"Partager avec {user.prenom} {user.nom}",
                    style="outlined",
                    icone="account",
                    on_release=self.share_visitor(self.visiteur, self.user.id, user.id)
                )
                content.add_widget(button)
        
        actions = [
            Widget(),
            self.creer_bouton(
            "Annuler",
            style="text",
            on_release=lambda x: self.dialog.dismiss(),
            ),
        ]
        
        self.dialog = self.creer_dialogue("Partager", content, actions)
            
    def remplir_champs(self):
        screen = self.root.get_screen("screen B")
        if self.visiteur is None:
            return self._remplir_champs_(screen)
        screen.ids.phone_number.text = self.visiteur.phone_number
        screen.ids.place_of_birth.text = self.visiteur.place_of_birth or ""
        screen.ids.motif.text = self.visiteur.motif
        screen.ids.date.text = self.visiteur.date
        screen.ids.arrival_time.text = self.visiteur.arrival_time
        screen.ids.exit_time.text = self.visiteur.exit_time or ""
        screen.ids.observation.text = self.visiteur.observation or ""

        screen.ids.image.source = self.visiteur.image_path
        self.masquer_bouttons(screen)

    def _remplir_champs_(self, screen):
        screen.ids.image.source = ""
        screen.ids.phone_number.text = ""
        screen.ids.place_of_birth.text = ""
        screen.ids.motif.text = ""
        screen.ids.date.text = ""
        screen.ids.arrival_time.text = ""
        screen.ids.exit_time.text = ""
        screen.ids.observation.text = ""

        screen.ids.btn_delete.disabled = True
        screen.ids.btn_share.disabled = True
        return self.masquer_bouttons(screen)

    def masquer_bouttons(self, screen):
        screen.ids.btn_save.disabled = True
        screen.ids.btn_cancel.disabled = True
        return

    def renitialiser_filtre(self):
        screen = self.root.get_screen("screen A")
        # Vide les champs de filtre
        screen.ids.year_filter.text = ""
        screen.ids.month_filter.text = ""
        screen.ids.day_filter.text = ""
        # Affiche tous les visiteurs
        self.afficher_heros_visiteurs()
    
    def reset_password(self):
        screen = self.root.get_screen("new_password")
        new_password_first = screen.ids.new_password_first.text.rstrip()
        new_password_second = screen.ids.new_password_second.text.rstrip()

        if not all([new_password_second, new_password_first]):
            self.show_error_dialog("Veuillez remplir les deux champs avec un nouveau mot de passe.")

        if new_password_second != new_password_first:
            self.show_error_dialog("Les deux mots de passes doivent être identiques.")
            return

        if len(new_password_first) < 8:
            self.show_error_dialog("La longueur minimale du mot de passe est de 8 caractères.")
            return

        try:
            self.reset_fields_modify_pw(new_password_first, screen)
        except ValueError as e:
            self.show_error_dialog("Une erreur s'est produite lors changement du mot de passe, veillez réessayer.")
            logger.error(f"L'erreur suivante vient de se produire {e}")

    def reset_fields_modify_pw(self, new_password_first, screen):
        self.user_manager.reset_password_with_token(self.token, new_password_first)
        self.show_info_snackbar("Mot de passe rénitialisé avec succès!")

        screen.ids.new_password_first.text = ""
        screen.ids.new_password_second.text = ""
        self.root.get_screen("reset").ids.reset_email.text = ""

        self.root.current = "login"
           
    def restart_app(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)
            
    def signup(self, last_name, first_name, email, password_first, role):
        try:
            self.user_manager.add_user(last_name, first_name, email, password_first, "GN-Rabat", role)
            
            self.user = self.user_manager.authenticate_user(email, password_first)
            self.root.current = "screen A"
            
            self.show_info_snackbar("Compte crée avec succès.", str(self.user))
        except ValueError as e:
            self.show_error_dialog("Une erreur s'est produite lors de la création du compte, veuillez réessayer.")
            logger.error(f"L'erreur suivante vient de se produire {e}")
            
    def send_reset_code(self):
        email = self.root.get_screen("reset").ids.reset_email.text
        
        try:
            self.token = self.user_manager.generate_reset_token(email)
            self.root.current = "code_input"
        except ValueError as e:
            self.show_error_dialog("Une erreur s'est produite lors de l'envoie du code, veuillez réessayer.")
            logger.error(f"L'erreur suivante vient de se produire {e}")
            self.root.get_screen("reset").ids.reset_email.text = ""
        
    def set_item(self, item, field_name):
        """Met à jour le champ de date avec l'item sélectionné."""
        self.get_field(field_name).text = item
        self.menu.dismiss()
            
    def set_text(self, text, name):
        screen_ids = self.root.get_screen("screen B").ids
        if name == "id":
            screen_ids.id_type.text = text
        elif name == "motif":
            screen_ids.motif.text = text
        
        self.menu.dismiss()
        self.activer_boutons_modification()

    def select_file(self, selection):
        if not selection:
            return

        for path in selection:
            if not path.lower().endswith(('.pdf', '.txt', '.doc', '.docx', '.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.show_error_dialog(f"Fichier invalide: {path}")
                continue


        if self.file_manager_mode == "document":
            self.file_manager_mode = None
            self.selected_document_path = selection[0]
            self.send_document()

        elif self.file_manager_mode == "image":
            self.set_img_path(selection)
            
    def set_img_path(self, selection):
        self.file_manager_mode = None
        self.activer_boutons_modification()

        path1 = Path(selection[0])
        img1 = Image.open(path1)

        if len(selection) > 1:
            self.concatene_save_image(selection, img1, path1)
        else:
            self.selected_image_path = str(path1)

        self.root.get_screen("screen B").ids.image.source = self.selected_image_path

    def concatene_save_image(self, selection, img1, path1):
        path2 = Path(selection[1])
        img2 = Image.open(path2)

        # Fusion verticale (empilement)
        new_img = Image.new("RGB", (max(img1.width, img2.width), img1.height + img2.height))
        new_img.paste(img1, (0, 0))
        new_img.paste(img2, (0, img1.height))

        image_dir = os.path.join(os.path.expanduser("~"), "Documents", "GestionVisiteur", "ID")
        os.makedirs(image_dir, exist_ok=True)
        self.selected_image_path = os.path.join(image_dir, f"fusion_de_{path1.stem}_et_{path2.stem}.jpg")
        new_img.save(self.selected_image_path)
    
    def send_document(self):
        if not self.selected_document_path:
            self.show_error_dialog("Aucun document sélectionné.")
            return

        caption = "Veuillez trouver le document ci-joint."
        receiver = self.demander_numero()

        try:
            self.send_document_whatsapp(receiver, caption)
        except Exception as e:
            logger.error(f"Une erreur s'est produite {e}")
            self.show_error_dialog("Désolé il faut être connecté à internet pour pouvoir faire ce partage. \nVérifiez l'état de votre connexion")
            return

        self.selected_document_path = ""

    def send_document_whatsapp(self, receiver, caption):
        from selenium import webdriver

        # Démarrer Chrome (assure-toi que le profil garde ta session WhatsApp)
        options = Options()
        options.add_experimental_option("detach", True)

        # Chemin vers Documents/GestionVisiteur/whatsapp_profile
        user_data_dir = os.path.join(os.path.expanduser("~"), "Documents", "GestionVisiteur", "whatsapp_profile")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        # Utiliser un profil utilisateur persistant
        options.add_argument(f"user-data-dir={user_data_dir}")

        driver = webdriver.Edge(options=options)
        driver.get(f"https://web.whatsapp.com/send?phone={receiver}")


        # Attendre que la page soit prête (QR scanné / session ouverte)
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
        )

        # Ouvre la conversation (soit via URL, soit en cherchant le contact)
        # Option A: si tu as déjà ouvert le chat ailleurs, saute cette étape.
        # Option B: naviguer vers une conversation existante par URL:
        # driver.get(receiver_url_or_selector)

        # Cliquer sur le bouton « trombone »
        attach_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='plus-rounded']"))
        )
        attach_button.click()

        self.find_input_file(driver, "div[aria-label^='Entrez du texte']", caption)
        self.find_input_file(driver, "input[type='file']", self.selected_document_path)
        # Envoyer
        send_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='wds-ic-send-filled']"))
        )
        time.sleep(1)
        send_button.click()
    
    def find_input_file(self, driver, arg1, arg2):
        # Trouver l'input file pour les documents
        # WhatsApp ouvre un menu; l’élément input file pour documents a souvent:
        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, arg1))
        )
        file_input.send_keys(arg2)

        # Ajouter une légende si besoin
        time.sleep(1)
        
    def share_document(self, from_user_id, to_user_id, document_path):
        document_type = os.path.splitext(document_path)[1][1:]
        doc = self.document_manager.share_document(from_user_id, to_user_id, document_path, document_type)
        self.show_info_snackbar("Document partagé avec succès!", str(doc.id))
        
        self.dialog.dismiss()
    
    def share_visitor(self, visiteur, from_user_id, to_user_id):
        def _share(instance):
            try:
                share_id = self.visitor_manager.share_visitor(visiteur, from_user_id, to_user_id)
                self.show_info_snackbar("Visiteur partagé avec succès!", str(share_id))
                
                self.dialog.dismiss()
            except ValueError as e:
                self.show_error_dialog("Une erreur s'est produite lors du partage du visiteur, veuillez réessayer.")
                logger.error(f"L'erreur suivante vient de se produire {e}")
        return _share
    
    def show_error_dialog(self, message):
        error_dialog = MDDialog(
            MDDialogHeadlineText(text="Erreur"),
            MDDialogContentContainer(MDBoxLayout(
                MDLabel(text=message),
                orientation="vertical",
                adaptive_height=True
            )),
        )
        error_dialog.open()
    
    def show_info_snackbar(self, message, id=""):
        logger.info(message + id)
        
        MDSnackbar(
            MDSnackbarText(
            text=message),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
            duration=2,
            background_color="green"
        ).open()
  
    def show_visitor_details(self, visiteur=None):
        self.visiteur = visiteur
        self.remplir_champs()
        
        self.root.current = "screen B"
        self.root.transition = SlideTransition(direction="left")
    
    def toggle_password_visibility(self, btn, text_field):
        text_field.password = btn.icon != "eye"
        btn.icon = "eye-off" if btn.icon == "eye" else "eye"
        
    def update_notification_badge(self):
        """Récupère et affiche le nombre de partages reçus."""
        shares = self.visitor_manager.get_active_shares_for_user(self.user.id)
        self.root.get_screen("screen A").ids.ntf_badge.text = str(len(shares)) if shares else ""
    
    def update_document_badge(self):
        """Récupère et affiche le nombre de documents partagés reçus."""
        documents = self.document_manager.get_shares_for_user(self.user.id)
        self.root.get_screen("screen A").ids.doc_badge.text = str(len(documents)) if documents else ""
        
    def valider_champs(self, phone_number, place_of_birth, motif):
        if not all([phone_number, place_of_birth, motif]):
            return "Tous les champs sont obligatoires."
        if not phone_number.isdigit() or len(phone_number) < 10:
            return "Numéro de téléphone invalide."
        return None
    
try:      
    Gestion().run()
except Exception as e:
    logger.error(f"Une erreur s'est produite {e}")