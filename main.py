from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogButtonContainer, MDDialogContentContainer
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from kivy.metrics import dp
from managers.visitor_manager import VisitorManager
import os
from datetime import datetime, date, timezone, timedelta

class VisitorRow(MDBoxLayout):
    image = StringProperty("")
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
    def scroll_table_up(self):
        table = self.ids.table_visiteurs
        table.scroll_y = min(1, table.scroll_y + 0.1)

    def scroll_table_down(self):
        table = self.ids.table_visiteurs
        table.scroll_y = max(0, table.scroll_y - 0.1)

class HistoriqueScreen(MDScreen):
    def on_enter(self, *args):
        MDApp.get_running_app().afficher_historique()


class GestionVisiteursApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = VisitorManager()
        self.dialog = None
        self.data_table = None
        self.menu = None
        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_file,
        )
        self.file_manager_mode = None

    def open_filechooser(self):
        self.file_manager_mode = "image"
        self.file_manager.show("C:/Users/mrtds/Pictures")  # Mets le chemin de départ adapté à ton OS

    def exit_file_manager(self, *args):
        self.file_manager.close()

    def on_start(self):
        self.afficher_table_visiteurs()

    def set_text(self, text, name):
        if name == "id":
            self.id_type_field.text = text
        if name == "motif":
            self.motif_field.text = text
        
        self.menu.dismiss()
    
    def build_form_content(self):
        self.image_button = MDButton(
            MDButtonIcon(
                icon="image"
            ),
            MDButtonText(
                text="Sélectionner une image"
            ),
            on_release=(lambda x: self.open_filechooser()),
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
        self.initialiser_dialogue(content, "Ajouter un visiteur")
    
    def ouvrir_dialogue_partager(self):
        email_button = MDButton(
            MDButtonIcon(
                icon="email"
            ),
            MDButtonText(
                text="Envoyer par mail"
            )
        )
        whatsapp_button  = MDButton(
            MDButtonIcon(
                icon="whatsapp"
            ),
            MDButtonText(
                text="Envoyer par whatsapp"
            )
        )
        
        content = MDBoxLayout(orientation="horizontal", spacing=20, padding=10, adaptive_height=True)
        content.add_widget(email_button)
        content.add_widget(whatsapp_button)
        
        self.initialiser_dialogue(content, "Partager")

    def ouvrir_dialogue_sortie(self, visitor_row):
        # Crée les champs pour heure de sortie et observation
        self.exit_time_field = self.create_text_field("Heure de sortie (HH:MM)", required=False)
        self.observation_field = self.create_text_field("Observation", required=False)
        content = MDBoxLayout(orientation="vertical", spacing=10, adaptive_height=True)
        content.add_widget(self.exit_time_field)
        content.add_widget(self.observation_field)

        dialog = MDDialog(
            MDDialogHeadlineText(text="Sortie du visiteur"),
            MDDialogContentContainer(content),
        )
        dialog.add_widget(
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Annuler"),
                    style="text",
                    on_release=lambda x: dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Valider"),
                    style="elevated",
                    on_release=lambda x: self.valider_sortie(visitor_row, dialog),
                ),
                spacing="10dp"
            )
        )
        dialog.open()
        self.dialog_sortie = dialog

    def valider_sortie(self, visitor_row, dialog):
        exit_time = self.exit_time_field.text
        observation = self.observation_field.text
        # Mets à jour la base de données via VisitorManager
        self.manager.mettre_a_jour_sortie(
            visitor_row.id_number,  # ou un identifiant unique
            exit_time,
            observation
        )
        dialog.dismiss()
        self.afficher_table_visiteurs()
    
    def initialiser_dialogue(self, content, titre):
        self.dialog = MDDialog(
            MDDialogHeadlineText(
                text=titre,
                halign="left",
            ),
            MDDialogContentContainer(
              content,
            ),
        )
        
        if titre != "Partager":
            self.dialog.add_widget(
                MDDialogButtonContainer(
                    Widget(),
                    MDButton(
                        MDButtonText(text="Annuler"),
                        style="text",
                        on_release=(lambda x: self.dialog.dismiss()),
                    ),
                    MDButton(
                        MDButtonText(text="Enregistrer"),
                        style="elevated",
                        on_release=(lambda x: self.enregistrer_visiteur(self.dialog))
                    ),
                    spacing="10dp"
                ),
            )
            self.dialog.auto_dismiss = False
            
        self.dialog.open()

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
    
    def enregistrer_visiteur(self, dialog):
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

            self.manager.ajouter_visiteur(image, nom, prenom, phone_number, id_type, id_number, motif)
            self.dialog.dismiss()
            self.afficher_table_visiteurs()
        except Exception as e:
            self.show_error_dialog(f"Erreur lors de l'ajout : {e}")

    def show_error_dialog(self, message):
        error_dialog = MDDialog(
            MDDialogHeadlineText(text="Erreur"),
            MDDialogContentContainer(MDBoxLayout(
                MDButtonText(text=message),
                orientation="vertical",
                adaptive_height=True
            )),
        )
        error_dialog.open()

    def afficher_visiteurs(self,table_id, date_filter=None):
        """Affiche les visiteurs dans la table spécifiée, avec un filtre de date optionnel."""
        screen = self.root.get_screen(self.root.current)
        visitor_table = screen.ids[table_id]

        visiteurs = self.manager.lister_visiteurs()
        row_data = []
        for v in visiteurs:
            if date_filter and v["date"] != date_filter:
                continue
            row = {
                "image": v["image"],
                "nom": v["nom"],
                "prenom": v["prenom"],
                "phone_number": v["phone_number"],
                "id_type": v["id_type"],
                "id_number": v["id_number"],
                "motif": v["motif"],
                "observation": v["observation"],
                "date": v["date"],
                "arrival_time": v["arrival_time"],
                "exit_time": v["exit_time"]
            }
            row_data.append(row)
        
        visitor_table.data = row_data
    
    def afficher_table_visiteurs(self, date=str(date.today())):
        self.afficher_visiteurs(table_id="table_visiteurs", date_filter=date)

    def afficher_historique(self, date_filter=None):
        self.afficher_visiteurs(table_id="historique_table", date_filter=date_filter)

    def filtrer_historique(self, date_str):
        self.afficher_historique(date_filter=date_str)

    def select_file(self, path):
        self.file_manager.close()
        if self.file_manager_mode == "export":
            # Si l'utilisateur sélectionne un dossier, propose un nom de fichier
            chemin = os.path.join(path, "visiteurs_export.json") if os.path.isdir(path) else path
            self.manager.exporter_visiteurs(chemin)
            self.show_error_dialog(f"Export terminé !\nFichier : {chemin}")
        elif self.file_manager_mode == "import":
            self.manager.importer_visiteurs(path)
            self.afficher_table_visiteurs()
            self.show_error_dialog("Import terminé !")
        elif self.file_manager_mode == "image":
            self.selected_image_path = path
            if hasattr(self, "image_button"):
                self.image_button.children[0].text = os.path.basename(path)
        self.file_manager_mode = None
        
    def exporter_visiteurs(self):
        self.file_manager_mode = "export"
        self.file_manager.show("C:/Users/mrtds/Documents")

    def importer_visiteurs(self):
        self.file_manager_mode = "import"
        self.file_manager.show("C:/Users/mrtds/Documents")

if __name__ == "__main__":
    GestionVisiteursApp().run()
