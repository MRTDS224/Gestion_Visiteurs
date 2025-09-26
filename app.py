from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty

from kivymd.app import MDApp
from kivymd.uix.hero import MDHeroFrom
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogButtonContainer, MDDialogContentContainer
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon, MDIconButton
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText, MDTextFieldLeadingIcon
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.fitimage import FitImage
from kivymd.uix.card import MDCard
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import MDList, MDListItem, MDListItemLeadingIcon, MDListItemHeadlineText, MDListItemSupportingText, MDListItemTertiaryText, MDListItemTrailingIcon
from kivy.uix.screenmanager import SlideTransition
from managers.visitor_manager import VisitorManager
from managers.user_manager import UserManager
from managers.document_manager import DocumentManager
import os
import sys
from datetime import datetime, date, timezone, timedelta
import webbrowser
import tempfile
import urllib.parse

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
            app.show_error_dialog(f"Erreur lors de l'acceptation du partage : {e}")
            return
        
        self.menu.dismiss()
        self.dialog.dismiss()
        app.show_info_snackbar("Partage accepté. visiteur ajouté à votre liste.")
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
        
        app = MDApp.get_running_app()
        user_id = app.user.id
        shares = app.visitor_manager.get_shares_for_user(user_id)
        
        # Trier par shared_at ascendant
        shares_sorted = sorted(shares, key=lambda s: s.shared_at)
        content = MDList(spacing=10)
        for share in shares_sorted:
            content.add_widget(
                format_share(share)
            )

        # Construire et ouvrir le MDDialog
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Notifications de partage", halign="left", valign="top"),
            MDDialogContentContainer(content),
            adaptive_height=True,
            auto_dismiss=True,
            md_bg_color="white"
        )
        self.dialog.open()
    
    def refuse_share(self, share_id):
        """Refuse un partage de visiteur."""
        app = MDApp.get_running_app()
        try:
            response = app.visitor_manager.revoke_share(share_id)
            print(response)
            if not response:
                app.show_error_dialog("Le partage est déjà révoqué ou n'existe pas.")
                return
        except Exception as e:
            app.show_error_dialog(f"Erreur lors du refus du partage : {e}")
            return
        
        self.menu.dismiss()
        
        app.show_info_snackbar("Partage refusé.")
        
class DetailScreen(MDScreen):
    pass
   
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
        self.ids.account_password_first.text = ""
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
                return self.show_error_dialog("Les mots de passe doivent être identiques.")
            if len(pwd1) < 8:
                return self.show_error_dialog("Le mot de passe doit faire au moins 8 caractères.")
        
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
            return self.show_info_snackbar("Aucune modification détectée.")

        # Appel au UserManager (décompactage des kwargs)
        try:
            app.user_manager.update_user(user.id, **params)
            app.user = app.user_manager.get_user_by_email(email)
            app.show_info_snackbar("Profil mis à jour avec succès.")
            # On recharge l’affichage et on désactive à nouveau
            self.populate_fields()
        except ValueError as e:
            app.show_error_dialog(str(e))
    
    def annuler_modification_utilisateur(self):
        self.populate_fields()

    def on_leave(self, *args):
        self.ids.account_last_name.text = ""
        self.ids.account_first_name.text = ""
        self.ids.account_email.text = ""
        self.ids.account_password_first.text = ""
        self.ids.account_password_second.text = ""
        self.ids.account_role.text = ""

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

class ResetPasswordScreen(MDScreen):
    pass

class CodeInputScreen(MDScreen):
    pass

class NewPasswordScreen(MDScreen):
    pass
   
class Gestion(MDApp):
    visiteur = ObjectProperty()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.visitor_manager = VisitorManager()
        self.user_manager = UserManager()
        self.document_manager = DocumentManager()
        self.icon = "pictures/logo1.jpg"
        self.title = "G-Entry"
        self.dialog = None
        self.menu = None
        self.user = None
        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_file,
        )
        self.file_manager_mode = None
        self.selected_document_path = ""
        self.selected_image_path = ""
        self.menu = MDDropdownMenu(
            position="bottom",
            width=dp(400),
        )
        
    def activer_boutons_modification(self):
        screen = self.root.get_screen("screen B")
        screen.ids.btn_cancel.disabled = False
        screen.ids.btn_save.disabled = False
    
    def afficher_heros_visiteurs(self, visiteurs=None):
        box = self.root.get_screen("screen A").ids.box
        box.clear_widgets()
        
        if visiteurs is None:
            visiteurs = self.visitor_manager.lister_visiteurs()
        
        if not visiteurs:
            return
            
        for visiteur in visiteurs:
            layout = MDCard(
                orientation="vertical",
                padding=10,
                size_hint_y=None,
                height=dp(250),
                on_release=lambda x, v=visiteur: self.show_visitor_details(v)
            )
            layout.add_widget(FitImage(
                source=visiteur.image_path,
                size_hint_y=None,
                height=dp(200)
            ))
            layout.add_widget(MDLabel(
                text=f"{visiteur.nom} {visiteur.prenom}",
                halign="left",
                size_hint_y=None,
                font_size='12sp',
                height=dp(30),
            ))
            box.add_widget(layout)
        
        if self.user is not None:
            self.update_notification_badge()    
            
    def animer_bouton(self, bouton):
        anim = Animation(opacity=0.5, duration=0.1) + Animation(opacity=1, duration=0.1)
        anim.start(bouton)
        
    def annuler_modifications(self):
        self.remplir_champs()
        
        screen = self.root.get_screen("screen B")
        screen.ids.btn_save.disabled = True
        screen.ids.btn_cancel.disabled = True
        
    def build(self):
        return Builder.load_file("main.kv")

    def build_form_content(self, contents=None):
        self.image_button = self.creer_bouton(
            "Sélectionner une image",
            style="elevated",
            icone="image",
            on_release=lambda x: self.open_image_filechooser(),
        )
        self.nom_field = self.create_text_field("Entrez le nom")
        self.prenom_field = self.create_text_field("Entrez le prénom")
        self.phone_field = self.create_text_field("Entrez le numéro de téléphone")
        self.id_type_field = self.create_text_field("Entrez le type de la pièce d'identité")
        self.id_number_field = self.create_text_field("Entrez le numéro de la pièce d'identité")
        self.motif_field = self.create_text_field("Entrez le motif de la visite")

        self.id_type_field.bind(
            focus=lambda instance, value: self.open_menu("id") if value else None
        )
        self.motif_field.bind(
            focus=lambda instance, value: self.open_menu("motif") if value else None
        )

        # Limite la hauteur du formulaire et ajoute un scroll si besoin
        form_layout = MDBoxLayout(
            orientation="vertical",
            spacing=20,
            padding=10,
            adaptive_height=True,
            size_hint_y=None
        )
        for field in [
            self.image_button,
            self.nom_field, self.prenom_field, self.phone_field,
            self.id_type_field, self.id_number_field, self.motif_field
        ]:
            form_layout.add_widget(field)
        
        if contents:
            for content in contents:
                form_layout.add_widget(content)
        
        form_layout.height = sum([field.height for field in form_layout.children])

        scroll = ScrollView(
            size_hint=(1, None),
            height=(min(600, self.root_window.height * 0.8)),  # Limite la hauteur max à 80% de l'écran
            do_scroll_x=False
        )
        scroll.add_widget(form_layout)
        return scroll
    
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
        dialog.add_widget(
            MDDialogButtonContainer(
                *actions,
                spacing="10dp"
            )
        )
        dialog.auto_dismiss = False
        
        if titre == "Connexion":
            self.root.opacity = 0.1
            dialog.bind(on_dismiss=lambda *args: setattr(self.root, 'opacity', 1))

            
        dialog.open()
        return dialog
    
    def delete_visitor(self):
        succes, error = self.visitor_manager.supprimer_visiteur(self.visiteur.id)
        if error:
            self.show_error_dialog(error)
            return
        self.show_info_snackbar("Visiteur supprimé avec succès.")
        self.root.current = "screen A"
        self.afficher_heros_visiteurs()
        
    def enregistrer_modifications(self):
        try:
            screen = self.root.get_screen("screen B")
            
            image = self.selected_image_path if self.selected_image_path else self.visiteur.image_path
            nom = screen.ids.nom.text
            prenom = screen.ids.prenom.text
            phone_number = screen.ids.phone_number.text
            id_type = screen.ids.id_type.text
            id_number = screen.ids.id_number.text
            motif = screen.ids.motif.text
            date = screen.ids.date.text
            arrival_time = screen.ids.arrival_time.text
            exit_time = screen.ids.exit_time.text
            observation = screen.ids.observation.text

            if not all([nom, prenom, phone_number, id_type, id_number, motif, date, arrival_time, exit_time, observation]):
                self.show_error_dialog("Tous les champs sont obligatoires.")
                return

            success, error = self.visitor_manager.mettre_a_jour_visiteur(
                self.visiteur.id, image_path=image, nom=nom, prenom=prenom,
                phone_number=phone_number, id_type=id_type,
                id_number=id_number, motif=motif,
                date=date, arrival_time=arrival_time,
                exit_time=exit_time, observation=observation
            )
            
            if not success:
                self.show_error_dialog(error or "Erreur lors de la mise à jour du visiteur.")
                return
            
            screen.ids.btn_save.disabled = True
            screen.ids.btn_cancel.disabled = True
            self.show_info_snackbar("Modifications enregistrées avec succès!")
            
            # Rafraîchir l'affichage
            self.visiteur = self.visitor_manager.chercher_visiteur(self.visiteur.id)
            self.remplir_champs()
            self.afficher_heros_visiteurs()

        except Exception as e:
            self.show_error_dialog(f"Erreur lors de la modification : {e}")
            
    def enregistrer_visiteur(self):
        try:
            image = self.selected_image_path
            nom = self.nom_field.text
            prenom = self.prenom_field.text
            phone_number = self.phone_field.text
            id_type = self.id_type_field.text
            id_number = self.id_number_field.text
            motif = self.motif_field.text

            if not all([nom, prenom, phone_number, id_type, id_number, motif]):
                self.show_error_dialog("Tous les champs sont obligatoires.")
                return

            erreur = self.valider_champs(nom, prenom, phone_number, id_type, id_number, motif)
            if erreur:
                self.show_error_dialog(erreur)
                return

            self.visitor_manager.ajouter_visiteur(image, nom, prenom, phone_number, id_type, id_number, motif)
            self.dialog.dismiss()
            self.afficher_heros_visiteurs()            
            self.show_info_snackbar("Visiteur ajouté avec succès!")

        except Exception as e:
            self.show_error_dialog(f"Erreur lors de l'ajout : {e}")
    
    def envoyer_par_mail(self, *args):
        if not self.visiteur:
            self.show_error_dialog("Aucun visiteur sélectionné.")
            return

        sujet = "Liste des visiteurs sélectionnés"
        corps = self.generer_message_visiteurs(self.visiteur)
        mailto_link = f"mailto:?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps)}"
        webbrowser.open(mailto_link)
        self.dialog.dismiss()

    def envoyer_par_whatsapp(self, *args):
        if not self.visiteur:
            self.show_error_dialog("Aucun visiteur sélectionné.")
            return

        message = self.generer_message_visiteurs(self.visiteur)
        whatsapp_link = f"https://wa.me/?text={urllib.parse.quote(message)}"
        webbrowser.open(whatsapp_link)
        self.dialog.dismiss()
    
    def exit_file_manager(self, *args):
        self.file_manager.close()
    
    def filtrer(self, year, month, day):
        visiteurs = self.visitor_manager.lister_visiteurs()
        result = []
        for v in visiteurs:
            try:
                d = datetime.strptime(v.date, "%Y-%m-%d")
            except Exception:
                continue
            if year and str(d.year) != year:
                continue
            if month and str(d.month).zfill(2) != month.zfill(2):
                continue
            if day and str(d.day).zfill(2) != day.zfill(2):
                continue
            result.append(v)
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

    def generer_message_visiteurs(self, visiteur):
        lignes = ["Bonjour, je vous partage ce visiteur :\n"]
        lignes.append(
            f"Nom : {visiteur.nom}\n"
            f"Prénom : {visiteur.prenom}\n"
            f"Téléphone : {visiteur.phone_number}\n"
            f"Pièce d'identité : {visiteur.id_type} - {visiteur.id_number}\n"
            f"Motif : {visiteur.motif}\n"
            f"Date : {visiteur.date}\n"
            f"Heure d'arrivée : {visiteur.arrival_time}\n"
            f"Heure de sortie : {visiteur.exit_time or 'Non renseignée'}\n"
            f"Observation : {visiteur.observation or 'Aucune'}\n"
        )
        return "\n".join(lignes)
    
    def go_to_screen(self, screen_name):
        self.root.current = screen_name
        self.dialog.dismiss()
        
    def login(self, email, password):
        if not email or not password:
            self.show_error_dialog("Tous les champs sont obligatoires.")
            return
        
        self.user, error = self.user_manager.authenticate_user(email, password)
        
        if error:
            self.show_error_dialog(error)
            return
        
        self.update_notification_badge()
        self.show_info_snackbar("Connexion réussie!")
        self.dialog.dismiss()
             
    def on_start(self):
        self.afficher_heros_visiteurs()
        self.ouvrir_dialogue_login()

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
            content =  MDListItem(
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
            open_icon = MDIconButton(
                    icon="eye-outline",
                    on_release=lambda x, d=doc:self.open_document(d)
                )
            content.add_widget(open_icon)
            return content
        
        content = MDList(spacing=10)
        for doc in documents:
            content.add_widget(
                format_document(doc)
            )

        # Construire et ouvrir le MDDialog
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Documents partagés avec vous", halign="left", valign="top"),
            MDDialogContentContainer(content),
            adaptive_height=True,
            auto_dismiss=True,
            md_bg_color="white"
        )
        self.dialog.open()
        
    def open_document_filechooser(self):
        self.file_manager_mode = "document"
        self.file_manager.show("C:/Users/mrtds/Documents")

    def open_image_filechooser(self):
        self.file_manager_mode = "image"
        self.file_manager.show("C:/Users/mrtds/Pictures")
    
    def open_menu(self, field_name):
        if field_name == "id":
            items = [
                {"text": "Passeport", "on_release": lambda x="Passeport": self.set_text(x, "id")},
                {"text": "Carte", "on_release": lambda x="Carte": self.set_text(x, "id")},
            ]
            
            self.menu.caller=self.id_type_field
            self.menu.items=items
            self.menu.position="top"
            self.menu.open()
            
        elif field_name == "motif":
            items = [
                {"text": "Consulat", "on_release": lambda x="Consulat": self.set_text(x, "motif")},
                {"text": "Attestation de couverture", "on_release": lambda x="Attestation de couverture": self.set_text(x, "motif")},
                {"text": "Demande de prise en charge", "on_release": lambda x="Demande de prise en charge": self.set_text(x, "motif")},
                {"text": "Légalisation", "on_release": lambda x="Légalisation": self.set_text(x, "motif")},
            ]
            self.menu.caller=self.motif_field
            self.menu.items=items
            self.menu.position="top"
            self.menu.open()
            
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
            
    def ouvrir_dialogue_ajout_visiteur(self):
        self.selected_image_path = ""
        content = self.build_form_content()
        actions = [
            Widget(),
            self.creer_bouton(
                "Annuler",
                style="text",
                on_release=lambda x: self.dialog.dismiss()
            ),
            self.creer_bouton(
                "Enregistrer",
                style="elevated",
                on_release=lambda x: self.enregistrer_visiteur()
            ),
        ]
        self.dialog = self.creer_dialogue("Ajouter un visiteur", content, actions)
    
    def ouvrir_dialogue_choix_destinataire_document(self):
        content = MDBoxLayout(orientation="vertical", spacing=10, adaptive_height=True)
        for user in self.user_manager.list_users():
            if user.id != self.user.id:
                btn = self.creer_bouton(
                    f"Partager avec {user.prenom} {user.nom}",
                    style="outlined",
                    icone="account",
                    on_release=lambda x, uid=user.id: self.share_document(self.user.id, uid, self.selected_document_path)
                )
                content.add_widget(btn)
        actions = [self.creer_bouton("Annuler", style="text", on_release=lambda x: self.dialog.dismiss())]
        self.dialog = self.creer_dialogue("Choisir le destinataire", content, actions)
  
    def ouvrir_dialogue_login(self):
        content = MDBoxLayout(
            orientation="vertical",
            spacing=20,
            padding=10,
            adaptive_height=True,
            
        )
        email_field = self.create_text_field("Entrez votre email", icon="email")
        email_field.required = True
        email_field.pos_hint = {"center_x": 0.5}
        password_field = self.create_text_field("Entrez votre mot de passe", icon="lock")
        password_field.password = True
        password_field.required = True
        password_field.pos_hint = {"center_x": 0.5}
        
        button_reset = self.creer_bouton(
            "Mot de passe oublié?",
            on_release=lambda x: self.go_to_screen("reset")
        )
        button_reset.pos_hint = {"center_x": 0.5}
        
        button_forgot = self.creer_bouton(
            "Créer un compte",
            on_release=lambda x: self.go_to_screen("signup")
        )
        button_forgot.pos_hint = {"center_x": 0.5}
        
        content.add_widget(email_field)
        content.add_widget(password_field)
        content.add_widget(button_reset)
        content.add_widget(button_forgot)
        
        actions = [
            Widget(),
            self.creer_bouton(
                "Se connecter",
                style="elevated",
                on_release=lambda x: self.login(email_field.text, password_field.text)
            ),
            Widget()
        ]
        
        self.dialog = self.creer_dialogue("Connexion", content, actions)
            
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
            on_release=lambda x: self.envoyer_par_whatsapp()
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
        screen.ids.image.source = self.visiteur.image_path
        screen.ids.nom.text = self.visiteur.nom
        screen.ids.prenom.text = self.visiteur.prenom
        screen.ids.phone_number.text = self.visiteur.phone_number
        screen.ids.id_type.text = self.visiteur.id_type
        screen.ids.id_number.text = self.visiteur.id_number
        screen.ids.motif.text = self.visiteur.motif
        screen.ids.date.text = self.visiteur.date
        screen.ids.arrival_time.text = self.visiteur.arrival_time
        screen.ids.exit_time.text = self.visiteur.exit_time or ""
        screen.ids.observation.text = self.visiteur.observation or ""
            
        screen.ids.btn_save.disabled = True
        screen.ids.btn_cancel.disabled = True

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
            self.user_manager.reset_password_with_token(self.token, new_password_first)
            self.show_info_snackbar("Mot de passe rénitialisé avec succès!")
            
            screen.ids.new_password_first.text = ""
            screen.ids.new_password_second.text = ""
            self.root.get_screen("reset").ids.reset_email.text = ""
            
            self.root.current = "screen A"
            self.ouvrir_dialogue_login()
        except ValueError as e:
            self.show_error_dialog(str(e))
            self.root.current = "reset"
       
    def restart_app(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)
            
    def signup(self, last_name, first_name, email, password_first, role):
        try:
            self.user = self.user_manager.add_user(last_name, first_name, email, password_first, "GN-Rabat", role)
            self.show_info_snackbar("Connexion réussie.")
            self.update_notification_badge()
            self.root.current = "screen A"
        except ValueError as e:
            self.show_error_dialog(str(e))
            
    def send_reset_code(self):
        email = self.root.get_screen("reset").ids.reset_email.text
        
        try:
            self.token = self.user_manager.generate_reset_token(email)
            self.root.current = "code_input"
        except ValueError as e:
            self.show_error_dialog(str(e))
            self.root.get_screen("reset").ids.reset_email.text = ""
        
    def set_item(self, item, field_name):
        """Met à jour le champ de date avec l'item sélectionné."""
        self.get_field(field_name).text = item
        self.menu.dismiss()
            
    def set_text(self, text, name):
        if name == "id":
            self.id_type_field.text = text
        if name == "motif":
            self.motif_field.text = text
        
        self.menu.dismiss()
    
    def select_file(self, path):
        if self.file_manager_mode == "document":
            if not path.lower().endswith(('.pdf', '.txt', '.doc', '.docx')):
                self.show_error_dialog("Veuillez sélectionner un fichier PDF, TXT ou DOC valide.")
                return
            self.file_manager.close()
            self.selected_document_path = path
            self.file_manager_mode = None
            
            # Ouvre le dialogue pour choisir le destinataire
            self.ouvrir_dialogue_choix_destinataire_document()
            
        elif self.file_manager_mode == "image":
            if not path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.show_error_dialog("Veuillez sélectionner un fichier image valide.")
                return
            self.file_manager.close()
            self.selected_image_path = path
            if hasattr(self, "image_button"):
                self.image_button.children[0].text = os.path.basename(path)
            self.file_manager_mode = None
            
            self.activer_boutons_modification()
    
    def share_document(self, from_user_id, to_user_id, document_path):
        document_type = os.path.splitext(document_path)[1][1:]
        self.document_manager.share_document(from_user_id, to_user_id, document_path, document_type)
        self.show_info_snackbar("Document partagé avec succès!")
        self.dialog.dismiss()
    
    def share_visitor(self, visiteur, from_user_id, to_user_id):
        def _share(instance):
            try:
                self.visitor_manager.share_visitor(visiteur, from_user_id, to_user_id)
                self.show_info_snackbar("Visiteur partagé avec succès!")
                self.dialog.dismiss()
            except ValueError as e:
                self.show_error_dialog(str(e))
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
        
    def show_info_snackbar(self, message):
        MDSnackbar(
            MDSnackbarText(
            text=message),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
            duration=2,
            background_color="green"
        ).open()
  
    def show_visitor_details(self, visiteur):
        self.visiteur = visiteur
        self.remplir_champs()
        self.root.current = "screen B"
        self.root.transition = SlideTransition(direction="left")
    
    def update_notification_badge(self):
        """Récupère et affiche le nombre de partages reçus."""
        shares = self.visitor_manager.get_shares_for_user(self.user.id)
        self.root.get_screen("screen A").ids.badge.text = str(len(shares)) if shares else ""
        
    def valider_champs(self, nom, prenom, phone_number, id_type, id_number, motif):
        if not all([nom, prenom, phone_number, id_type, id_number, motif]):
            return "Tous les champs sont obligatoires."
        if not phone_number.isdigit() or len(phone_number) < 10:
            return "Numéro de téléphone invalide."
        return None
          
Gestion().run()