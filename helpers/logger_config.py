import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Dossier de base
    base_dir = os.path.join(os.path.expanduser("~"), "Documents", "GestionVisiteur")
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "app.log")

    # Handler avec rotation
    handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5 Mo max
        backupCount=3          # garder 3 fichiers de backup
    )

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger
