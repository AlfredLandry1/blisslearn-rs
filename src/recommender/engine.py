"""
Module du moteur de recommandation basé sur le contenu.

Ce module implémente un système de recommandation de cours basé sur :
- La similarité TF-IDF des descriptions et compétences
- La pondération des plateformes
- Le filtrage par niveau et durée
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Set, Tuple, Optional
import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from collections import defaultdict
from nltk.stem import WordNetLemmatizer

class ContentBasedRecommender:
    """
    Système de recommandation de cours basé sur le contenu.
    
    Utilise TF-IDF et la similarité cosinus pour trouver les cours
    les plus pertinents en fonction des préférences de l'utilisateur.
    """
    
    def __init__(self):
        """Initialise le système de recommandation."""
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)
        )
        self.lemmatizer = WordNetLemmatizer()
        self.courses_df = None
        self.tfidf_matrix = None
        
        # Poids des différentes plateformes
        self.platform_weights = {
            'Coursera': 1.2,
            'edX': 1.2,
            'MIT': 1.3,
            'Harvard': 1.3,
            'Stanford': 1.3,
            'Udemy': 0.9
        }
        
        # Dictionnaire enrichi des termes techniques et leurs variantes
        self.tech_terms = {
            'javascript': {'js', 'javascript', 'ecmascript', 'node.js', 'nodejs', 'react', 'vue', 'angular'},
            'web': {'web', 'webapp', 'website', 'web development', 'web application', 'frontend', 'backend'},
            'python': {'python', 'py', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'scipy'},
            'data science': {'data science', 'data analysis', 'machine learning', 'ml', 'deep learning'},
            'database': {'sql', 'mysql', 'postgresql', 'mongodb', 'database', 'db', 'oracle', 'nosql'},
        }
        
        # Charger les stopwords pour plusieurs langues
        self.stop_words = set()
        for lang in ['french', 'english']:
            try:
                self.stop_words.update(stopwords.words(lang))
            except:
                print(f"Warning: stopwords not available for {lang}")
        
        # Cache pour les termes fréquents par domaine
        self.domain_terms_cache = {}
    
    def safe_float(self, value: Any) -> float:
        """Convertit une valeur en float de manière sécurisée."""
        if pd.isna(value):
            return 0.0
        try:
            float_val = float(value)
            return float_val if np.isfinite(float_val) else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def safe_list(self, value: Any) -> List[str]:
        """Convertit une valeur en liste de manière sécurisée."""
        # Si c'est une série pandas ou un tableau numpy
        if hasattr(value, 'tolist'):
            value = value.tolist()
        
        # Si c'est NaN ou None
        if isinstance(value, float) and np.isnan(value):
            return []
        if value is None:
            return []
            
        # Si c'est une chaîne, essayer de la parser comme JSON
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except:
                return [value] if value.strip() else []
                
        # Si c'est une liste/tuple/set
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value if item is not None and (not isinstance(item, float) or not np.isnan(item))]
            
        # Pour tout autre type
        return [str(value)]
    
    def extract_domain_terms(self, text: str) -> Set[str]:
        """Extrait les termes de domaine pertinents du texte."""
        if pd.isna(text):
            return set()
        words = set(str(text).lower().split())
        domain_terms = set()
        
        for domain, terms in self.tech_terms.items():
            if any(term in words for term in terms):
                domain_terms.add(domain)
                domain_terms.update(terms)
        
        return domain_terms
    
    def calculate_domain_relevance(self, course_text: str, query_terms: Set[str]) -> float:
        """Calcule la pertinence du domaine entre le cours et la requête."""
        if pd.isna(course_text) or not query_terms:
            return 0.0
        course_terms = self.extract_domain_terms(str(course_text))
        if not course_terms:
            return 0.0
        
        intersection = len(course_terms.intersection(query_terms))
        union = len(course_terms.union(query_terms))
        return intersection / union if union > 0 else 0.0
    
    def expand_terms(self, text: str) -> str:
        """Enrichit le texte avec des termes connexes et synonymes."""
        if pd.isna(text):
            return ""
        words = str(text).lower().split()
        expanded = set(words)
        
        for word in words:
            for key, variants in self.tech_terms.items():
                if word in variants or any(variant in str(text).lower() for variant in variants):
                    expanded.update(variants)
                    expanded.add(key)
        
        return " ".join(expanded)
    
    def preprocess_text(self, text: str) -> str:
        """
        Prétraite le texte pour l'analyse TF-IDF.
        
        Args:
            text (str): Texte à prétraiter
            
        Returns:
            str: Texte prétraité
        """
        if pd.isna(text):
            return ""
        
        # Tokenisation et mise en minuscules
        tokens = word_tokenize(str(text).lower())
        
        # Lemmatisation
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        return " ".join(tokens)
    
    def calculate_course_quality_score(self, course: pd.Series) -> float:
        """Calcule un score de qualité pour un cours basé sur plusieurs facteurs."""
        score = 1.0
        
        # Bonus pour les plateformes prestigieuses
        platform = course.get('platform', '')
        score *= self.platform_weights.get(platform, 1.0)
        
        # Bonus pour les cours bien notés
        rating = self.safe_float(course.get('rating'))
        if rating >= 4.5:
            score *= 1.3
        elif rating >= 4.0:
            score *= 1.2
        elif rating >= 3.5:
            score *= 1.1
        
        # Bonus pour les cours avec une bonne description des compétences
        skills = self.safe_list(course.get('skills', []))
        if len(skills) >= 5:
            score *= 1.2
        elif len(skills) >= 3:
            score *= 1.1
        
        return score
    
    def prepare_course_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare les caractéristiques des cours pour l'analyse.
        
        Args:
            df (pd.DataFrame): DataFrame des cours
            
        Returns:
            pd.DataFrame: DataFrame avec les caractéristiques préparées
        """
        df = df.copy()
        
        # S'assurer que toutes les colonnes nécessaires existent
        required_columns = ['title', 'provider', 'skills', 'platform', 'level', 'duration']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Nettoyer les valeurs NaN
        df['title'] = df['title'].fillna('')
        df['provider'] = df['provider'].fillna('')
        df['skills'] = df['skills'].apply(self.safe_list)
        df['platform'] = df['platform'].fillna('')
        df['level'] = df['level'].fillna('')
        df['duration'] = df['duration'].apply(self.safe_float)
        
        # Combiner les caractéristiques textuelles
        df['combined_features'] = df.apply(
            lambda row: " ".join([
                str(row['title']),
                str(row['provider']),
                " ".join(self.safe_list(row['skills']))
            ]),
            axis=1
        )
        
        # Prétraiter le texte
        df['combined_features'] = df['combined_features'].apply(self.preprocess_text)
        
        return df
    
    def fit(self, courses_df: pd.DataFrame) -> None:
        """
        Entraîne le système de recommandation.
        
        Args:
            courses_df (pd.DataFrame): DataFrame des cours
        """
        if len(courses_df) == 0:
            raise ValueError("Le DataFrame des cours est vide")
            
        self.courses_df = courses_df.copy()
        
        # Créer le texte pour chaque cours
        course_texts = []
        for _, row in self.courses_df.iterrows():
            text_parts = [
                row['title'] + " " + row['title'],  # Donner plus de poids au titre
                row['provider'],
                row['level'],
                " ".join(row['skills'])
            ]
            course_texts.append(" ".join(text_parts).lower())
            
        # Calculer la matrice TF-IDF
        self.tfidf_matrix = self.vectorizer.fit_transform(course_texts)
        
        # Précalculer les termes de domaine pour chaque cours
        self.domain_terms_cache = {
            i: self.extract_domain_terms(text)
            for i, text in enumerate(course_texts)
        }
    
    def get_recommendations(
        self,
        objectifs: List[str],
        niveau: Optional[str] = None,
        domaines_interet: Optional[List[str]] = None,
        duree_disponible: Optional[float] = None,
        n_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Génère des recommandations de cours.
        
        Args:
            objectifs (List[str]): Liste des objectifs d'apprentissage
            niveau (Optional[str]): Niveau souhaité
            domaines_interet (Optional[List[str]]): Domaines d'intérêt
            duree_disponible (Optional[float]): Durée disponible en heures
            n_recommendations (int): Nombre de recommandations à retourner
            
        Returns:
            List[Dict[str, Any]]: Liste des cours recommandés
        """
        if not self.courses_df is not None or not self.tfidf_matrix is not None:
            raise ValueError("Le recommender n'a pas été entraîné")
            
        # Créer le texte de requête
        query_parts = []
        
        # Ajouter les objectifs avec plus de poids
        for obj in objectifs:
            query_parts.extend([obj] * 3)
            
        # Ajouter le niveau si spécifié
        if niveau:
            query_parts.append(niveau)
            
        # Ajouter les domaines d'intérêt
        if domaines_interet:
            query_parts.extend(domaines_interet)
            
        query_text = " ".join(query_parts).lower()
        
        # Vectoriser la requête
        query_vector = self.vectorizer.transform([query_text])
        
        # Calculer les similarités
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Créer un masque pour le filtrage
        mask = np.ones(len(self.courses_df), dtype=bool)
        
        # Filtrer par niveau si spécifié
        if niveau and niveau.lower() != "all levels":
            mask &= (self.courses_df['level'].str.lower() == niveau.lower())
            
        # Filtrer par durée si spécifiée
        if duree_disponible is not None:
            mask &= (self.courses_df['duration'].fillna(np.inf) <= duree_disponible)
            
        # Appliquer le masque aux similarités
        similarities[~mask] = -1
        
        # Trier les cours par similarité
        course_indices = similarities.argsort()[::-1]
        
        # Préparer les recommandations
        recommendations = []
        seen_titles = set()
        
        for idx in course_indices:
            if similarities[idx] <= 0:
                break
                
            course = self.courses_df.iloc[idx]
            
            # Éviter les doublons
            if course['title'] in seen_titles:
                continue
                
            seen_titles.add(course['title'])
            
            recommendations.append({
                'titre': course['title'],
                'plateforme': course['platform'],
                'fournisseur': course['provider'],
                'niveau': course['level'],
                'duree': course['duration'] if pd.notna(course['duration']) else None,
                'skills': course['skills'],
                'score': float(similarities[idx])
            })
            
            if len(recommendations) >= n_recommendations:
                break
                
        return recommendations 