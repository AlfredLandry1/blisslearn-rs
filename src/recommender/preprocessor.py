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
import os
import logging


class DataPreprocessor:
    """
    Préprocesseur de données pour le système de recommandation.
    """

    def __init__(self):
        """Initialise le préprocesseur."""
        self.column_mappings = {
            "Coursera": {
                "course": "title",
                "partner": "provider",
                "skills": "skills",
                "rating": "rating",
                "level": "level",
                "duration": "duration",
            },
            "edX": {
                "course_name": "title",
                "institution": "provider",
                "skills_taught": "skills",
                "course_rating": "rating",
                "course_level": "level",
                "estimated_time": "duration",
            },
            "Udemy": {
                "course_title": "title",
                "instructor": "provider",
                "course_skills": "skills",
                "rating": "rating",
                "level": "level",
                "duration_hours": "duration",
            },
            # Ajoute d'autres mappings si nécessaire
        }

        self.level_mapping = {
            "beginner": "Beginner",
            "intermediate": "Intermediate",
            "advanced": "Advanced",
            "all levels": "All Levels",
            "mixed": "All Levels",
        }

    def run_preprocessing(self, input_files: dict, output_file: str):
        """
        Exécute le pipeline de prétraitement complet et sauvegarde le résultat.

        Args:
            input_files (dict): Dictionnaire des fichiers d'entrée {platform: file_path}
            output_file (str): Chemin du fichier de sortie CSV.
        """
        all_courses = []

        for platform, file_path in input_files.items():
            try:
                if not os.path.exists(file_path):
                    print(f"✗ Fichier non trouvé pour {platform}: {file_path}")
                    continue

                print(f"Traitement des données de {platform}...")
                df = pd.read_csv(file_path, encoding="utf-8")
                processed_df = self.process_single_dataset(df, platform)

                if not processed_df.empty:
                    all_courses.append(processed_df)
                    print(f"✓ {len(processed_df)} cours traités pour {platform}")
                else:
                    print(f"✗ Aucune donnée traitée pour {platform}")

            except Exception as e:
                print(f"✗ Erreur lors du traitement de {platform}: {e}")
                continue

        if not all_courses:
            print("Aucune donnée n'a pu être traitée. Fichier non généré.")
            return

        # Combiner, nettoyer et sauvegarder
        combined_df = pd.concat(all_courses, ignore_index=True)
        combined_df = combined_df.drop_duplicates(
            subset=["title", "platform", "provider"]
        )
        combined_df.reset_index(drop=True, inplace=True)
        combined_df["course_id"] = combined_df.index

        # S'assurer que les colonnes finales sont présentes
        final_columns = [
            "course_id",
            "title",
            "platform",
            "provider",
            "level",
            "duration",
            "rating",
            "skills",
            "price",
        ]
        for col in final_columns:
            if col not in combined_df.columns:
                combined_df[col] = np.nan

        combined_df = combined_df[final_columns]  # Ordonner les colonnes

        combined_df.to_csv(output_file, index=False, encoding="utf-8")
        print(
            f"\nFichier '{output_file}' généré avec succès avec {len(combined_df)} cours."
        )

    def process_single_dataset(self, df: pd.DataFrame, platform: str) -> pd.DataFrame:
        """Traite un DataFrame unique d'une plateforme."""
        df = df.copy()

        if platform in self.column_mappings:
            df = df.rename(columns=self.column_mappings[platform])

        processed_data = {}
        processed_data["title"] = (
            df.get("title", pd.Series([""] * len(df))).fillna("").astype(str)
        )
        processed_data["platform"] = platform
        processed_data["provider"] = (
            df.get("provider", pd.Series([platform] * len(df)))
            .fillna(platform)
            .astype(str)
        )
        processed_data["duration"] = df.get(
            "duration", pd.Series([np.nan] * len(df))
        ).apply(lambda x: self.clean_duration(x) if pd.notna(x) else np.nan)
        processed_data["level"] = (
            df.get("level", pd.Series(["All Levels"] * len(df)))
            .fillna("All Levels")
            .apply(self.clean_level)
        )
        processed_data["rating"] = df.get(
            "rating", pd.Series([np.nan] * len(df))
        ).apply(lambda x: self.clean_rating(x) if pd.notna(x) else np.nan)
        processed_data["skills"] = df.get("skills", pd.Series([[]] * len(df))).apply(
            lambda x: self.parse_skills(x) if pd.notna(x) else []
        )
        processed_data["price"] = df.get("price", pd.Series([0.0] * len(df))).apply(
            lambda x: self.clean_price(x) if pd.notna(x) else 0.0
        )

        processed_df = pd.DataFrame(processed_data)
        processed_df = processed_df[processed_df["title"].str.len() > 0]

        return processed_df

    def clean_duration(self, duration: Any) -> float:
        """Convertit les différents formats de durée en heures."""
        if pd.isna(duration):
            return np.nan
        try:
            if isinstance(duration, (int, float)):
                return float(duration)
            duration_str = str(duration).lower()
            val = float(re.findall(r"(\d+\.?\d*)", duration_str)[0])
            if "hour" in duration_str:
                return val
            if "min" in duration_str:
                return val / 60
            if "week" in duration_str:
                return val * 35  # estimation
            if "month" in duration_str:
                return val * 150  # estimation
            return val
        except:
            return np.nan

    def clean_rating(self, rating: Any) -> float:
        """Nettoie et normalise la note sur 5."""
        if pd.isna(rating):
            return np.nan
        try:
            rating_float = float(rating)
            return rating_float if 0 <= rating_float <= 5 else np.nan
        except (ValueError, TypeError):
            return np.nan

    def clean_level(self, level: str) -> str:
        """Standardise les niveaux."""
        level = str(level).lower().strip()
        for key, standard_level in self.level_mapping.items():
            if key in level:
                return standard_level
        return "All Levels"

    def clean_price(self, price: Any) -> float:
        """Nettoie et convertit le prix en float."""
        if pd.isna(price) or str(price).lower() in ["free", "gratuit"]:
            return 0.0
        try:
            price_str = re.sub(r"[^\d\.]", "", str(price))
            return float(price_str) if price_str else 0.0
        except:
            return 0.0

    def parse_skills(self, skills: Any) -> List[str]:
        """Extrait et nettoie une liste de compétences."""
        if pd.isna(skills):
            return []
        if isinstance(skills, list):
            return list(set(s.strip() for s in skills if s and isinstance(s, str)))
        try:
            # Essayer de parser comme du JSON
            skills_list = json.loads(skills)
            return list(set(s.strip() for s in skills_list if s and isinstance(s, str)))
        except:
            # Sinon, traiter comme une chaîne séparée par des virgules
            return list(
                set(s.strip() for s in str(skills).split(",") if s and s.strip())
            )


if __name__ == "__main__":
    # Définir le répertoire de base du projet
    project_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    data_raw_dir = os.path.join(project_dir, "data", "raw")
    data_processed_dir = os.path.join(project_dir, "data", "processed")
    os.makedirs(data_processed_dir, exist_ok=True)

    # Lister tous les fichiers CSV dans le dossier raw
    all_raw_files = {
        os.path.splitext(f)[0].capitalize(): os.path.join(data_raw_dir, f)
        for f in os.listdir(data_raw_dir)
        if f.endswith(".csv")
    }

    # Fichier de sortie
    output_csv_path = os.path.join(data_processed_dir, "processed_courses.csv")

    # Créer et exécuter le préprocesseur
    preprocessor = DataPreprocessor()
    preprocessor.run_preprocessing(all_raw_files, output_csv_path)
