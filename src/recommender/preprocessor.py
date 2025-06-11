"""
Module de prétraitement des données pour le système de recommandation.

Ce module gère le nettoyage, la fusion et la standardisation des données
provenant de différentes plateformes de cours en ligne.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime
import logging

class DataPreprocessor:
    """
    Préprocesseur de données pour le système de recommandation.
    """
    
    def __init__(self):
        """Initialise le préprocesseur."""
        self.column_mappings = {
            'Coursera': {
                'course': 'title',
                'partner': 'provider',
                'skills': 'skills',
                'rating': 'rating',
                'level': 'level',
                'duration': 'duration'
            },
            'edX': {
                'course_name': 'title',
                'institution': 'provider',
                'skills_taught': 'skills',
                'course_rating': 'rating',
                'course_level': 'level',
                'estimated_time': 'duration'
            },
            'Udemy': {
                'course_title': 'title',
                'instructor': 'provider',
                'course_skills': 'skills',
                'rating': 'rating',
                'level': 'level',
                'duration_hours': 'duration'
            }
        }
        
        self.level_mapping = {
            'beginner': 'Beginner',
            'intermediate': 'Intermediate',
            'advanced': 'Advanced',
            'all levels': 'All Levels',
            'mixed': 'All Levels'
        }
    
    def preprocess_dataset(self, input_files: dict) -> pd.DataFrame:
        """
        Prétraite les données de plusieurs sources.
        
        Args:
            input_files (dict): Dictionnaire des fichiers d'entrée
            
        Returns:
            pd.DataFrame: DataFrame combiné et prétraité
        """
        all_courses = []
        
        for platform, file_path in input_files.items():
            try:
                print(f"Traitement des données de {platform}...")
                
                # Lire le fichier CSV
                df = pd.read_csv(file_path, encoding='utf-8')
                
                # Traiter le DataFrame
                processed_df = self.process_dataset(df, platform)
                
                if len(processed_df) > 0:
                    all_courses.append(processed_df)
                    print(f"✓ {len(processed_df)} cours traités pour {platform}")
                else:
                    print(f"✗ Aucune donnée traitée pour {platform}")
                    
            except Exception as e:
                print(f"✗ Erreur lors du traitement de {platform}: {str(e)}")
                continue
        
        if not all_courses:
            raise Exception("Aucune donnée n'a pu être traitée")
            
        # Combiner tous les DataFrames
        combined_df = pd.concat(all_courses, ignore_index=True)
        
        # Supprimer les doublons
        combined_df = combined_df.drop_duplicates(subset=['title', 'platform', 'provider'])
        
        return combined_df
    
    def process_dataset(self, df: pd.DataFrame, platform: str) -> pd.DataFrame:
        """
        Traite un DataFrame de cours.
        
        Args:
            df (pd.DataFrame): DataFrame à traiter
            platform (str): Nom de la plateforme
            
        Returns:
            pd.DataFrame: DataFrame traité
        """
        try:
            # Créer une copie du DataFrame pour éviter les modifications en place
            df = df.copy()
            
            # Standardiser les noms de colonnes selon la plateforme
            if platform in self.column_mappings:
                df = df.rename(columns=self.column_mappings[platform])
            
            # Créer un nouveau DataFrame avec les colonnes requises
            processed_df = pd.DataFrame()
            
            # Traiter le titre
            if 'title' in df.columns:
                processed_df['title'] = df['title'].fillna('').astype(str)
            else:
                processed_df['title'] = pd.Series([''] * len(df), index=df.index)
            
            # Ajouter la plateforme
            processed_df['platform'] = platform
            
            # Traiter le fournisseur
            if 'provider' in df.columns:
                processed_df['provider'] = df['provider'].fillna(platform).astype(str)
            else:
                processed_df['provider'] = pd.Series([platform] * len(df), index=df.index)
            
            # Traiter la durée
            if 'duration' in df.columns:
                processed_df['duration'] = df['duration'].apply(lambda x: self.clean_duration(x) if pd.notna(x) else np.nan)
            else:
                processed_df['duration'] = pd.Series([np.nan] * len(df), index=df.index)
                
            # Traiter le niveau
            if 'level' in df.columns:
                processed_df['level'] = df['level'].fillna('All Levels').apply(self.clean_level)
            else:
                processed_df['level'] = pd.Series(['All Levels'] * len(df), index=df.index)
                
            # Traiter la note
            if 'rating' in df.columns:
                processed_df['rating'] = df['rating'].apply(lambda x: self.clean_rating(x) if pd.notna(x) else np.nan)
            else:
                processed_df['rating'] = pd.Series([np.nan] * len(df), index=df.index)
                
            # Traiter les compétences
            if 'skills' in df.columns:
                processed_df['skills'] = df['skills'].apply(lambda x: self.parse_skills(x) if pd.notna(x) else [])
            else:
                # Si pas de compétences, utiliser le sujet ou le département
                skills_found = False
                for col in ['Subject', 'Department', 'Topics']:
                    if col in df.columns:
                        processed_df['skills'] = df[col].fillna('').astype(str).apply(lambda x: [x] if x.strip() else [])
                        skills_found = True
                        break
                
                if not skills_found:
                    processed_df['skills'] = pd.Series([[]] * len(df), index=df.index)
            
            # Supprimer les lignes sans titre valide
            processed_df = processed_df[processed_df['title'].str.len() > 0]
            
            # S'assurer que toutes les colonnes ont le bon type
            processed_df['title'] = processed_df['title'].astype(str)
            processed_df['platform'] = processed_df['platform'].astype(str)
            processed_df['provider'] = processed_df['provider'].astype(str)
            processed_df['level'] = processed_df['level'].astype(str)
            
            # Convertir les colonnes numériques
            processed_df['duration'] = pd.to_numeric(processed_df['duration'], errors='coerce')
            processed_df['rating'] = pd.to_numeric(processed_df['rating'], errors='coerce')
            
            # Remplacer les NaN par des valeurs appropriées
            processed_df['title'] = processed_df['title'].fillna('')
            processed_df['platform'] = processed_df['platform'].fillna(platform)
            processed_df['provider'] = processed_df['provider'].fillna(platform)
            processed_df['level'] = processed_df['level'].fillna('All Levels')
            processed_df['skills'] = processed_df['skills'].apply(lambda x: x if isinstance(x, list) else [])
            
            return processed_df
            
        except Exception as e:
            print(f"Erreur détaillée lors du traitement de {platform}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return pd.DataFrame(columns=['title', 'platform', 'provider', 'level', 'duration', 'rating', 'skills'])
            
    def clean_duration(self, duration: Any) -> float:
        """
        Convertit les différents formats de durée en heures.
        
        Args:
            duration (Any): Durée à convertir
            
        Returns:
            float: Durée en heures
        """
        if pd.isna(duration):
            return np.nan
            
        try:
            # Si c'est déjà un nombre
            if isinstance(duration, (int, float)):
                return float(duration) if not np.isnan(float(duration)) else np.nan
                
            duration_str = str(duration).lower()
            
            # Patterns pour différents formats de durée
            hours_match = re.search(r'(\d+\.?\d*)\s*hours?', duration_str)
            months_match = re.search(r'(\d+\.?\d*)\s*months?', duration_str)
            weeks_match = re.search(r'(\d+\.?\d*)\s*weeks?', duration_str)
            minutes_match = re.search(r'(\d+\.?\d*)\s*min', duration_str)
            
            if hours_match:
                return float(hours_match.group(1))
            elif months_match:
                return float(months_match.group(1)) * 30  # estimation
            elif weeks_match:
                return float(weeks_match.group(1)) * 7  # estimation
            elif minutes_match:
                return float(minutes_match.group(1)) / 60
            elif '-' in duration_str:
                # Pour les plages comme "3-6 hours"
                try:
                    nums = re.findall(r'\d+\.?\d*', duration_str)
                    if len(nums) >= 2:
                        avg = (float(nums[0]) + float(nums[1])) / 2
                        if 'month' in duration_str:
                            return avg * 30
                        elif 'week' in duration_str:
                            return avg * 7
                        elif 'hour' in duration_str:
                            return avg
                        elif 'min' in duration_str:
                            return avg / 60
                except:
                    pass
            return np.nan
        except:
            return np.nan
            
    def clean_rating(self, rating: Any) -> float:
        """
        Nettoie et normalise les notes.
        
        Args:
            rating (Any): Note à normaliser
            
        Returns:
            float: Note normalisée
        """
        if pd.isna(rating):
            return np.nan
            
        try:
            # Si c'est déjà un nombre
            if isinstance(rating, (int, float)):
                rating_float = float(rating)
                if np.isnan(rating_float):
                    return np.nan
                if rating_float > 5:
                    return rating_float / 20  # Conversion en échelle de 5
                return rating_float
                
            # Si c'est une chaîne
            rating_str = str(rating).replace('k', '000').strip()
            if not rating_str:
                return np.nan
                
            rating_float = float(rating_str)
            if rating_float > 5:
                return rating_float / 20  # Conversion en échelle de 5
            return rating_float
        except:
            return np.nan
            
    def clean_level(self, level: str) -> str:
        """
        Nettoie et normalise le niveau.
        
        Args:
            level (str): Niveau à normaliser
            
        Returns:
            str: Niveau normalisé
        """
        if pd.isna(level):
            return "All Levels"
            
        level = str(level).lower().strip()
        return self.level_mapping.get(level, "All Levels")
        
    def parse_skills(self, skills: Any) -> List[str]:
        """
        Parse la chaîne de compétences en liste.
        
        Args:
            skills (Any): Compétences à parser
            
        Returns:
            List[str]: Liste des compétences
        """
        # Si c'est déjà une liste
        if isinstance(skills, (list, tuple, np.ndarray)):
            return [str(s).strip() for s in skills if pd.notna(s) and str(s).strip()]
            
        # Si c'est une chaîne
        if isinstance(skills, str):
            # Essayer de parser comme JSON
            try:
                skills_list = json.loads(skills.replace("'", '"'))
                if isinstance(skills_list, list):
                    return [str(s).strip() for s in skills_list if s and str(s).strip()]
            except:
                # Si ce n'est pas du JSON, diviser par virgule
                return [s.strip() for s in skills.split(',') if s.strip()]
                
        # Si c'est un NaN ou None
        if pd.isna(skills):
            return []
            
        # Pour tout autre type
        return [str(skills).strip()] if str(skills).strip() else []

def process_coursera_data(file_path: str) -> pd.DataFrame:
    """Traite les données Coursera."""
    try:
        df = pd.read_csv(file_path)
        df['platform'] = 'Coursera'
        df['duration'] = df['duration'].apply(clean_duration)
        df['level'] = df['level'].apply(clean_level)
        df['rating'] = df['rating'].apply(clean_rating)
        df['skills'] = df['skills'].apply(parse_skills)
        df['price'] = None  # Coursera utilise un modèle d'abonnement
        
        # Renommer les colonnes
        df = df.rename(columns={
            'course': 'title',
            'partner': 'provider',
            'certificatetype': 'certificate_type'
        })
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def process_udemy_data(file_path: str) -> pd.DataFrame:
    """Traite les données Udemy."""
    try:
        df = pd.read_csv(file_path)
        df['platform'] = 'Udemy'
        
        # Gérer les différents noms de colonnes possibles pour la durée
        duration_columns = ['content_duration', 'duration', 'Duration', 'course_duration']
        for col in duration_columns:
            if col in df.columns:
                df['duration'] = df[col].apply(clean_duration)
                break
        
        # Gérer les différents noms de colonnes pour le niveau
        level_columns = ['level', 'Level', 'difficulty']
        for col in level_columns:
            if col in df.columns:
                df['level'] = df[col].apply(clean_level)
                break
        
        # Gérer les différents noms de colonnes pour les compétences
        skills_columns = ['subject', 'Subject', 'topics', 'Topics', 'skills', 'Skills']
        for col in skills_columns:
            if col in df.columns:
                df['skills'] = df[col].apply(lambda x: [x] if pd.notna(x) else [])
                break
        
        # Gérer les différents noms de colonnes pour le titre
        title_columns = ['course_title', 'title', 'name', 'Name', 'Course Name']
        for col in title_columns:
            if col in df.columns:
                df['title'] = df[col]
                break
        
        df['provider'] = 'Udemy'
        
        # Gérer les différents noms de colonnes pour le prix
        price_columns = ['price', 'Price', 'price_detail', 'course_price']
        for col in price_columns:
            if col in df.columns:
                df['price'] = df[col]
                break
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def process_edx_data(file_path: str) -> pd.DataFrame:
    """Traite les données edX."""
    try:
        df = pd.read_csv(file_path)
        df['platform'] = 'edX'
        
        # Mapper les colonnes avec gestion flexible des noms
        column_mapping = {
            'Course Name': 'title',
            'course_name': 'title',
            'name': 'title',
            'Duration': 'duration',
            'duration': 'duration',
            'Length': 'duration',
            'Level': 'level',
            'level': 'level',
            'Difficulty': 'level',
            'University': 'provider',
            'university': 'provider',
            'Institution': 'provider',
            'Price': 'price',
            'price': 'price',
            'Subject': 'skills',
            'subject': 'skills',
            'Topics': 'skills'
        }
        
        # Renommer les colonnes existantes
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Appliquer les transformations sur les colonnes existantes
        if 'duration' in df.columns:
            df['duration'] = df['duration'].apply(clean_duration)
        if 'level' in df.columns:
            df['level'] = df['level'].apply(clean_level)
        if 'skills' in df.columns:
            df['skills'] = df['skills'].apply(lambda x: [x] if pd.notna(x) else [])
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def process_university_data(file_path: str, university_name: str) -> pd.DataFrame:
    """Traite les données des universités."""
    try:
        # Essayer différents encodages
        encodings = ['utf-8', 'latin1', 'cp1252']
        df = None
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError:
                continue
        
        if df is None:
            raise Exception(f"Impossible de lire le fichier avec les encodages: {encodings}")
        
        # Vérifier les colonnes requises
        required_columns = ['Name', 'Duration', 'subject', 'Price', 'Availability']
        if not all(col in df.columns for col in required_columns):
            print(f"Colonnes manquantes dans {file_path}. Colonnes trouvées: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Mapper les colonnes
        df['platform'] = university_name
        df['provider'] = university_name
        df['title'] = df['Name']
        df['skills'] = df['subject'].fillna('')
        
        # Nettoyer la durée
        def clean_duration_harvard(duration):
            if pd.isna(duration):
                return None
            duration = str(duration).lower()
            if 'self-paced' in duration:
                return None
            if 'week' in duration:
                weeks = re.search(r'(\d+)', duration)
                if weeks:
                    return int(weeks.group(1)) * 7
            if 'day' in duration:
                days = re.search(r'(\d+)', duration)
                if days:
                    return int(days.group(1))
            return None
        
        df['duration'] = df['Duration'].apply(clean_duration_harvard)
        
        # Nettoyer le prix
        def clean_price_harvard(price):
            if pd.isna(price):
                return 0
            price = str(price)
            if price.lower() == 'free':
                return 0
            if '+' in price:
                price = price.split('+')[0]
            if '-' in price:
                price = price.split('-')[0]
            price = re.sub(r'[^\d.]', '', price)
            try:
                return float(price) if price else 0
            except ValueError:
                return 0
        
        df['price'] = df['Price'].apply(clean_price_harvard)
        
        # Nettoyer les compétences
        df['skills'] = df['skills'].apply(lambda x: [str(x).strip()] if pd.notna(x) else [])
        
        # Ajouter le niveau (All Levels par défaut)
        df['level'] = 'All Levels'
        
        # Filtrer les cours non disponibles
        df = df[df['Availability'].fillna('').str.contains('Available now', case=False, na=False)]
        
        # Sélectionner les colonnes finales
        final_columns = ['title', 'platform', 'provider', 'duration', 'price', 'level', 'skills']
        df = df[final_columns]
        
        # Supprimer les lignes sans titre
        df = df[df['title'].notna()]
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def process_alison_data(file_path: str) -> pd.DataFrame:
    """Traite les données Alison."""
    try:
        df = pd.read_csv(file_path)
        df['platform'] = 'Alison'
        df['provider'] = 'Alison'
        
        # Mapper les colonnes
        column_mapping = {
            'Course Name': 'title',
            'name': 'title',
            'Duration': 'duration',
            'Time': 'duration',
            'Category': 'skills',
            'category': 'skills'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Appliquer les transformations
        if 'duration' in df.columns:
            df['duration'] = df['duration'].apply(clean_duration)
        df['level'] = 'All Levels'  # Alison ne spécifie pas toujours les niveaux
        df['skills'] = df['skills'].apply(lambda x: [x] if pd.notna(x) else [])
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def process_futurelearn_data(file_path: str) -> pd.DataFrame:
    """Traite les données FutureLearn."""
    try:
        df = pd.read_csv(file_path)
        df['platform'] = 'FutureLearn'
        
        # Mapper les colonnes
        column_mapping = {
            'Course Name': 'title',
            'Title': 'title',
            'Duration': 'duration',
            'Length': 'duration',
            'Level': 'level',
            'Category': 'skills',
            'Organisation': 'provider'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Appliquer les transformations
        if 'duration' in df.columns:
            df['duration'] = df['duration'].apply(clean_duration)
        if 'level' in df.columns:
            df['level'] = df['level'].apply(clean_level)
        df['skills'] = df['skills'].apply(lambda x: [x] if pd.notna(x) else [])
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def process_pluralsight_data(file_path: str) -> pd.DataFrame:
    """Traite les données Pluralsight."""
    try:
        df = pd.read_csv(file_path)
        df['platform'] = 'Pluralsight'
        df['provider'] = 'Pluralsight'
        
        # Mapper les colonnes
        column_mapping = {
            'Course Name': 'title',
            'Title': 'title',
            'Duration': 'duration',
            'Level': 'level',
            'Category': 'skills',
            'Rating': 'rating'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Appliquer les transformations
        if 'duration' in df.columns:
            df['duration'] = df['duration'].apply(clean_duration)
        if 'level' in df.columns:
            df['level'] = df['level'].apply(clean_level)
        if 'rating' in df.columns:
            df['rating'] = df['rating'].apply(clean_rating)
        
        # Assurer que skills est une liste
        if 'skills' not in df.columns:
            df['skills'] = [[]] * len(df)
        else:
            df['skills'] = df['skills'].apply(lambda x: [str(x)] if pd.notna(x) else [])
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def process_swayam_data(file_path: str) -> pd.DataFrame:
    """Traite les données SWAYAM."""
    try:
        df = pd.read_csv(file_path)
        df['platform'] = 'SWAYAM'
        
        # Mapper les colonnes
        column_mapping = {
            'Course Name': 'title',
            'Title': 'title',
            'Duration': 'duration',
            'Level': 'level',
            'Category': 'skills',
            'Institution': 'provider'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Assurer que provider existe
        if 'provider' not in df.columns:
            df['provider'] = 'SWAYAM'
        
        # Appliquer les transformations
        if 'duration' in df.columns:
            df['duration'] = df['duration'].apply(clean_duration)
        if 'level' in df.columns:
            df['level'] = df['level'].apply(clean_level)
        
        # Assurer que skills est une liste
        if 'skills' not in df.columns:
            df['skills'] = [[]] * len(df)
        else:
            df['skills'] = df['skills'].apply(lambda x: [str(x)] if pd.notna(x) else [])
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def process_udacity_data(file_path: str) -> pd.DataFrame:
    """Traite les données Udacity."""
    try:
        df = pd.read_csv(file_path)
        df['platform'] = 'Udacity'
        df['provider'] = 'Udacity'
        
        # Mapper les colonnes
        column_mapping = {
            'Course Name': 'title',
            'Title': 'title',
            'Duration': 'duration',
            'Level': 'level',
            'Category': 'skills',
            'Rating': 'rating'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Appliquer les transformations
        if 'duration' in df.columns:
            df['duration'] = df['duration'].apply(clean_duration)
        if 'level' in df.columns:
            df['level'] = df['level'].apply(clean_level)
        if 'rating' in df.columns:
            df['rating'] = df['rating'].apply(clean_rating)
        
        # Assurer que skills est une liste
        if 'skills' not in df.columns:
            df['skills'] = [[]] * len(df)
        else:
            df['skills'] = df['skills'].apply(lambda x: [str(x)] if pd.notna(x) else [])
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def process_skillshare_data(file_path: str) -> pd.DataFrame:
    """Traite les données Skillshare."""
    try:
        df = pd.read_csv(file_path)
        df['platform'] = 'Skillshare'
        
        # Mapper les colonnes
        column_mapping = {
            'Course Name': 'title',
            'Title': 'title',
            'Duration': 'duration',
            'Level': 'level',
            'Category': 'skills',
            'Teacher': 'provider',
            'Rating': 'rating'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Assurer que provider existe
        if 'provider' not in df.columns:
            df['provider'] = 'Skillshare'
        
        # Appliquer les transformations
        if 'duration' in df.columns:
            df['duration'] = df['duration'].apply(clean_duration)
        if 'level' in df.columns:
            df['level'] = df['level'].apply(clean_level)
        if 'rating' in df.columns:
            df['rating'] = df['rating'].apply(clean_rating)
        
        # Assurer que skills est une liste
        if 'skills' not in df.columns:
            df['skills'] = [[]] * len(df)
        else:
            df['skills'] = df['skills'].apply(lambda x: [str(x)] if pd.notna(x) else [])
        
        return df
    except Exception as e:
        print(f"Erreur lors du traitement de {file_path}: {str(e)}")
        return pd.DataFrame()

def merge_datasets() -> pd.DataFrame:
    """Fusionne tous les datasets en un seul DataFrame cohérent."""
    datasets = []
    
    # Traiter les datasets principaux
    print("Traitement des datasets principaux...")
    main_platforms = {
        'Coursera': 'Coursera.csv',
        'Udemy': 'Udemy.csv',
        'edX': 'edx.csv',
        'Alison': 'alison.csv',
        'FutureLearn': 'futurelearn.csv',
        'Pluralsight': 'pluralsight.csv',
        'SWAYAM': 'swayam.csv',
        'Udacity': 'udacity.csv',
        'Skillshare': 'skillshare.csv'
    }
    
    for platform, file_path in main_platforms.items():
        print(f"Traitement de {platform}...")
        if platform == 'Coursera':
            datasets.append(process_coursera_data(file_path))
        elif platform == 'Udemy':
            datasets.append(process_udemy_data(file_path))
        elif platform == 'edX':
            datasets.append(process_edx_data(file_path))
        elif platform == 'Alison':
            datasets.append(process_alison_data(file_path))
        elif platform == 'FutureLearn':
            datasets.append(process_futurelearn_data(file_path))
        elif platform == 'Pluralsight':
            datasets.append(process_pluralsight_data(file_path))
        elif platform == 'SWAYAM':
            datasets.append(process_swayam_data(file_path))
        elif platform == 'Udacity':
            datasets.append(process_udacity_data(file_path))
        elif platform == 'Skillshare':
            datasets.append(process_skillshare_data(file_path))
    
    # Traiter les datasets universitaires
    print("\nTraitement des datasets universitaires...")
    university_files = {
        'Harvard University': 'Harvard_university.csv',
        'Stanford University': 'Stanford.csv',
        'MIT': 'MIT ocw.csv',
        'Oxford University': 'Oxford.csv',
        'Berkeley': 'Barkeley_extension.csv',
        'LSE': 'london school of economics.csv'
    }
    
    for univ_name, file_path in university_files.items():
        print(f"Traitement de {univ_name}...")
        datasets.append(process_university_data(file_path, univ_name))
    
    # Fusionner tous les datasets
    print("\nFusion des datasets...")
    merged_df = pd.concat(datasets, ignore_index=True)
    
    # Nettoyer les doublons potentiels
    initial_size = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=['title', 'platform', 'provider'])
    duplicates_removed = initial_size - len(merged_df)
    print(f"Doublons supprimés: {duplicates_removed}")
    
    # Standardiser les colonnes
    required_columns = ['title', 'platform', 'provider', 'level', 'duration', 'rating', 'skills', 'price']
    for col in required_columns:
        if col not in merged_df.columns:
            merged_df[col] = None
    
    # Remplir les valeurs manquantes
    merged_df['duration'] = merged_df['duration'].fillna(merged_df['duration'].median())
    merged_df['rating'] = merged_df['rating'].fillna(merged_df['rating'].median())
    merged_df['level'] = merged_df['level'].fillna('All Levels')
    merged_df['skills'] = merged_df['skills'].apply(lambda x: x if isinstance(x, list) else [])
    
    # Créer un index de cours unique
    merged_df['course_id'] = range(len(merged_df))
    
    return merged_df[required_columns + ['course_id']]

def save_processed_data(df: pd.DataFrame, output_file: str = 'processed_courses.csv'):
    """Sauvegarde les données traitées."""
    # Convertir la liste de compétences en chaîne JSON pour le stockage
    df['skills'] = df['skills'].apply(json.dumps)
    df.to_csv(output_file, index=False)
    print(f"Données sauvegardées dans {output_file}")

if __name__ == "__main__":
    # Traiter et fusionner les datasets
    merged_data = merge_datasets()
    
    # Afficher quelques statistiques
    print("\nStatistiques du dataset fusionné:")
    print(f"Nombre total de cours: {len(merged_data)}")
    print(f"Nombre de cours par plateforme:\n{merged_data['platform'].value_counts()}")
    print(f"Nombre de cours par niveau:\n{merged_data['level'].value_counts()}")
    
    # Sauvegarder les données traitées
    save_processed_data(merged_data) 