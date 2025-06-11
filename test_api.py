import requests
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api():
    """Teste l'API de recommandation."""
    base_url = "http://localhost:8000"
    
    # 1. Obtenir un token
    logger.info("Obtention du token...")
    token_response = requests.post(f"{base_url}/token")
    if token_response.status_code != 200:
        logger.error(f"Erreur lors de l'obtention du token: {token_response.text}")
        return
    
    token_data = token_response.json()
    token = token_data["access_token"]
    logger.info(f"Token obtenu: {token[:20]}...")
    
    # 2. Configurer les headers avec le token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 3. Tester l'endpoint de recommandation
    test_preferences = {
        "objectifs": ["Python", "Machine Learning"],
        "niveau": "Beginner",
        "domaines_interet": ["Data Science", "Artificial Intelligence"],
        "duree_disponible": 40
    }
    
    logger.info("Test des recommandations...")
    recommendations_response = requests.post(
        f"{base_url}/recommandations/",
        headers=headers,
        json=test_preferences
    )
    
    if recommendations_response.status_code != 200:
        logger.error(f"Erreur lors de la recommandation: {recommendations_response.text}")
        return
    
    recommendations = recommendations_response.json()
    logger.info(f"Nombre de recommandations reçues: {len(recommendations)}")
    
    # Afficher les recommandations
    for i, rec in enumerate(recommendations, 1):
        logger.info(f"\nRecommandation {i}:")
        logger.info(f"Titre: {rec['titre']}")
        logger.info(f"Plateforme: {rec['plateforme']}")
        logger.info(f"Score: {rec['score']:.2f}")
        logger.info(f"Niveau: {rec['niveau']}")
        logger.info(f"Durée: {rec['duree']} heures")
        logger.info(f"Compétences: {', '.join(rec['skills'])}")

if __name__ == "__main__":
    test_api() 