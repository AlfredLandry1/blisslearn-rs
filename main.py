"""
API FastAPI pour le système de recommandation BlissLearn.
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from contextlib import asynccontextmanager
import pandas as pd
from datetime import timedelta
import logging

from src.recommender.engine import ContentBasedRecommender
from src.recommender.preprocessor import DataPreprocessor
from src.recommender.security import (
    Token,
    User,
    create_access_token,
    get_current_active_user,
    OAuth2PasswordRequestForm
)
from config import (
    LOGS_DIR,
    DATA_FILES,
    LOG_LEVEL,
    LOG_FORMAT,
    API_HOST,
    API_PORT,
    API_RELOAD,
    TEST_USERNAME,
    TEST_PASSWORD,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_required_directories,
    verify_data_files
)

# Créer les dossiers nécessaires
create_required_directories()

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOGS_DIR / 'app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Modèles Pydantic pour la validation des données
class RecommendationRequest(BaseModel):
    objectifs: List[str]
    niveau: Optional[str] = None
    domaines_interet: Optional[List[str]] = None
    duree_disponible: Optional[float] = None
    n_recommendations: Optional[int] = 10

class RecommendationResponse(BaseModel):
    titre: str
    plateforme: str
    fournisseur: str
    niveau: str
    duree: Optional[float]
    skills: List[str]
    score: float

# Variables globales pour stocker les instances
recommender = None
preprocessor = None

# Gestionnaire de cycle de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code à exécuter au démarrage
    global recommender, preprocessor
    
    logger.info("Chargement et prétraitement des données...")
    preprocessor = DataPreprocessor()
    
    # Vérifier l'existence des fichiers
    missing_files = verify_data_files()
    if missing_files:
        error_msg = f"Fichiers manquants : {', '.join(missing_files)}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        # Prétraiter les données
        courses_df = preprocessor.preprocess_dataset(DATA_FILES)
        logger.info(f"Nombre total de cours : {len(courses_df)}")
        
        # Initialiser et entraîner le recommender
        logger.info("Initialisation du système de recommandation...")
        recommender = ContentBasedRecommender()
        recommender.fit(courses_df)
        logger.info("Système de recommandation initialisé avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation : {str(e)}")
        raise
    
    yield
    
    # Code à exécuter à l'arrêt
    logger.info("Arrêt du système...")

# Création de l'application FastAPI
app = FastAPI(
    title="BlissLearn API",
    description="API de recommandation de cours en ligne",
    version="2.2.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Page d'accueil de l'API."""
    return {
        "message": "Bienvenue sur l'API BlissLearn",
        "version": "2.2.0",
        "status": "online"
    }

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint d'authentification pour obtenir un token JWT."""
    try:
        if form_data.username != TEST_USERNAME or form_data.password != TEST_PASSWORD:
            raise HTTPException(
                status_code=401,
                detail="Identifiants incorrects",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        logger.error(f"Erreur d'authentification : {str(e)}")
        raise

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Retourne les informations de l'utilisateur connecté."""
    return current_user

@app.post("/recommandations/", response_model=List[RecommendationResponse])
async def get_recommendations(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Génère des recommandations de cours personnalisées.
    
    Args:
        request (RecommendationRequest): Les préférences de l'utilisateur
        current_user (User): L'utilisateur authentifié
        
    Returns:
        List[RecommendationResponse]: Liste des cours recommandés
    """
    try:
        if not recommender:
            logger.error("Le système de recommandation n'est pas initialisé")
            raise HTTPException(
                status_code=503,
                detail="Le système de recommandation n'est pas initialisé"
            )
        
        logger.info(f"Génération de recommandations pour {current_user.username}")
        logger.info(f"Objectifs : {request.objectifs}")
        
        recommendations = recommender.get_recommendations(
            objectifs=request.objectifs,
            niveau=request.niveau,
            domaines_interet=request.domaines_interet,
            duree_disponible=request.duree_disponible,
            n_recommendations=request.n_recommendations
        )
        
        # Convertir les recommandations en format de réponse
        response = []
        for rec in recommendations:
            response.append(RecommendationResponse(
                titre=rec['titre'],
                plateforme=rec['plateforme'],
                fournisseur=rec['fournisseur'],
                niveau=rec['niveau'],
                duree=rec['duree'],
                skills=rec['skills'],
                score=rec['score']
            ))
        
        logger.info(f"{len(response)} recommandations générées")
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des recommandations : {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD
    ) 