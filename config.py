"""
Configuration du système BlissLearn.
"""
import os
from pathlib import Path

# Chemin de base du projet (le dossier parent du fichier config.py)
BASE_DIR = Path(__file__).resolve().parent

# Dossiers de données
DATA_DIR = BASE_DIR / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'

# Dossier de logs
LOGS_DIR = BASE_DIR / 'logs'

# Fichiers de données
DATA_FILES = {
    'Coursera': RAW_DATA_DIR / 'Coursera.csv',
    'edX': RAW_DATA_DIR / 'edx.csv',
    'Udemy': RAW_DATA_DIR / 'Udemy.csv',
    'Harvard': RAW_DATA_DIR / 'Harvard_university.csv',
    'MIT': RAW_DATA_DIR / 'MIT ocw.csv',
    'Stanford': RAW_DATA_DIR / 'Stanford.csv'
}

# Configuration de l'API
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_RELOAD = os.getenv('API_RELOAD', 'true').lower() == 'true'

# Configuration de la sécurité
SECRET_KEY = os.getenv('SECRET_KEY', "E\FDLmdp0sfWMSWtMjrPe7ol44b5aWk6oJg6fet1Fqo=")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

# Configuration du logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Identifiants de test (à changer en production)
TEST_USERNAME = os.getenv('TEST_USERNAME', 'test')
TEST_PASSWORD = os.getenv('TEST_PASSWORD', 'test123')

# Créer les dossiers nécessaires
def create_required_directories():
    """Crée les dossiers nécessaires s'ils n'existent pas."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Vérifier l'existence des fichiers de données
def verify_data_files():
    """Vérifie l'existence des fichiers de données requis."""
    missing_files = []
    for platform, file_path in DATA_FILES.items():
        if not file_path.exists():
            missing_files.append(str(file_path))
    return missing_files 