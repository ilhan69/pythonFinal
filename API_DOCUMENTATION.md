# API REST - Documentation

## Vue d'ensemble

Cette API REST permet de gérer les articles, commentaires et likes du blog avec support multilingue complet.

**Base URL**: `http://localhost:8000/api/`

## Authentification

L'API utilise l'authentification de session Django. Certaines opérations nécessitent une authentification :
- Création, modification, suppression d'articles
- Création, modification, suppression de commentaires
- Ajout/suppression de likes

## Endpoints

### Articles

#### GET /api/articles/
Liste tous les articles publiés avec pagination et filtres.

**Paramètres de requête** :
- `page` (int) : Numéro de page (défaut: 1)
- `per_page` (int) : Nombre d'articles par page (max: 50, défaut: 10)
- `category` (int) : ID de la catégorie
- `tag` (string) : Slug du tag
- `search` (string) : Recherche dans titre, contenu et extrait
- `author` (int) : ID de l'auteur
- `ordering` (string) : Tri (-created_at, created_at, -views_count, -likes_count, etc.)

**Réponse** :
```json
{
  "success": true,
  "message": "Opération réussie",
  "data": {
    "articles": [...],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 42,
      "has_next": true,
      "has_previous": false,
      "next_page": 2,
      "previous_page": null
    }
  }
}
```

#### POST /api/articles/
Crée un nouvel article (authentification requise).

**Corps de la requête** :
```json
{
  "title": "Titre de l'article",
  "content": "Contenu de l'article",
  "excerpt": "Résumé (optionnel)",
  "status": "draft|published",
  "category_id": 1,
  "tag_ids": [1, 2, 3],
  "meta_title": "Titre SEO",
  "meta_description": "Description SEO"
}
```

#### GET /api/articles/{slug}/
Récupère un article par son slug.

#### PUT /api/articles/{slug}/
Modifie un article (auteur ou admin uniquement).

#### DELETE /api/articles/{slug}/
Supprime un article (auteur ou admin uniquement).

### Commentaires

#### GET /api/articles/{article_slug}/comments/
Liste les commentaires d'un article.

**Paramètres** :
- `page` : Numéro de page
- `per_page` : Commentaires par page (max: 100, défaut: 20)

#### POST /api/articles/{article_slug}/comments/
Ajoute un commentaire (authentification requise).

**Corps** :
```json
{
  "content": "Contenu du commentaire"
}
```

#### PUT /api/comments/{comment_id}/
Modifie un commentaire (auteur ou admin uniquement).

#### DELETE /api/comments/{comment_id}/
Supprime un commentaire (auteur ou admin uniquement).

### Likes

#### POST /api/articles/{article_slug}/like/
Ajoute ou retire un like (authentification requise).

**Réponse** :
```json
{
  "success": true,
  "message": "Article liké",
  "data": {
    "liked": true,
    "likes_count": 15
  }
}
```

### Métadonnées

#### GET /api/categories/
Liste toutes les catégories avec le nombre d'articles.

#### GET /api/tags/
Liste tous les tags avec le nombre d'articles.

**Paramètres** :
- `limit` : Limite le nombre de tags retournés

#### GET /api/stats/
Retourne les statistiques générales du blog.

## Support multilingue

L'API respecte automatiquement la langue de l'interface utilisateur Django. Les messages d'erreur et de succès sont traduits selon la langue active.

Les traductions sont gérées via :
- `gettext()` pour les messages dynamiques
- `gettext_lazy()` pour les messages statiques

## Gestion des erreurs

Toutes les réponses d'erreur suivent le format :
```json
{
  "success": false,
  "message": "Message d'erreur traduit",
  "errors": {...} // Optionnel
}
```

Codes d'erreur :
- 400 : Données invalides
- 401 : Authentification requise
- 403 : Permission refusée
- 404 : Ressource non trouvée
- 500 : Erreur serveur

## Headers CORS

L'API inclut les headers CORS nécessaires pour les requêtes cross-origin.

## Exemples d'utilisation

### JavaScript (Fetch API)

```javascript
// Récupérer les articles
fetch('/api/articles/?search=python&per_page=5')
  .then(response => response.json())
  .then(data => console.log(data));

// Créer un article
fetch('/api/articles/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({
    title: 'Mon nouvel article',
    content: 'Contenu de l\'article',
    status: 'published'
  })
});

// Liker un article
fetch('/api/articles/mon-article/like/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': getCookie('csrftoken')
  }
});
```

### Python (requests)

```python
import requests

# Récupérer les articles
response = requests.get('http://localhost:8000/api/articles/')
articles = response.json()

# Créer un commentaire
response = requests.post(
    'http://localhost:8000/api/articles/mon-article/comments/',
    json={'content': 'Super article !'},
    cookies={'sessionid': 'your_session_id'}
)
```