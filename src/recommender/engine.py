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
from collections import defaultdict, Counter
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
        self.feedback_scores = defaultdict(int)
        self.user_history = defaultdict(Counter)
        
        # Poids des différentes plateformes
        self.platform_weights = {
            'Coursera': 1.2,
            'edX': 1.2,
            'MIT': 1.3,
            'Harvard': 1.3,
            'Stanford': 1.3,
            'Udemy': 0.9,
            "aws": 1.1,
            "google cloud": 1.1
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
        
        # Graphe de compétences associées (pour recherche sémantique approchée)
        self.skill_graph = {
            "python": {"data science", "machine learning", "web"},
            "data science": {"python", "machine learning", "sql", "statistiques"},
            "machine learning": {"python", "data science", "deep learning"},
            "web": {"javascript", "html", "css", "react", "python"},
            "javascript": {"web", "react", "nodejs"},
            "react": {"web", "javascript"},
            "cybersécurité": {"réseau", "pentesting"},
        }
    
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
        
        # Bonus pour les cours gratuits ou peu chers
        price = course.get('price', None)
        try:
            price = float(price) if price is not None and price != '' else None
        except Exception:
            price = None
        if price is not None:
            if price == 0:
                score *= 1.2
            elif price < 20:
                score *= 1.1
        
        # Prise en compte du feedback utilisateur
        course_id = course.get('course_id')
        if course_id is not None and course_id in self.feedback_scores:
            feedback_score = self.feedback_scores[course_id]
            if feedback_score > 0:
                score *= (1 + 0.2 * feedback_score) # Bonus pour like
            else:
                score *= (1 - 0.2 * abs(feedback_score)) # Pénalité pour dislike
        
        return score
    
    def record_feedback(self, course_id: int, rating: int):
        """Enregistre un feedback (+1 ou -1) pour un cours."""
        self.feedback_scores[course_id] += rating
    
    def record_user_search(self, username: str, skills: List[str]):
        """Enregistre les compétences recherchées par un utilisateur."""
        self.user_history[username].update(skills)
    
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
        n_recommendations: int = 10,
        niveau: Optional[str] = None,
        duree_max: Optional[float] = None,
        plateforme: Optional[str] = None,
        prix_max: Optional[float] = None,
        username: Optional[str] = None
    ) -> List[dict]:
        """
        Génère des recommandations de cours.
        
        Args:
            objectifs (List[str]): Liste des objectifs d'apprentissage
            n_recommendations (int): Nombre de recommandations à retourner
            niveau (Optional[str]): Niveau souhaité
            duree_max (Optional[float]): Durée maximale disponible en heures
            plateforme (Optional[str]): Plateforme souhaitée
            prix_max (Optional[float]): Prix maximal accepté
            username (Optional[str]): Nom d'utilisateur
            
        Returns:
            List[dict]: Liste des cours recommandés
        """
        if self.courses_df is None or self.tfidf_matrix is None:
            raise ValueError("Le moteur de recommandation n'est pas initialisé.")

        # Enrichissement des objectifs avec des compétences associées (recherche sémantique approchée)
        expanded_objectifs = set(objectifs)
        for obj in objectifs:
            if obj in self.skill_graph:
                expanded_objectifs.update(self.skill_graph[obj])

        query_text = " ".join(expanded_objectifs)
        query_vector = self.vectorizer.transform([query_text])
        
        # Calcul de la similarité cosinus
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Créer un masque pour le filtrage
        mask = np.ones(len(self.courses_df), dtype=bool)
        
        # Filtrer par niveau si spécifié
        if niveau and niveau.lower() != "all levels":
            mask &= (self.courses_df['level'].str.lower() == niveau.lower())
            
        # Filtrer par durée si spécifiée
        if duree_max is not None:
            mask &= (self.courses_df['duration'].fillna(np.inf) <= duree_max)
            
        # Filtrer par plateforme si spécifiée
        if plateforme:
            mask &= (self.courses_df['platform'].str.lower() == plateforme.lower())
            
        # Filtrer par prix si spécifié
        if prix_max is not None:
            mask &= (self.courses_df['price'].fillna(np.inf) <= prix_max)
            
        # Appliquer le masque aux similarités
        similarities[~mask] = -1
        
        # Trier les cours par similarité
        course_indices = similarities.argsort()[::-1]
        
        # Préparer les recommandations
        recommendations = []
        seen_titles = set()
        seen_main_skills = set()
        seen_platforms = set()
        for idx in course_indices:
            if similarities[idx] <= 0:
                break
            course = self.courses_df.iloc[idx]
            # Éviter les doublons de titre
            if course['title'] in seen_titles:
                continue
            # Diversité thématique : éviter les doublons de compétence principale
            main_skill = None
            if isinstance(course['skills'], list) and len(course['skills']) > 0:
                main_skill = course['skills'][0].lower()
            if main_skill and main_skill in seen_main_skills:
                continue
            # Diversité plateforme : éviter trop de répétitions
            platform = course['platform']
            if platform in seen_platforms and len(seen_platforms) < 3:
                continue
            # Calcul du score enrichi
            score = self.calculate_course_quality_score(course)
            
            # Bonus de personnalisation basé sur l'historique
            personalization_bonus = 0
            if username and username in self.user_history:
                user_prefs = self.user_history[username]
                course_skills = course.get('skills', [])
                # Calcule un bonus basé sur la fréquence des compétences recherchées par l'utilisateur
                personalization_bonus = sum(user_prefs.get(skill, 0) for skill in course_skills) / max(1, sum(user_prefs.values()))

            combined_score = (similarities[idx] * 0.6) + (score * 0.4) + (personalization_bonus * 0.2)
            recommendations.append({
                'titre': course['title'],
                'plateforme': course['platform'],
                'fournisseur': course['provider'],
                'niveau': course['level'],
                'duree': course['duration'] if pd.notna(course['duration']) else None,
                'skills': course['skills'],
                'score': float(combined_score)
            })
            seen_titles.add(course['title'])
            if main_skill:
                seen_main_skills.add(main_skill)
            seen_platforms.add(platform)
            if len(recommendations) >= n_recommendations:
                break
        return recommendations 