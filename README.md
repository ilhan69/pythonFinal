# Blog Django - Projet Final Python

![Django](https://img.shields.io/badge/Django-5.2.1-green.svg)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)

Une application de blog moderne développée avec Django, offrant un système complet de gestion d'articles avec authentification utilisateur, catégories, tags, et fonctionnalités sociales.

## 🚀 Fonctionnalités

### 📝 Gestion d'Articles
- **CRUD complet** : Création, lecture, modification et suppression d'articles
- **Éditeur riche** : Intégration de CKEditor pour la rédaction
- **Images de couverture** : Support des images pour les articles
- **Extraits automatiques** : Génération automatique des résumés
- **SEO optimisé** : Meta-titres et descriptions personnalisables
- **Statuts d'article** : Brouillon, Publié, Archivé
- **Estimation du temps de lecture**

### 👥 Système d'Utilisateurs
- **Modèle utilisateur personnalisé** : Extension du modèle Django par défaut
- **Profils utilisateur** : Bio et avatar
- **Authentification complète** : Inscription, connexion, déconnexion
- **Gestion des droits** : Seuls les auteurs peuvent modifier leurs articles

### 🏷️ Organisation du Contenu
- **Catégories** : Classification avec couleurs et icônes personnalisables
- **Tags** : Système de tags avec popularité
- **Recherche PostgreSQL** : Recherche full-text optimisée
- **URLs SEO-friendly** : Slugs automatiques

### 📊 Fonctionnalités Sociales
- **Système de likes** : Un utilisateur = un like par article
- **Partages d'articles** : Suivi des partages avec analytics
- **Commentaires** : Système de commentaires par article
- **Compteurs de vues** : Statistiques de consultation

## 🛠️ Technologies Utilisées

- **Backend** : Django 5.2.1
- **Base de données** : PostgreSQL
- **Frontend** : HTML5, CSS3, JavaScript
- **Éditeur** : CKEditor
- **Gestion des fichiers** : Django Media Files
- **Authentification** : Django Auth System

## 📋 Prérequis

- Python 3.8+
- PostgreSQL 12+
- pip (gestionnaire de packages Python)

## 🔧 Installation

### 1. Cloner le projet
```bash
git clone <votre-repo>
cd pythonFinal
```

### 2. Créer un environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate  # Sur macOS/Linux
# ou
venv\Scripts\activate     # Sur Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration de la base de données

**Créer la base de données PostgreSQL :**
```sql
CREATE DATABASE blogdb;
CREATE USER postgres WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE blogdb TO postgres;
```

**Modifier les paramètres dans `pythonFinal/settings.py` :**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'blogdb',
        'USER': 'postgres',
        'PASSWORD': 'votre_mot_de_passe',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 5. Appliquer les migrations
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### 6. Créer un superutilisateur
```bash
python3 manage.py createsuperuser
```

### 7. Collecter les fichiers statiques (en production)
```bash
python3 manage.py collectstatic
```

## 🚀 Lancement du serveur

### Mode développement
```bash
python3 manage.py runserver
```

L'application sera accessible à l'adresse : http://127.0.0.1:8000/

### Interface d'administration
Accédez à l'interface admin Django : http://127.0.0.1:8000/admin/

## 📁 Structure du Projet

```
pythonFinal/
├── blog/                          # Application principale du blog
│   ├── models.py                  # Modèles (User, Article, Category, Tag, etc.)
│   ├── views.py                   # Vues et logique métier
│   ├── forms.py                   # Formulaires Django
│   ├── urls.py                    # Routes de l'application
│   ├── admin.py                   # Configuration de l'admin Django
│   ├── templates/blog/            # Templates HTML
│   └── migrations/                # Migrations de base de données
├── media/                         # Fichiers uploadés (images, avatars)
├── pythonFinal/                   # Configuration Django
│   ├── settings.py                # Paramètres du projet
│   ├── urls.py                    # URLs principales
│   └── wsgi.py                    # Configuration WSGI
├── db.sqlite3                     # Base de données SQLite (développement)
├── manage.py                      # Script de gestion Django
└── requirements.txt               # Dépendances Python
```

## 🎯 Utilisation

### Créer un article
1. Connectez-vous avec votre compte
2. Allez sur "Ajouter un article"
3. Remplissez le titre, contenu, sélectionnez une catégorie
4. Ajoutez des tags et une image de couverture (optionnel)
5. Choisissez le statut (brouillon ou publié)

### Gérer les catégories et tags
- Accès via l'interface d'administration Django
- Ou via les formulaires dédiés dans l'interface utilisateur

### Recherche d'articles
- Utilise la recherche full-text PostgreSQL
- Recherche dans le titre, contenu et tags

## 🔒 Sécurité

- **CSRF Protection** : Activé par défaut
- **XSS Protection** : Templates Django sécurisés
- **Authentification** : Système Django intégré
- **Validation des données** : Formulaires Django avec validation
- **Upload sécurisé** : Validation des types de fichiers

## 📈 Fonctionnalités Avancées

### Analytics
- Comptage des vues par article
- Suivi des likes et partages
- Statistiques des tags populaires

### SEO
- URLs optimisées avec slugs
- Meta-données personnalisables
- Structure HTML sémantique

### Performance
- Index de recherche PostgreSQL
- Optimisation des requêtes avec `select_related`
- Pagination des listes d'articles

## 🧪 Tests

Pour lancer les tests :
```bash
python3 manage.py test blog
```

## 🚀 Déploiement

### Variables d'environnement recommandées pour la production
```bash
export DEBUG=False
export SECRET_KEY='votre-clé-secrète-sécurisée'
export DATABASE_URL='postgresql://user:password@host:port/dbname'
export ALLOWED_HOSTS='votre-domaine.com'
```

### Configuration pour la production
- Modifier `DEBUG = False` dans settings.py
- Configurer `ALLOWED_HOSTS`
- Utiliser un serveur web (Nginx + Gunicorn)
- Configurer les fichiers statiques et media

## 🤝 Contribution

1. Forkez le projet
2. Créez une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Pushez vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👨‍💻 Auteur

**Ilhan KOPRULU** - Projet Final Python/Django

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Contactez l'équipe de développement

---

*Ce projet a été développé dans le cadre du cours de Python à Isitech.*