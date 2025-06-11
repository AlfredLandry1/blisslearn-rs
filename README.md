# BlissLearn - Système de Recommandation de Cours en Ligne

BlissLearn est un système de recommandation intelligent qui aide les apprenants à trouver les meilleurs cours en ligne adaptés à leurs objectifs, leur niveau et leurs centres d'intérêt.

## Fonctionnalités

- Recommandation personnalisée basée sur :
  - Objectifs d'apprentissage
  - Niveau de compétence
  - Domaines d'intérêt
  - Durée disponible
- Support multi-plateformes (Coursera, edX, Udemy, etc.)
- API REST sécurisée avec authentification JWT
- Interface de programmation simple et intuitive

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/votre-username/blisslearn.git
cd blisslearn
```

2. Créer un environnement virtuel :
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Structure du Projet

```
blisslearn/
├── data/
│   └── raw/              # Données brutes des plateformes
├── logs/                 # Fichiers de logs
├── src/
│   └── recommender/      # Module de recommandation
├── tests/               # Tests unitaires et d'intégration
├── notebooks/           # Notebooks Jupyter d'analyse
├── main.py             # Point d'entrée de l'API
├── requirements.txt    # Dépendances Python
└── README.md          # Documentation
```

## Utilisation de l'API

### 1. Démarrer le serveur

```bash
python main.py
```

Le serveur démarre sur `http://localhost:8000`.

### 2. Authentification

Pour utiliser l'API, vous devez d'abord obtenir un token JWT :

```bash
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test&password=test123"
```

Réponse :
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

### 3. Exemples de Recommandations

#### Exemple 1 : Parcours Développeur Full Stack

```bash
curl -X POST "http://localhost:8000/recommandations/" \
     -H "Authorization: Bearer votre_token" \
     -H "Content-Type: application/json" \
     -d '{
         "objectifs": [
             "JavaScript",
             "React",
             "Node.js",
             "MongoDB",
             "Web Development"
         ],
         "niveau": "Intermediate",
         "domaines_interet": [
             "Frontend Development",
             "Backend Development",
             "Database Design",
             "API Development"
         ],
         "duree_disponible": 60,
         "n_recommendations": 5
     }'
```

Réponse :
```json
[
    {
        "titre": "Full Stack Web Development Specialization",
        "plateforme": "Coursera",
        "fournisseur": "Hong Kong University",
        "niveau": "Intermediate",
        "duree": 24.0,
        "skills": [
            "JavaScript",
            "React",
            "Node.js",
            "Express.js",
            "MongoDB",
            "RESTful APIs",
            "Authentication",
            "Web Security"
        ],
        "score": 0.98
    },
    {
        "titre": "The Complete Web Developer in 2024",
        "plateforme": "Udemy",
        "fournisseur": "Zero To Mastery Academy",
        "niveau": "Intermediate",
        "duree": 35.0,
        "skills": [
            "HTML5",
            "CSS3",
            "JavaScript",
            "React",
            "Node.js",
            "Database Design",
            "API Development",
            "DevOps Basics"
        ],
        "score": 0.95
    },
    {
        "titre": "Professional Certificate in Full Stack Development",
        "plateforme": "edX",
        "fournisseur": "MIT",
        "niveau": "Intermediate",
        "duree": 32.0,
        "skills": [
            "MERN Stack",
            "Frontend Architecture",
            "Backend Development",
            "Database Management",
            "Cloud Deployment"
        ],
        "score": 0.93
    },
    {
        "titre": "Advanced Web Development Bootcamp",
        "plateforme": "Udemy",
        "fournisseur": "Colt Steele",
        "niveau": "Intermediate",
        "duree": 28.0,
        "skills": [
            "Modern JavaScript",
            "React Hooks",
            "Redux",
            "Node.js",
            "MongoDB Atlas"
        ],
        "score": 0.91
    },
    {
        "titre": "Full Stack Open 2024",
        "plateforme": "University of Helsinki",
        "fournisseur": "University of Helsinki",
        "niveau": "Intermediate",
        "duree": 30.0,
        "skills": [
            "Modern JavaScript",
            "React",
            "Redux",
            "Node.js",
            "MongoDB",
            "GraphQL",
            "TypeScript",
            "CI/CD"
        ],
        "score": 0.89
    }
]
```

#### Exemple 2 : Parcours Data Science & AI Avancé

```bash
curl -X POST "http://localhost:8000/recommandations/" \
     -H "Authorization: Bearer votre_token" \
     -H "Content-Type: application/json" \
     -d '{
         "objectifs": [
             "Machine Learning",
             "Deep Learning",
             "Natural Language Processing",
             "Computer Vision",
             "MLOps"
         ],
         "niveau": "Advanced",
         "domaines_interet": [
             "Artificial Intelligence",
             "Neural Networks",
             "Big Data",
             "Cloud Computing",
             "Research"
         ],
         "duree_disponible": 120,
         "n_recommendations": 5
     }'
```

Réponse :
```json
[
    {
        "titre": "Advanced Machine Learning Specialization",
        "plateforme": "Coursera",
        "fournisseur": "Higher School of Economics",
        "niveau": "Advanced",
        "duree": 45.0,
        "skills": [
            "Bayesian Methods",
            "Deep Learning",
            "Reinforcement Learning",
            "Computer Vision",
            "NLP",
            "Advanced Mathematics",
            "Research Methods"
        ],
        "score": 0.99
    },
    {
        "titre": "Deep Learning and MLOps Engineer Path",
        "plateforme": "Stanford Online",
        "fournisseur": "Stanford University",
        "niveau": "Advanced",
        "duree": 60.0,
        "skills": [
            "PyTorch",
            "TensorFlow",
            "MLOps",
            "Kubernetes",
            "Model Deployment",
            "CI/CD for ML",
            "Distributed Training"
        ],
        "score": 0.97
    },
    {
        "titre": "Natural Language Processing Specialization",
        "plateforme": "Coursera",
        "fournisseur": "deeplearning.ai",
        "niveau": "Advanced",
        "duree": 40.0,
        "skills": [
            "NLP",
            "Transformers",
            "BERT",
            "GPT",
            "Attention Mechanisms",
            "Text Generation",
            "Language Models"
        ],
        "score": 0.95
    },
    {
        "titre": "Computer Vision Advanced Program",
        "plateforme": "edX",
        "fournisseur": "Georgia Tech",
        "niveau": "Advanced",
        "duree": 35.0,
        "skills": [
            "CNN Architecture",
            "Object Detection",
            "Image Segmentation",
            "GANs",
            "3D Vision",
            "Video Analysis"
        ],
        "score": 0.94
    },
    {
        "titre": "MLOps & Data Engineering Professional",
        "plateforme": "MIT",
        "fournisseur": "MIT",
        "niveau": "Advanced",
        "duree": 50.0,
        "skills": [
            "Data Pipeline Design",
            "Model Monitoring",
            "Feature Store",
            "Model Registry",
            "A/B Testing",
            "Production ML Systems",
            "Cloud Architecture"
        ],
        "score": 0.92
    }
]
```

#### Exemple 3 : Parcours Cybersécurité & Ethical Hacking

```bash
curl -X POST "http://localhost:8000/recommandations/" \
     -H "Authorization: Bearer votre_token" \
     -H "Content-Type: application/json" \
     -d '{
         "objectifs": [
             "Cybersecurity",
             "Ethical Hacking",
             "Network Security",
             "Penetration Testing",
             "Security Certifications"
         ],
         "niveau": "Intermediate",
         "domaines_interet": [
             "Information Security",
             "Network Defense",
             "Malware Analysis",
             "Incident Response",
             "Cloud Security"
         ],
         "duree_disponible": 80,
         "n_recommendations": 5
     }'
```

Réponse :
```json
[
    {
        "titre": "Certified Ethical Hacker (CEH) Preparation",
        "plateforme": "Coursera",
        "fournisseur": "EC-Council",
        "niveau": "Intermediate",
        "duree": 40.0,
        "skills": [
            "Ethical Hacking",
            "Network Security",
            "Vulnerability Assessment",
            "System Hacking",
            "Malware Threats",
            "Social Engineering",
            "Cryptography"
        ],
        "score": 0.97
    },
    {
        "titre": "Advanced Penetration Testing Program",
        "plateforme": "Offensive Security",
        "fournisseur": "Offensive Security",
        "niveau": "Intermediate",
        "duree": 45.0,
        "skills": [
            "Penetration Testing",
            "Exploit Development",
            "Web Application Security",
            "Network Attacks",
            "Privilege Escalation",
            "Report Writing"
        ],
        "score": 0.95
    },
    {
        "titre": "Cloud Security Engineering",
        "plateforme": "edX",
        "fournisseur": "Harvard University",
        "niveau": "Intermediate",
        "duree": 35.0,
        "skills": [
            "AWS Security",
            "Azure Security",
            "Cloud Architecture",
            "Identity Management",
            "Compliance",
            "DevSecOps"
        ],
        "score": 0.93
    },
    {
        "titre": "Incident Response & Digital Forensics",
        "plateforme": "SANS Institute",
        "fournisseur": "SANS",
        "niveau": "Intermediate",
        "duree": 30.0,
        "skills": [
            "Digital Forensics",
            "Incident Handling",
            "Memory Analysis",
            "Network Forensics",
            "Malware Analysis",
            "Evidence Collection"
        ],
        "score": 0.91
    },
    {
        "titre": "Network Defense Essentials",
        "plateforme": "Udemy",
        "fournisseur": "Nathan House",
        "niveau": "Intermediate",
        "duree": 25.0,
        "skills": [
            "Firewall Configuration",
            "IDS/IPS",
            "SIEM",
            "Network Monitoring",
            "Threat Intelligence",
            "Security Architecture"
        ],
        "score": 0.89
    }
]
```

#### Exemple 4 : Parcours DevOps & Cloud Engineering

```bash
curl -X POST "http://localhost:8000/recommandations/" \
     -H "Authorization: Bearer votre_token" \
     -H "Content-Type: application/json" \
     -d '{
         "objectifs": [
             "DevOps",
             "Cloud Architecture",
             "Infrastructure as Code",
             "Containerization",
             "CI/CD"
         ],
         "niveau": "Intermediate",
         "domaines_interet": [
             "AWS",
             "Docker",
             "Kubernetes",
             "Terraform",
             "GitOps"
         ],
         "duree_disponible": 90,
         "n_recommendations": 5
     }'
```

Réponse :
```json
[
    {
        "titre": "DevOps Engineering Professional Certificate",
        "plateforme": "AWS Training",
        "fournisseur": "Amazon Web Services",
        "niveau": "Intermediate",
        "duree": 40.0,
        "skills": [
            "AWS Services",
            "Infrastructure as Code",
            "Docker",
            "Kubernetes",
            "CI/CD Pipelines",
            "Monitoring",
            "Cost Optimization"
        ],
        "score": 0.98
    },
    {
        "titre": "Cloud Native DevOps Bootcamp",
        "plateforme": "Coursera",
        "fournisseur": "Google Cloud",
        "niveau": "Intermediate",
        "duree": 35.0,
        "skills": [
            "Kubernetes",
            "Docker",
            "Microservices",
            "Service Mesh",
            "GitOps",
            "Cloud Native Tools"
        ],
        "score": 0.96
    },
    {
        "titre": "Infrastructure Automation Specialization",
        "plateforme": "HashiCorp Learn",
        "fournisseur": "HashiCorp",
        "niveau": "Intermediate",
        "duree": 30.0,
        "skills": [
            "Terraform",
            "Vault",
            "Consul",
            "Infrastructure as Code",
            "Security Automation",
            "Multi-Cloud"
        ],
        "score": 0.94
    },
    {
        "titre": "GitOps & Continuous Delivery",
        "plateforme": "edX",
        "fournisseur": "Linux Foundation",
        "niveau": "Intermediate",
        "duree": 25.0,
        "skills": [
            "ArgoCD",
            "Flux",
            "GitOps",
            "Helm",
            "Progressive Delivery",
            "Kubernetes Operators"
        ],
        "score": 0.92
    },
    {
        "titre": "Site Reliability Engineering (SRE)",
        "plateforme": "Coursera",
        "fournisseur": "Google",
        "niveau": "Intermediate",
        "duree": 45.0,
        "skills": [
            "SLO/SLI",
            "Monitoring",
            "Incident Response",
            "Performance Optimization",
            "Automation",
            "Chaos Engineering"
        ],
        "score": 0.90
    }
]
```

#### Exemple 5 : Parcours Mobile Development & Cross-Platform

```bash
curl -X POST "http://localhost:8000/recommandations/" \
     -H "Authorization: Bearer votre_token" \
     -H "Content-Type: application/json" \
     -d '{
         "objectifs": [
             "Mobile Development",
             "React Native",
             "Flutter",
             "iOS Development",
             "Android Development"
         ],
         "niveau": "Intermediate",
         "domaines_interet": [
             "Cross-Platform Development",
             "Mobile UI/UX",
             "App Store Deployment",
             "Mobile Security",
             "State Management"
         ],
         "duree_disponible": 70,
         "n_recommendations": 5
     }'
```

Réponse :
```json
[
    {
        "titre": "Cross-Platform Mobile Development",
        "plateforme": "Coursera",
        "fournisseur": "Meta",
        "niveau": "Intermediate",
        "duree": 35.0,
        "skills": [
            "React Native",
            "JavaScript/TypeScript",
            "Mobile Navigation",
            "State Management",
            "Native Modules",
            "Performance Optimization"
        ],
        "score": 0.97
    },
    {
        "titre": "Flutter Development Bootcamp",
        "plateforme": "Udemy",
        "fournisseur": "App Brewery",
        "niveau": "Intermediate",
        "duree": 30.0,
        "skills": [
            "Flutter",
            "Dart",
            "Material Design",
            "State Management",
            "Firebase Integration",
            "Custom Animations"
        ],
        "score": 0.95
    },
    {
        "titre": "iOS App Development with Swift",
        "plateforme": "Coursera",
        "fournisseur": "Apple",
        "niveau": "Intermediate",
        "duree": 40.0,
        "skills": [
            "Swift",
            "UIKit",
            "SwiftUI",
            "Core Data",
            "App Store Guidelines",
            "iOS Security"
        ],
        "score": 0.93
    },
    {
        "titre": "Android Development with Kotlin",
        "plateforme": "Google Developers",
        "fournisseur": "Google",
        "niveau": "Intermediate",
        "duree": 35.0,
        "skills": [
            "Kotlin",
            "Android SDK",
            "Jetpack Compose",
            "Material Design",
            "Google Play Services",
            "App Bundle"
        ],
        "score": 0.91
    },
    {
        "titre": "Mobile App Architecture",
        "plateforme": "edX",
        "fournisseur": "Microsoft",
        "niveau": "Intermediate",
        "duree": 25.0,
        "skills": [
            "Clean Architecture",
            "MVVM Pattern",
            "State Management",
            "Testing Strategies",
            "CI/CD for Mobile",
            "Performance"
        ],
        "score": 0.89
    }
]
```

## Paramètres de Recommandation

- `objectifs` : Liste des objectifs d'apprentissage (obligatoire)
- `niveau` : Niveau souhaité ("Beginner", "Intermediate", "Advanced", "All Levels")
- `domaines_interet` : Liste des domaines d'intérêt
- `duree_disponible` : Durée maximale en heures
- `n_recommendations` : Nombre de recommandations souhaité (défaut: 10)

## Développement

### Tests

Exécuter les tests unitaires :
```bash
pytest tests/
```

### Logs

Les logs sont disponibles dans le dossier `logs/` :
- `app.log` : Logs de l'application

## Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajout d'une nouvelle fonctionnalité'`)
4. Push la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Contact

- Email : alfredlandrytalom2004@egmail.com
- GitHub : [@votre-username](https://github.com/alfred-landry)

## Configuration et Portabilité

Le projet utilise une configuration centralisée qui le rend portable et facile à déplacer :

### Variables d'Environnement

Créez un fichier `.env` à la racine du projet :

```bash
# Configuration de l'API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Configuration de la sécurité
SECRET_KEY=votre_clé_secrète
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuration du logging
LOG_LEVEL=INFO

# Identifiants de test
TEST_USERNAME=test
TEST_PASSWORD=test123
```

### Structure des Dossiers

Le projet utilise des chemins relatifs et crée automatiquement la structure nécessaire :

```
blisslearn/
├── data/
│   └── raw/              # Données brutes (CSV)
├── logs/                 # Logs générés automatiquement
├── src/
│   └── recommender/      # Module de recommandation
├── config.py            # Configuration centralisée
├── main.py             # Point d'entrée de l'API
└── .env                # Variables d'environnement
```

### Déplacement du Projet

Le projet peut être déplacé ou renommé sans problème car :
1. Tous les chemins sont relatifs au dossier racine
2. Les dossiers nécessaires sont créés automatiquement
3. La configuration est centralisée dans `config.py`
4. Les variables sensibles sont dans `.env`

### Vérification des Données

Au démarrage, le système :
1. Crée les dossiers nécessaires s'ils n'existent pas
2. Vérifie la présence des fichiers de données
3. Configure les logs dans le bon dossier
4. Utilise les variables d'environnement

### Personnalisation

Pour personnaliser le projet :
1. Modifiez les variables dans `.env`
2. Ajoutez/modifiez les sources de données dans `config.py`
3. Ajustez les paramètres de logging selon vos besoins 