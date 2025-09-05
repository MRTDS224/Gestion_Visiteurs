from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty

from kivymd.app import MDApp
from kivymd.uix.hero import MDHeroFrom
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogButtonContainer, MDDialogContentContainer
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import SlideTransition
from managers.visitor_manager import VisitorManager
from managers.user_manager import UserManager
import os
from datetime import datetime, date, timezone, timedelta
import webbrowser
import urllib.parse


class HeroItem(MDHeroFrom):
    visiteur = ObjectProperty()
    manager = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.image.ripple_duration_in_fast = 0.05

    def on_transform_in(self, instance_hero_widget, duration):
        for instance in [
            instance_hero_widget,
            instance_hero_widget._overlay_container,
            instance_hero_widget._image,
        ]:
            Animation(radius=[0, 0, 0, 0], duration=duration).start(instance)

    def on_transform_out(self, instance_hero_widget, duration):
        for instance, radius in {
            instance_hero_widget: [dp(24), dp(24), dp(24), dp(24)],
            instance_hero_widget._overlay_container: [0, 0, dp(24), dp(24)],
            instance_hero_widget._image: [dp(24), dp(24), dp(24), dp(24)],
        }.items():
            Animation(
                radius=radius,
                duration=duration,
            ).start(instance)

    def on_release(self):
        def switch_screen(*args):
            MDApp.get_running_app().visiteur = self.visiteur
            
            self.manager.current_heroes = [self.tag]
            self.manager.ids.hero_to.tag = self.tag
            self.manager.current = "screen B"
            
            MDApp.get_running_app().remplir_champs()

        Clock.schedule_once(switch_screen, 0.2)


class Gestion(MDApp):
    visiteur = ObjectProperty()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.visitor_manager = VisitorManager()
        self.icon = "pictures/logo1.jpg"
        self.title = "G-Entry"
        self.user_manager = UserManager()
        self.dialog = None
        self.data_table = None
        self.menu = None
        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_file,
        )
        self.file_manager_mode = None
        self.selected_image_path = ""
        self.menu = MDDropdownMenu(
            position="bottom",
            width=dp(400),
        )
        
    def activer_boutons_modification(self):
        self.root.ids.btn_cancel.disabled = False
        self.root.ids.btn_save.disabled = False
    
    def afficher_heros_visiteurs(self, visiteurs=None):
        box = self.root.ids.box
        box.clear_widgets()
        
        if visiteurs is None:
            visiteurs = self.visitor_manager.lister_visiteurs()
        
        if not visiteurs:
            return
            
        for visiteur in visiteurs:
            hero_item = HeroItem(
                visiteur=visiteur,
                tag=f"{visiteur.id}",
                manager=self.root
            )
            hero_item.md_bg_color = "lightgrey"
            box.add_widget(hero_item)
            
    def animer_bouton(self, bouton):
        anim = Animation(opacity=0.5, duration=0.1) + Animation(opacity=1, duration=0.1)
        anim.start(bouton)
        
    def annuler_modifications(self):
        self.remplir_champs()
        
        self.root.ids.btn_save.disabled = True
        self.root.ids.btn_cancel.disabled = True
        
    def build(self):
        return Builder.load_file("main.kv")

    def build_form_content(self, contents=None):
        self.image_button = self.creer_bouton(
            "Sélectionner une image",
            style="elevated",
            icone="image",
            on_release=lambda x: self.open_filechooser(),
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
        
    def create_text_field(self, hint, required=True):
        return MDTextField(
            MDTextFieldHintText(text=hint),
            required=required,
            mode="outlined",
            size_hint_x=None,
            width="300dp",
        )
        
    def creer_bouton(self, texte, style="text", icone=None, on_release=None):
        """Crée un bouton MDButton avec texte, style, icône et callback."""
        elements = []
        if icone:
            elements.append(MDButtonIcon(icon=icone))
        elements.append(MDButtonText(text=texte))
        kwargs = {"style": style}

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
        dialog.open()
        return dialog
    
    def enregistrer_modifications(self):
        try:
            image = self.selected_image_path if self.selected_image_path else self.visiteur.image_path
            nom = self.root.ids.nom.text
            prenom = self.root.ids.prenom.text
            phone_number = self.root.ids.phone_number.text
            id_type = self.root.ids.id_type.text
            id_number = self.root.ids.id_number.text
            motif = self.root.ids.motif.text
            date = self.root.ids.date.text
            arrival_time = self.root.ids.arrival_time.text
            exit_time = self.root.ids.exit_time.text
            observation = self.root.ids.observation.text

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
            
            self.root.ids.btn_save.disabled = True
            self.root.ids.btn_cancel.disabled = True
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
            self.afficher_table_visiteurs()
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
        if "day" in field_name:
            return self.root.ids.day_filter
        elif "month" in field_name:
            return self.root.ids.month_filter
        elif "year" in field_name:
            return self.root.ids.year_filter
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
    
    def login(self, email, password):
        self.user, error = self.user_manager.authenticate_user(email, password)
        
        if error:
            self.show_error_dialog(error)
            return
        
        self.show_info_snackbar("Connexion réussie!")
        self.root.current = "accueil" if self.user.role == "Huissier" else "historique"
         
    def on_select_all_visitors(self, is_active):
        screen = self.root.get_screen(self.root.current)
        if screen.name == "accueil":
            table = screen.ids.table_visiteurs
        elif screen.name == "historique":
            table = screen.ids.historique_table
            
        for row in table.data:
            if is_active:
                if row.get("selected") != is_active:
                    self.selected_visitors.clear()
                    screen.ids.select_all_checkbox.active = False
                    return
                
                self.selected_visitors.add(row.get("visitor_id"))
        
        screen.partager_visible = bool(self.selected_visitors)
        
    def on_select_visitor(self, visitor_row, is_active):
        # Détermine la table selon l'écran courant
        screen = self.root.get_screen(self.root.current)
        if screen.name == "accueil":
            table = screen.ids.table_visiteurs
        elif screen.name == "historique":
            table = screen.ids.historique_table
        else:
            return

        # Mets à jour la propriété 'selected' de la ligne
        visitor_row.selected = is_active
        # Mets aussi à jour dans la data de la table
        for row in table.data:
            if row.get("visitor_id") == visitor_row.visitor_id:
                row["selected"] = is_active

        if is_active:
            if visitor_row.visitor_id not in self.selected_visitors:
                self.selected_visitors.add(visitor_row.visitor_id)
        else:
            if visitor_row.visitor_id in self.selected_visitors:
                self.selected_visitors.discard(visitor_row.visitor_id)
        
        screen.partager_visible = bool(self.selected_visitors)
        
    def on_start(self):
        visiteurs = self.visitor_manager.lister_visiteurs()
        for visiteur in visiteurs:
            hero_item = HeroItem(
                visiteur=visiteur, 
                tag=f"{visiteur.id}", 
                manager=self.root
            )
            hero_item.md_bg_color = "lightgrey"
            self.root.ids.box.add_widget(hero_item)

    def open_filechooser(self):
        self.file_manager_mode = "image"
        self.file_manager.show("C:/Users/mrtds/Pictures")  # Mets le chemin de départ adapté à ton OS
    
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
        
        content = MDBoxLayout(orientation="horizontal", spacing=20, padding=10, adaptive_height=True)
        content.add_widget(email_button)
        content.add_widget(whatsapp_button)
        
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
        self.root.ids.nom.text = self.visiteur.nom
        self.root.ids.prenom.text = self.visiteur.prenom
        self.root.ids.phone_number.text = self.visiteur.phone_number
        self.root.ids.id_type.text = self.visiteur.id_type
        self.root.ids.id_number.text = self.visiteur.id_number
        self.root.ids.motif.text = self.visiteur.motif
        self.root.ids.date.text = self.visiteur.date
        self.root.ids.arrival_time.text = self.visiteur.arrival_time
        self.root.ids.exit_time.text = self.visiteur.exit_time
        self.root.ids.observation.text = self.visiteur.observation
            
        self.root.ids.btn_save.disabled = True
        self.root.ids.btn_cancel.disabled = True

    def renitialiser_filtre(self):
        # Vide les champs de filtre
        self.root.ids.year_filter.text = ""
        self.root.ids.month_filter.text = ""
        self.root.ids.day_filter.text = ""
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
            
            self.root.current = "login"
        except ValueError as e:
            self.show_error_dialog(str(e))
            self.root.current = "reset"
            
    def signup(self, last_name, first_name, email, password_first, role):
        try:
            self.user = self.user_manager.add_user(last_name, first_name, email, password_first, "GN-Rabat", role)
            self.show_info_snackbar("Connexion réussie.")
            self.root.current = "acceuil" if self.user.role == "Huissier" else "historique"
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
        self.file_manager.close()
        if self.file_manager_mode == "export":
            chemin = os.path.join(path, "visiteurs_export.json") if os.path.isdir(path) else path
            self.visitor_manager.exporter_visiteurs(chemin)
            self.show_error_dialog(f"Export terminé !\nFichier : {chemin}")
        elif self.file_manager_mode == "import":
            self.visitor_manager.importer_visiteurs(path)
            self.afficher_table_visiteurs()
            self.show_error_dialog("Import terminé !")
        elif self.file_manager_mode == "image":
            if not path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.show_error_dialog("Veuillez sélectionner un fichier image valide.")
                return
            self.selected_image_path = path
            if hasattr(self, "image_button"):
                self.image_button.children[0].text = os.path.basename(path)
            self.file_manager_mode = None
            
            self.activer_boutons_modification()
    
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
    
    def valider_champs(self, nom, prenom, phone_number, id_type, id_number, motif):
        if not all([nom, prenom, phone_number, id_type, id_number, motif]):
            return "Tous les champs sont obligatoires."
        if not phone_number.isdigit() or len(phone_number) < 10:
            return "Numéro de téléphone invalide."
        return None
      
    def valider_sortie(self, visitor_row, dialog):
        exit_time = self.exit_time_field.text
        observation = self.observation_field.text
        # Mets à jour la base de données via VisitorManager
        success, error = self.visitor_manager.mettre_a_jour_visiteur(
            int(visitor_row.visitor_id),
            exit_time=exit_time,
            observation=observation
        )
        if not success:
            self.show_error_dialog(error or "Erreur lors de la mise à jour du visiteur.")
            return
        dialog.dismiss()
        self.afficher_table_visiteurs()
        
Gestion().run()