"""
Script de test pour vérifier le système de recommandation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.recommender.engine import ContentBasedRecommender
from src.recommender.preprocessor import DataPreprocessor

def main():
    # Charger et prétraiter les données
    print("Chargement et prétraitement des données...")
    preprocessor = DataPreprocessor()
    
    # Définir les sources de données
    input_files = {
        "Coursera": "data/raw/Coursera.csv",
        "edX": "data/raw/edx.csv",
        "Udemy": "data/raw/udemy_online_education_courses_dataset.csv",
        "Harvard": "data/raw/Harvard_university.csv",
        "MIT": "data/raw/MIT ocw.csv",
        "Stanford": "data/raw/Stanford.csv"
    }
    
    # Prétraiter les données
    courses_df = preprocessor.preprocess_dataset(input_files)
    print(f"\nNombre total de cours : {len(courses_df)}")
    
    # Initialiser et entraîner le recommender
    print("\nInitialisation du système de recommandation...")
    recommender = ContentBasedRecommender()
    recommender.fit(courses_df)
    
    # Tester les recommandations
    print("\nTest des recommandations...")
    test_preferences = {
        "objectifs": ["Python", "Machine Learning"],
        "niveau": "Beginner",
        "domaines_interet": ["Data Science", "Artificial Intelligence"],
        "duree_disponible": 40
    }
    
    recommendations = recommender.get_recommendations(**test_preferences)
    
    # Afficher les résultats
    print("\nRecommandations trouvées :")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['titre']}")
        print(f"   Plateforme : {rec['plateforme']}")
        print(f"   Fournisseur : {rec['fournisseur']}")
        print(f"   Niveau : {rec['niveau']}")
        if rec['duree']:
            print(f"   Durée : {rec['duree']:.1f} heures")
        if rec['score']:
            print(f"   Score : {rec['score']:.2f}")
        print(f"   Compétences : {', '.join(rec['skills'])}")

if __name__ == "__main__":
    main() 