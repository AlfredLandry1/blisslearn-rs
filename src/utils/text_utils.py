"""
Utilitaires pour le traitement de texte.

Ce module fournit des fonctions utilitaires pour le traitement
et l'analyse de texte utilisées dans le système de recommandation.
"""

import re
import string
import json
from typing import List, Set, Dict, Any
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag

def ensure_nltk_resources():
    """Télécharge les ressources NLTK nécessaires si elles ne sont pas présentes."""
    resources = ['punkt', 'stopwords', 'averaged_perceptron_tagger', 'wordnet']
    for resource in resources:
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            nltk.download(resource, quiet=True)

class TextProcessor:
    """
    Classe pour le traitement avancé de texte.
    
    Cette classe fournit des méthodes pour :
    - La tokenization
    - La lemmatisation
    - L'extraction de termes techniques
    - L'analyse de similarité textuelle
    """
    
    def __init__(self, language: str = 'french'):
        """
        Initialise le processeur de texte.
        
        Args:
            language (str): Langue principale ('french' ou 'english')
        """
        ensure_nltk_resources()
        
        self.language = language
        self.stop_words = set(stopwords.words(language))
        if language == 'french':
            self.stop_words.update(stopwords.words('english'))
        
        self.lemmatizer = WordNetLemmatizer()
        
        # Dictionnaire des termes techniques par domaine
        self.tech_terms = self._load_tech_terms()
    
    def _load_tech_terms(self) -> Dict[str, Set[str]]:
        """
        Charge le dictionnaire des termes techniques.
        
        Returns:
            Dict[str, Set[str]]: Dictionnaire des termes par domaine
        """
        return {
            "Programming": {
                "python", "java", "javascript", "c++", "ruby", "php",
                "html", "css", "sql", "api", "git", "docker"
            },
            "Data Science": {
                "machine learning", "deep learning", "neural network",
                "statistics", "regression", "classification", "clustering",
                "data analysis", "visualization", "pandas", "numpy"
            },
            "Web Development": {
                "frontend", "backend", "fullstack", "react", "angular",
                "vue", "node.js", "express", "django", "flask", "api"
            },
            "Cloud Computing": {
                "aws", "azure", "google cloud", "docker", "kubernetes",
                "devops", "microservices", "serverless", "cloud native"
            },
            "Cybersecurity": {
                "security", "encryption", "firewall", "vulnerability",
                "penetration testing", "cryptography", "authentication"
            }
        }
    
    def preprocess_text(self, text: str) -> str:
        """
        Prétraite un texte pour l'analyse.
        
        Args:
            text (str): Texte à prétraiter
            
        Returns:
            str: Texte prétraité
        """
        if not isinstance(text, str):
            return ""
        
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer la ponctuation
        text = text.translate(str.maketrans("", "", string.punctuation))
        
        # Tokenization
        tokens = word_tokenize(text)
        
        # Supprimer les stopwords et les tokens courts
        tokens = [
            token for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]
        
        # Lemmatisation
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        return " ".join(tokens)
    
    def extract_technical_terms(self, text: str) -> Dict[str, Set[str]]:
        """
        Extrait les termes techniques d'un texte par domaine.
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            Dict[str, Set[str]]: Termes techniques trouvés par domaine
        """
        text = text.lower()
        found_terms = {}
        
        for domain, terms in self.tech_terms.items():
            domain_terms = set()
            for term in terms:
                if term in text:
                    domain_terms.add(term)
            if domain_terms:
                found_terms[domain] = domain_terms
        
        return found_terms
    
    def extract_key_phrases(self, text: str, max_phrases: int = 5) -> List[str]:
        """
        Extrait les phrases clés d'un texte.
        
        Args:
            text (str): Texte à analyser
            max_phrases (int): Nombre maximum de phrases à extraire
            
        Returns:
            List[str]: Liste des phrases clés
        """
        # Tokenization et POS tagging
        tokens = word_tokenize(text)
        tagged = pos_tag(tokens)
        
        # Extraire les groupes nominaux
        phrases = []
        current_phrase = []
        
        for word, tag in tagged:
            if tag.startswith(('NN', 'JJ')):  # Noms et adjectifs
                current_phrase.append(word)
            elif current_phrase:
                if len(current_phrase) > 1:
                    phrases.append(" ".join(current_phrase))
                current_phrase = []
        
        # Ajouter la dernière phrase si elle existe
        if current_phrase and len(current_phrase) > 1:
            phrases.append(" ".join(current_phrase))
        
        # Trier par longueur et retourner les plus longues
        phrases.sort(key=len, reverse=True)
        return phrases[:max_phrases]
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité entre deux textes.
        
        Args:
            text1 (str): Premier texte
            text2 (str): Second texte
            
        Returns:
            float: Score de similarité entre 0 et 1
        """
        # Prétraiter les textes
        tokens1 = set(self.preprocess_text(text1).split())
        tokens2 = set(self.preprocess_text(text2).split())
        
        # Calculer la similarité de Jaccard
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0 