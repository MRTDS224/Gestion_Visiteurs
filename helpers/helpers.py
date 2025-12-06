import os
import sys

def resource_path(relative_path):
    """
    Renvoie le chemin absolu vers la ressource, que l'app soit
    en mode dev (script .py) ou packagée en .exe par PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # Lorsque PyInstaller crée un onefile, _MEIPASS pointe vers un dossier temporaire
        base_dir = sys._MEIPASS
    else:
        # En dev, on part du répertoire du fichier courant
        base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, relative_path)