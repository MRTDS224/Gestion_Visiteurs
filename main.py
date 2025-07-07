from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogButtonContainer, MDDialogContentContainer
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import snackbar
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp
from managers.visitor_manager import VisitorManager
import os
from datetime import datetime, date, timezone, timedelta
import webbrowser
import urllib.parse
from kivy.uix.screenmanager import SlideTransition
from kivy.animation import Animation

class VisitorRow(MDBoxLayout):
    selected = BooleanProperty(False)
    visitor_id = StringProperty("")
    image_path = StringProperty("")
    nom = StringProperty("")
    prenom = StringProperty("")
    phone_number = StringProperty("")
    id_type = StringProperty("")
    id_number = StringProperty("")
    date = StringProperty("")
    arrival_time = StringProperty("")
    motif = StringProperty("")
    exit_time = StringProperty("")
    observation = StringProperty("")

class AccueilScreen(MDScreen):
    partager_visible = BooleanProperty(False)
    
    def scroll_table_up(self):
        table = self.ids.table_visiteurs
        table.scroll_y = min(1, table.scroll_y + 0.1)

    def scroll_table_down(self):
        table = self.ids.table_visiteurs
        table.scroll_y = max(0, table.scroll_y - 0.1)

class HistoriqueScreen(MDScreen):
    partager_visible = BooleanProperty(False)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        months = ["Janvier", "Février", "Mars", "Avril", "May", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        self.days_items = [
            {
                "text": f"{i}",
                "on_release": lambda x=f"{i}": self.set_item(x, "day_filter"),
            } for i in range(1, 32)]
        self.months_items = [
            {
                "text": months[i],
                "on_release": lambda x=str(i+1): self.set_item(x, "month_filter"),
            } for i in range(len(months))]
        self.years_items = [
            {
                "text": str(year),
                "on_release": lambda x=str(year): self.set_item(x, "year_filter"),
            } for year in range(2024, datetime.now(timezone.utc).year + 1)
        ]
        self.menu = MDDropdownMenu(
            position="bottom",
            width=dp(100),
        )
        
    def on_enter(self, *args):
        MDApp.get_running_app().afficher_historique()
        
    def open_menu(self, field_name):
        """Ouvre le menu pour sélectionner le jour, le mois ou l'année."""
        if "day" in field_name:
            items = self.days_items
        elif "month" in field_name:
            items = self.months_items
        elif "year" in field_name:
            items = self.years_items
        else:
            return
        
        self.menu.items = items
        self.menu.caller = self.get_field(field_name)
        self.menu.open()
    
    def set_item(self, item, field_name):
        """Met à jour le champ de date avec l'item sélectionné."""
        self.get_field(field_name).text = item
        self.menu.dismiss()
        
    def get_field(self, field_name):
        """Retourne le champ de date correspondant au nom."""
        if "day" in field_name:
            return self.ids.day_filter
        elif "month" in field_name:
            return self.ids.month_filter
        elif "year" in field_name:
            return self.ids.year_filter
        else:
            raise ValueError(f"Champ inconnu : {field_name}")

    def filtrer_historique(self, year=None, month=None, day=None):
        """Filtre l'historique en fonction de l'année, du mois et du jour."""
        if year and month and day:
            date_filter = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            self.reinitialiser_filtre(date_filter)
        elif year and month:
            date_filter = f"{year}-{month.zfill(2)}"
            self.reinitialiser_filtre(date_filter, "year-month")
        elif year:
            self.reinitialiser_filtre(year, "year")
        elif month:
            self.reinitialiser_filtre(month.zfill(2), "month")
        elif day:
            self.reinitialiser_filtre(day.zfill(2), "day")
        else:
            self.reinitialiser_filtre()

    def reinitialiser_filtre(self, date_filter=None, date_filter_type=""):
        self.ids.day_filter.text = ""
        self.ids.month_filter.text = ""
        self.ids.year_filter.text = ""
        MDApp.get_running_app().afficher_historique(date_filter, date_filter_type=date_filter_type)
class GestionVisiteursApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.icon = "pictures/logo1.jpg"
        self.title = "G-Entry"
        self.manager = VisitorManager()
        self.dialog = None
        self.data_table = None
        self.menu = None
        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_file,
        )
        self.file_manager_mode = None
        self.selected_image_path = ""
        self.selected_visitors = set()
    
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
    
    def open_filechooser(self):
        self.file_manager_mode = "image"
        self.file_manager.show("C:/Users/mrtds/Pictures")  # Mets le chemin de départ adapté à ton OS
    
    def exit_file_manager(self, *args):
        self.file_manager.close()
        
    def on_start(self):
        self.afficher_table_visiteurs()
    
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        self.root.transition = SlideTransition(duration=0.3)  # Animation douce
        return self.root
    
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
    
    def animer_bouton(self, bouton):
        anim = Animation(opacity=0.5, duration=0.1) + Animation(opacity=1, duration=0.1)
        anim.start(bouton)
    
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
    
    def set_text(self, text, name):
        if name == "id":
            self.id_type_field.text = text
        if name == "motif":
            self.motif_field.text = text
        
        self.menu.dismiss()
    
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
    
    def create_text_field(self, hint, required=True):
        return MDTextField(
            MDTextFieldHintText(text=hint),
            required=required,
            mode="outlined",
            size_hint_x=None,
            width="300dp",
        )
     
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
        
    def remplir_champs(self, visitor):
        self.selected_image_path = visitor.image_path
        self.image_button.children[0].text = os.path.basename(visitor.image_path) if visitor.image_path else "Sélectionner une image"
        self.nom_field.text = visitor.nom
        self.prenom_field.text = visitor.prenom
        self.phone_field.text = visitor.phone_number
        self.id_type_field.text = visitor.id_type
        self.id_number_field.text = visitor.id_number
        self.motif_field.text = visitor.motif
        if hasattr(self, 'exit_time_field'):
            self.exit_time_field.text = visitor.exit_time or ""
        if hasattr(self, 'observation_field'):
            self.observation_field.text = visitor.observation or ""
    
    def ouvrir_dialogue_modification(self, visitor_row):
        self.visitor_id = visitor_row.visitor_id
        self.exit_time_field = self.create_text_field("Heure de sortie (HH:MM)", required=False)
        self.observation_field = self.create_text_field("Observation", required=False)
        content = self.build_form_content([self.exit_time_field, self.observation_field])
        self.remplir_champs(visitor_row)
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
                on_release=lambda x: self.enregistrer_modification()
            ),
        ]
        self.dialog = self.creer_dialogue("Modifier le visiteur", content, actions)
        
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

    def ouvrir_dialogue_sortie(self, visitor_row):
        # Crée les champs pour heure de sortie et observation
        self.exit_time_field = self.create_text_field("Heure de sortie (HH:MM)", required=False)
        self.observation_field = self.create_text_field("Observation", required=False)
        content = MDBoxLayout(orientation="vertical", spacing=10, adaptive_height=True)
        content.add_widget(self.exit_time_field)
        content.add_widget(self.observation_field)

        actions = [
            Widget(),
            self.creer_bouton(
                "Annuler",
                style="text",
                on_release=lambda x: self.dialog.dismiss(),
            ),
            self.creer_bouton(
                "Valider",
                style="elevated",
                on_release=lambda x: self.valider_sortie(visitor_row, self.dialog),
            )
        ]
        self.dialog = self.creer_dialogue("Enregistrer la sortie", content, actions)

    def valider_sortie(self, visitor_row, dialog):
        exit_time = self.exit_time_field.text
        observation = self.observation_field.text
        # Mets à jour la base de données via VisitorManager
        success, error = self.manager.mettre_a_jour_visiteur(
            int(visitor_row.visitor_id),
            exit_time=exit_time,
            observation=observation
        )
        if not success:
            self.show_error_dialog(error or "Erreur lors de la mise à jour du visiteur.")
            return
        dialog.dismiss()
        self.afficher_table_visiteurs()
    
    def valider_champs(self, nom, prenom, phone_number, id_type, id_number, motif):
        if not all([nom, prenom, phone_number, id_type, id_number, motif]):
            return "Tous les champs sont obligatoires."
        if not phone_number.isdigit() or len(phone_number) < 10:
            return "Numéro de téléphone invalide."
        return None

    def open_menu(self, name):
        if name == "id":
            items = [
                {"text": "Passeport", "on_release": lambda x="Passeport": self.set_text(x, "id")},
                {"text": "Carte", "on_release": lambda x="Carte": self.set_text(x, "id")},
            ]
            menu = MDDropdownMenu(
                caller=self.id_type_field,
                items=items,
                position="top",
                width=425,
            )
            menu.open()
            self.menu = menu
        elif name == "motif":
            items = [
                {"text": "Consulat", "on_release": lambda x="Consulat": self.set_text(x, "motif")},
                {"text": "Attestation de couverture", "on_release": lambda x="Attestation de couverture": self.set_text(x, "motif")},
                {"text": "Demande de prise en charge", "on_release": lambda x="Demande de prise en charge": self.set_text(x, "motif")},
                {"text": "Légalisation", "on_release": lambda x="Légalisation": self.set_text(x, "motif")},
            ]
            menu = MDDropdownMenu(
                caller=self.motif_field,
                items=items,
                position="top",
                width=425,
            )
            menu.open()
            self.menu = menu
    
    def enregistrer_modification(self):
        try:
            image = self.selected_image_path
            nom = self.nom_field.text
            prenom = self.prenom_field.text
            phone_number = self.phone_field.text
            id_type = self.id_type_field.text
            id_number = self.id_number_field.text
            motif = self.motif_field.text
            exit_time = self.exit_time_field.text
            observation = self.observation_field.text

            if not all([nom, prenom, phone_number, id_type, id_number, motif, exit_time, observation]):
                self.show_error_dialog("Tous les champs sont obligatoires.")
                return

            success, error = self.manager.mettre_a_jour_visiteur(
                self.visitor_id, image_path=image, nom=nom, prenom=prenom,
                phone_number=phone_number, id_type=id_type,
                id_number=id_number, motif=motif,
                exit_time=exit_time, observation=observation
            )
            
            self.visitor_id = None
            
            if not success:
                self.show_error_dialog(error or "Erreur lors de la mise à jour du visiteur.")
                return
            
            self.dialog.dismiss()
            self.afficher_historique()
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

            self.manager.ajouter_visiteur(image, nom, prenom, phone_number, id_type, id_number, motif)
            self.dialog.dismiss()
            self.afficher_table_visiteurs()
        except Exception as e:
            self.show_error_dialog(f"Erreur lors de l'ajout : {e}")

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
        snackbar(text=message, duration=2).open()
        
    def afficher_visiteurs(self, table_id, date_filter=None, date_filter_type=""):
        """Affiche les visiteurs dans la table spécifiée, avec un filtre de date optionnel."""
        screen = self.root.get_screen(self.root.current)
        visitor_table = screen.ids[table_id]

        visiteurs = self.manager.lister_visiteurs()
        row_data = []
        for v in visiteurs:
            try:
                year, month, day = v.date.split("-")
            except ValueError:
                continue  # Ignore les dates mal formatées

            if date_filter_type == "day" and date_filter != day:
                continue
            elif date_filter_type == "month" and date_filter != month:
                continue
            elif date_filter_type == "year" and date_filter != year:
                continue
            elif date_filter_type == "year-month" and not (date_filter.startswith(f"{year}-{month}")):
                continue
            elif date_filter and date_filter_type == "" and date_filter != v.date:
                continue

            row = {
                "visitor_id": str(v.id),
                "image_path": v.image_path,
                "nom": v.nom,
                "prenom": v.prenom,
                "phone_number": v.phone_number,
                "id_type": v.id_type,
                "id_number": v.id_number,
                "motif": v.motif,
                "observation": v.observation if v.observation else "",
                "date": v.date,
                "arrival_time": v.arrival_time,
                "exit_time": v.exit_time if v.exit_time else "",
                "selected": False,
            }
            row_data.append(row)

        visitor_table.data = row_data
    
    def afficher_table_visiteurs(self, date=str(date.today())):
        self.afficher_visiteurs(table_id="table_visiteurs", date_filter=date)

    def afficher_historique(self, date_filter=None, date_filter_type=""):
        self.afficher_visiteurs(table_id="historique_table", date_filter=date_filter, date_filter_type=date_filter_type)

    def select_file(self, path):
        self.file_manager.close()
        if self.file_manager_mode == "export":
            chemin = os.path.join(path, "visiteurs_export.json") if os.path.isdir(path) else path
            self.manager.exporter_visiteurs(chemin)
            self.show_error_dialog(f"Export terminé !\nFichier : {chemin}")
        elif self.file_manager_mode == "import":
            self.manager.importer_visiteurs(path)
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
        
    def envoyer_par_mail(self, *args):
        visiteurs = [row for row in self.manager.lister_visiteurs() if str(row.id) in self.selected_visitors]
        if not visiteurs:
            self.show_error_dialog("Aucun visiteur sélectionné.")
            return

        sujet = "Liste des visiteurs sélectionnés"
        corps = self.generer_message_visiteurs(visiteurs)
        mailto_link = f"mailto:?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps)}"
        webbrowser.open(mailto_link)
        self.dialog.dismiss()

    def envoyer_par_whatsapp(self, *args):
        visiteurs = [row for row in self.manager.lister_visiteurs() if str(row.id) in self.selected_visitors]
        if not visiteurs:
            self.show_error_dialog("Aucun visiteur sélectionné.")
            return

        message = self.generer_message_visiteurs(visiteurs)
        whatsapp_link = f"https://wa.me/?text={urllib.parse.quote(message)}"
        webbrowser.open(whatsapp_link)
        self.dialog.dismiss()
    
    def generer_message_visiteurs(self, visiteurs):
        lignes = ["Liste des visiteurs sélectionnés :\n"]
        for i, v in enumerate(visiteurs, 1):
            lignes.append(
                f"{i}. Nom : {v.nom}\n"
                f"   Prénom : {v.prenom}\n"
                f"   Téléphone : {v.phone_number}\n"
                f"   Pièce d'identité : {v.id_type} - {v.id_number}\n"
                f"   Motif : {v.motif}\n"
                f"   Date : {v.date}\n"
                f"   Heure d'arrivée : {v.arrival_time}\n"
                f"   Heure de sortie : {v.exit_time or 'Non renseignée'}\n"
                f"   Observation : {v.observation or 'Aucune'}\n"
            )
        return "\n".join(lignes)

if __name__ == "__main__":
    GestionVisiteursApp().run()
