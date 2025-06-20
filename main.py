"""
API FastAPI pour le système de recommandation BlissLearn.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from contextlib import asynccontextmanager
import pandas as pd
from datetime import timedelta
import logging
from fastapi.responses import JSONResponse
import re

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
    explication: Optional[str] = None

class CourseResponse(BaseModel):
    titre: str
    plateforme: str
    fournisseur: str
    niveau: str
    duree: Optional[float]
    skills: List[str]
    score: Optional[float] = None  # Score non utilisé ici, mais pour homogénéité

class PromptRequest(BaseModel):
    prompt: str

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
            explications = []
            if any(obj.lower() in (s.lower() for s in rec['skills']) for obj in request.objectifs):
                explications.append("Correspond à vos objectifs de compétences")
            if rec['score'] >= 1.2:
                explications.append("Cours très bien noté ou de qualité supérieure")
            if 'gratuit' in str(rec.get('prix', '')).lower() or rec.get('prix', 1) == 0:
                explications.append("Cours gratuit")
            if not explications:
                explications.append("Cours pertinent selon vos critères")
            response.append(RecommendationResponse(
                titre=rec['titre'],
                plateforme=rec['plateforme'],
                fournisseur=rec['fournisseur'],
                niveau=rec['niveau'],
                duree=rec['duree'],
                skills=rec['skills'],
                score=rec['score'],
                explication="; ".join(explications)
            ))
        
        logger.info(f"{len(response)} recommandations générées")
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des recommandations : {str(e)}"
        )

@app.get("/cours/", response_model=List[CourseResponse])
async def get_all_courses(
    skip: int = Query(0, ge=0, description="Décalage de départ pour la pagination"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de cours à retourner"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retourne la liste complète des cours disponibles (paginée).
    """
    try:
        if not recommender or recommender.courses_df is None:
            logger.error("Le système de recommandation n'est pas initialisé")
            raise HTTPException(
                status_code=503,
                detail="Le système de recommandation n'est pas initialisé"
            )
        courses = []
        df = recommender.courses_df.iloc[skip:skip+limit]
        for _, row in df.iterrows():
            courses.append(CourseResponse(
                titre=row['title'],
                plateforme=row['platform'],
                fournisseur=row['provider'],
                niveau=row['level'],
                duree=row['duration'] if pd.notna(row['duration']) else None,
                skills=row['skills'] if isinstance(row['skills'], list) else [],
            ))
        logger.info(f"{len(courses)} cours retournés via /cours/ (pagination: skip={skip}, limit={limit})")
        return courses
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des cours : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des cours : {str(e)}"
        )

@app.get("/recherche/", response_model=List[CourseResponse])
async def search_courses(
    q: Optional[str] = Query(None, description="Mots-clés à rechercher dans le titre, les compétences ou le fournisseur"),
    plateforme: Optional[str] = Query(None, description="Filtrer par plateforme (ex: Coursera, edX, Udemy...)"),
    niveau: Optional[str] = Query(None, description="Filtrer par niveau (Beginner, Intermediate, Advanced, All Levels)"),
    prix_min: Optional[float] = Query(None, ge=0, description="Prix minimum"),
    prix_max: Optional[float] = Query(None, ge=0, description="Prix maximum"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de résultats à retourner"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Recherche intelligente de cours par mots-clés, plateforme, niveau et prix.
    """
    try:
        if not recommender or recommender.courses_df is None:
            logger.error("Le système de recommandation n'est pas initialisé")
            raise HTTPException(
                status_code=503,
                detail="Le système de recommandation n'est pas initialisé"
            )
        df = recommender.courses_df.copy()
        if q:
            q_lower = q.lower()
            df = df[df['title'].str.lower().str.contains(q_lower) |
                    df['provider'].str.lower().str.contains(q_lower) |
                    df['skills'].apply(lambda skills: any(q_lower in str(skill).lower() for skill in skills) if isinstance(skills, list) else False)]
        if plateforme:
            df = df[df['platform'].str.lower() == plateforme.lower()]
        if niveau:
            df = df[df['level'].str.lower() == niveau.lower()]
        if prix_min is not None:
            df = df[df['price'].apply(lambda p: float(p) if p not in [None, ''] else float('inf')) >= prix_min]
        if prix_max is not None:
            df = df[df['price'].apply(lambda p: float(p) if p not in [None, ''] else 0) <= prix_max]
        df = df.head(limit)
        results = []
        for _, row in df.iterrows():
            results.append(CourseResponse(
                titre=row['title'],
                plateforme=row['platform'],
                fournisseur=row['provider'],
                niveau=row['level'],
                duree=row['duration'] if pd.notna(row['duration']) else None,
                skills=row['skills'] if isinstance(row['skills'], list) else [],
            ))
        logger.info(f"Recherche /recherche/ : {len(results)} résultats pour q={q}, plateforme={plateforme}, niveau={niveau}, prix_min={prix_min}, prix_max={prix_max}")
        return results
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de cours : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche de cours : {str(e)}"
        )

@app.get("/stats/")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """
    Retourne des statistiques globales sur le catalogue de cours.
    """
    try:
        if not recommender or recommender.courses_df is None:
            logger.error("Le système de recommandation n'est pas initialisé")
            raise HTTPException(
                status_code=503,
                detail="Le système de recommandation n'est pas initialisé"
            )
        df = recommender.courses_df
        n_total = len(df)
        plateformes = df['platform'].nunique()
        all_skills = set()
        for skills in df['skills']:
            if isinstance(skills, list):
                all_skills.update([s for s in skills if s])
        niveaux = df['level'].value_counts().to_dict()
        stats = {
            "nombre_total_cours": n_total,
            "nombre_plateformes": plateformes,
            "nombre_competences_uniques": len(all_skills),
            "repartition_niveaux": niveaux
        }
        logger.info(f"Statistiques globales calculées : {stats}")
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du calcul des statistiques : {str(e)}"
        )

@app.get("/cours/{course_id}", response_model=CourseResponse)
async def get_course_detail(course_id: int, current_user: User = Depends(get_current_active_user)):
    """
    Retourne le détail d'un cours à partir de son identifiant unique.
    """
    try:
        if not recommender or recommender.courses_df is None:
            logger.error("Le système de recommandation n'est pas initialisé")
            raise HTTPException(status_code=503, detail="Le système de recommandation n'est pas initialisé")
        df = recommender.courses_df
        if 'course_id' not in df.columns:
            raise HTTPException(status_code=404, detail="Identifiant de cours non disponible")
        row = df[df['course_id'] == course_id]
        if row.empty:
            raise HTTPException(status_code=404, detail="Cours non trouvé")
        row = row.iloc[0]
        return CourseResponse(
            titre=row['title'],
            plateforme=row['platform'],
            fournisseur=row['provider'],
            niveau=row['level'],
            duree=row['duration'] if pd.notna(row['duration']) else None,
            skills=row['skills'] if isinstance(row['skills'], list) else [],
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du détail du cours : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du détail du cours : {str(e)}")

@app.get("/plateformes/", response_model=List[str])
async def get_plateformes(current_user: User = Depends(get_current_active_user)):
    """
    Retourne la liste des plateformes de cours disponibles.
    """
    try:
        if not recommender or recommender.courses_df is None:
            logger.error("Le système de recommandation n'est pas initialisé")
            raise HTTPException(status_code=503, detail="Le système de recommandation n'est pas initialisé")
        plateformes = sorted(recommender.courses_df['platform'].dropna().unique().tolist())
        return plateformes
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des plateformes : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des plateformes : {str(e)}")

# Dictionnaire enrichi de domaines/compétences (avec variantes)
ENRICHED_SKILLS = competences = {
    "python": [
        "python", "python3", "python 3", "python2", "python 2",
        "py", "langage python", "phyton", "pyton"
    ],
    "science des données": [
        "science des données", "data science", "big data", "analyse de données",
        "analyse des données", "datascience", "data analyse"
    ],
    "apprentissage automatique": [
        "apprentissage automatique", "machine learning", "ML",
        "apprentissage artificiel", "apprentissage statistique", "autoML"
    ],
    "apprentissage profond": [
        "apprentissage profond", "deep learning", "DL"
    ],
    "développement web": [
        "développement web", "webdev", "web dev", "dev web",
        "web development", "full stack", "fullstack"
    ],
    "cybersécurité": [
        "cybersécurité", "cyber sécurité", "cybersecurity", "infosec",
        "sécurité informatique", "internet security", "information security",
        "sécurité des données", "hacking"
    ],
    "devops": [
        "devops", "dev ops", "CI/CD", "intégration continue",
        "déploiement continu", "infrastructure as code", "devsecops"
    ],
    "cloud computing": [
        "cloud", "cloud computing", "informatique en nuage", "cloud computing",
        "amazon web services", "aws", "azure", "google cloud", "gcp"
    ],
    "développement mobile": [
        "développement mobile", "mobile", "dev mobile", "applications mobiles",
        "android", "iOS", "mobile development", "apps mobile"
    ],
    "front-end": [
        "front-end", "frontend", "front end", "UI", "interface utilisateur",
        "développement frontal", "html", "css", "javascript", "vue js", "react"
    ],
    "back-end": [
        "back-end", "backend", "back end", "serveur", "API",
        "développement backend", "nodejs", "python backend", "java backend", "php"
    ],
    "base de données": [
        "base de données", "bdd", "database", "SQL", "nosql",
        "mysql", "postgresql", "oracle", "mongodb", "cassandra", "firebase"
    ],
    "intelligence artificielle": [
        "intelligence artificielle", "IA", "AI", "artificial intelligence",
        "machine learning", "deep learning", "IA générative", "chatbot", "vision par ordinateur"
    ],
    "statistiques": [
        "statistiques", "stats", "analyse statistique", "statistique",
        "R", "SPSS", "SAS", "data analysis", "analytique"
    ],
    "excel": [
        "excel", "tableur", "feuille de calcul", "microsoft excel",
        "excel vba", "macros excel"
    ],
    "design UI/UX": [
        "ui design", "ux design", "design d'interface", "expérience utilisateur",
        "interface utilisateur", "maquette", "wireframe", "ux/ui"
    ],
    "réalité augmentée": [
        "réalité augmentée", "augmented reality", "AR",
        "réalité virtuelle", "virtual reality", "VR",
        "réalité mixte", "mixed reality", "MR", "metavers"
    ],
    "web3": [
        "web3", "web 3.0", "blockchain", "crypto", "cryptomonnaie",
        "dapp", "smart contract", "ethereum", "bitcoin", "NFT", "décentralisé"
    ],
    "blockchain": [
        "blockchain", "chaîne de blocs", "distributed ledger",
        "registre distribué", "cryptomonnaie", "bitcoin", "ethereum", "EOS", "IOTA"
    ],
    "grands modèles de langage": [
        "grands modèles de langage", "LLM", "large language model",
        "GPT", "GPT-3", "GPT-4", "BERT", "transformer", "modèle pré-entrainé"
    ],
    "prompt engineering": [
        "prompt engineering", "ingénierie de prompt", "conception de prompts",
        "prompt design", "prompting", "ingénierie des requêtes", "AI prompting"
    ],
    "internet des objets": [
        "internet des objets", "IoT", "objets connectés", "capteurs connectés",
        "arduino", "raspberry pi", "smart home", "domotique", "smarthome"
    ]
}


@app.post("/recommandation-prompt/", response_model=List[RecommendationResponse])
async def get_recommendations_from_prompt(
    request: PromptRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Génère des recommandations à partir d'un prompt textuel libre (intelligence automatique, extraction enrichie sans spaCy).
    """
    try:
        prompt = request.prompt.lower()
        # Extraction enrichie des objectifs
        objectifs = set()
        for skill, variants in ENRICHED_SKILLS.items():
            for variant in variants:
                if variant in prompt:
                    objectifs.add(skill)
        # Fallback : extraire tous les mots de plus de 4 lettres non stopwords
        if not objectifs:
            mots = re.findall(r"\b\w{4,}\b", prompt)
            stopwords = set(["cours", "formation", "apprendre", "envie", "souhaite", "rapide", "gratuit", "niveau", "débutant", "avancé", "intermédiaire", "heures", "jours", "semaines", "mois", "projet", "certification", "diplôme", "obtenir", "meilleur", "en", "de", "le", "la", "les", "des", "pour", "avec", "sur", "dans", "et", "ou", "par", "un", "une", "du", "au", "aux", "à", "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses"])
            objectifs = set([w for w in mots if w not in stopwords])
        # Niveau
        niveau = None
        if re.search(r"débutant|beginner", prompt):
            niveau = "Beginner"
        elif re.search(r"intermédiaire|intermediate", prompt):
            niveau = "Intermediate"
        elif re.search(r"avancé|advanced", prompt):
            niveau = "Advanced"
        # Durée
        duree = None
        m = re.search(r"(\d+)\s*(heures|h|jours|j|semaines|mois)", prompt)
        if m:
            val, unite = m.groups()
            val = float(val)
            if 'jour' in unite:
                duree = val * 8
            elif 'semaine' in unite:
                duree = val * 40
            elif 'mois' in unite:
                duree = val * 160
            else:
                duree = val
        # Prix
        prix_max = None
        if 'gratuit' in prompt or 'free' in prompt:
            prix_max = 0
        elif re.search(r"moins de (\d+)[ €$]?", prompt):
            prix_max = float(re.search(r"moins de (\d+)[ €$]?", prompt).group(1))
        # Appel du moteur de recommandation
        recommandations = recommender.get_recommendations(
            objectifs=list(objectifs) or ["Python"],
            niveau=niveau,
            duree_disponible=duree,
            n_recommendations=5
        )
        # Filtrer par prix si besoin
        if prix_max is not None:
            recommandations = [r for r in recommandations if getattr(r, 'prix', None) in [None, '', 0] or (isinstance(r.get('prix', None), (int, float)) and r['prix'] <= prix_max)]
        # Formatage réponse
        response = []
        for rec in recommandations:
            explications = []
            if any(obj.lower() in (s.lower() for s in rec['skills']) for obj in objectifs):
                explications.append("Correspond à vos objectifs de compétences")
            if rec['score'] >= 1.2:
                explications.append("Cours très bien noté ou de qualité supérieure")
            if 'gratuit' in str(rec.get('prix', '')).lower() or rec.get('prix', 1) == 0:
                explications.append("Cours gratuit")
            if not explications:
                explications.append("Cours pertinent selon vos critères")
            response.append(RecommendationResponse(
                titre=rec['titre'],
                plateforme=rec['plateforme'],
                fournisseur=rec['fournisseur'],
                niveau=rec['niveau'],
                duree=rec['duree'],
                skills=rec['skills'],
                score=rec['score'],
                explication="; ".join(explications)
            ))
        logger.info(f"Prompt: {prompt} => {len(response)} recommandations générées")
        return response
    except Exception as e:
        logger.error(f"Erreur lors de la recommandation via prompt : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recommandation via prompt : {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD
    ) 