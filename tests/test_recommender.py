"""
Tests unitaires pour le système de recommandation.

Ce module contient les tests pour vérifier le bon fonctionnement
du système de recommandation et de ses composants.
"""

import unittest
import pandas as pd
import numpy as np
from src.recommender.engine import ContentBasedRecommender
from src.recommender.preprocessor import DataPreprocessor
from src.utils.text_utils import TextProcessor

class TestRecommender(unittest.TestCase):
    """Tests pour le système de recommandation."""
    
    @classmethod
    def setUpClass(cls):
        """Initialise les données de test."""
        # Créer un DataFrame de test
        cls.test_data = pd.DataFrame({
            'course_id': [1, 2, 3],
            'title': [
                'Python for Data Science',
                'Web Development with JavaScript',
                'Machine Learning Basics'
            ],
            'description': [
                'Learn Python programming for data analysis',
                'Build modern web applications with JavaScript',
                'Introduction to machine learning algorithms'
            ],
            'platform': [
                'Coursera',
                'Udemy',
                'edX'
            ],
            'provider': [
                'University of Michigan',
                'Tech Academy',
                'MIT'
            ],
            'level': [
                'Beginner',
                'Intermediate',
                'All Levels'
            ],
            'duration': [
                20.0,
                15.0,
                40.0
            ],
            'skills': [
                ['Python', 'Data Analysis', 'Pandas'],
                ['JavaScript', 'HTML', 'CSS'],
                ['Python', 'Machine Learning', 'Statistics']
            ]
        })
        
        # Initialiser le recommender
        cls.recommender = ContentBasedRecommender()
        cls.recommender.fit(cls.test_data)
    
    def test_initialization(self):
        """Teste l'initialisation du recommender."""
        self.assertIsNotNone(self.recommender.courses_df)
        self.assertIsNotNone(self.recommender.tfidf_matrix)
        self.assertEqual(len(self.recommender.courses_df), 3)
    
    def test_recommendations(self):
        """Teste la génération de recommandations."""
        recommendations = self.recommender.get_recommendations(
            objectifs=['Python', 'Data Science'],
            niveau='Beginner',
            domaines_interet=['Machine Learning'],
            n_recommendations=2
        )
        
        self.assertEqual(len(recommendations), 2)
        self.assertIsInstance(recommendations[0], dict)
        self.assertIn('titre', recommendations[0])
        self.assertIn('score', recommendations[0])
    
    def test_domain_relevance(self):
        """Teste le calcul de la pertinence du domaine."""
        course_text = "Python programming with pandas and numpy"
        query_terms = {'Python', 'Data Science'}
        
        relevance = self.recommender.calculate_domain_relevance(
            course_text,
            query_terms
        )
        
        self.assertIsInstance(relevance, float)
        self.assertGreaterEqual(relevance, 0.0)
        self.assertLessEqual(relevance, 1.0)
    
    def test_course_quality_score(self):
        """Teste le calcul du score de qualité des cours."""
        course = self.test_data.iloc[0]
        score = self.recommender.calculate_course_quality_score(course)
        
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0.0)
    
    def test_text_preprocessing(self):
        """Teste le prétraitement du texte."""
        text = "Python Programming & Data Analysis"
        processed = self.recommender.preprocess_text(text)
        
        self.assertIsInstance(processed, str)
        self.assertNotIn('&', processed)
        self.assertEqual(processed, processed.lower())

class TestPreprocessor(unittest.TestCase):
    """Tests pour le préprocesseur de données."""
    
    def setUp(self):
        """Initialise le préprocesseur."""
        self.preprocessor = DataPreprocessor()
    
    def test_clean_text(self):
        """Teste le nettoyage de texte."""
        text = "Python & Data Science!!!"
        cleaned = self.preprocessor.clean_text(text)
        
        self.assertNotIn('&', cleaned)
        self.assertNotIn('!', cleaned)
    
    def test_duration_extraction(self):
        """Teste l'extraction de la durée."""
        durations = [
            ("2 hours", 2.0),
            ("90 minutes", 1.5),
            ("4 weeks", 20.0),
            ("2 months", 40.0)
        ]
        
        for text, expected in durations:
            result = self.preprocessor.extract_duration_hours(text)
            self.assertEqual(result, expected)
    
    def test_level_standardization(self):
        """Teste la standardisation des niveaux."""
        levels = [
            ("beginner", "Beginner"),
            ("débutant", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
            ("invalid", "All Levels")
        ]
        
        for input_level, expected in levels:
            result = self.preprocessor.standardize_level(input_level)
            self.assertEqual(result, expected)
    
    def test_skills_processing(self):
        """Teste le traitement des compétences."""
        skills_inputs = [
            ("Python, Data Science", ["Python", "Data Science"]),
            ('["Python", "SQL"]', ["Python", "SQL"]),
            (["Python", "R"], ["Python", "R"]),
            (None, [])
        ]
        
        for input_skills, expected in skills_inputs:
            result = self.preprocessor.process_skills(input_skills)
            self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main() 