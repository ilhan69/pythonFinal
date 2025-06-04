# Système de Logging - Documentation

## Vue d'ensemble

Ce système de logging complet pour l'application Django capture et analyse tous les événements importants :

- **Erreurs** : Exceptions, erreurs de validation, erreurs de base de données
- **Sécurité** : Tentatives de connexion, accès non autorisés, activités suspectes
- **Administration** : Actions d'administration, gestion des utilisateurs
- **Contenu** : Création/modification/suppression d'articles, commentaires
- **Accès** : Consultations de pages, tentatives d'accès

## Architecture

### Fichiers de logs
- `logs/django.log` - Logs généraux de l'application
- `logs/errors.log` - Erreurs et exceptions
- `logs/security.log` - Événements de sécurité
- `logs/auth.log` - Authentification et gestion des utilisateurs
- `logs/admin.log` - Actions d'administration
- `logs/alerts.json` - Historique des alertes automatiques

### Composants principaux
- `pythonFinal/logging_utils.py` - Utilitaires de logging centralisés
- `pythonFinal/middleware.py` - Middleware de sécurité automatique
- `scripts/analyze_logs.py` - Analyseur de logs
- `scripts/monitor_logs.py` - Surveillance automatique
- `blog/management/commands/analyze_logs.py` - Commande Django

## Configuration

### Settings Django
La configuration de logging est dans `settings.py` avec :
- Formatters pour différents types de logs
- Handlers pour fichiers et console
- Loggers spécialisés par application
- Rotation automatique (à configurer en production)

### Middleware de sécurité
Le middleware `SecurityLoggingMiddleware` capture automatiquement :
- Tentatives d'accès à des URLs sensibles
- Erreurs 403/404 suspectes
- Échecs de connexion via signals Django

## Utilisation

### Logging dans les vues
```python
from pythonFinal.logging_utils import log_content_action, log_security_event, log_error

# Logger une action sur le contenu
log_content_action(request, 'CREATION', 'Article', article.id, "Titre: Mon Article")

# Logger un événement de sécurité
log_security_event(request, 'TENTATIVE_ACCES_NON_AUTORISE', 'WARNING', "Détails...")

# Logger une erreur
try:
    # code susceptible d'échouer
    pass
except Exception as e:
    log_error(request, e, "Contexte de l'erreur")
```

### Décorateurs de logging
```python
from pythonFinal.logging_utils import log_view_access

@log_view_access('blog')
def ma_vue(request):
    # La vue sera automatiquement loggée
    pass
```

### Commandes d'analyse

#### Rapport complet
```bash
python manage.py analyze_logs
```

#### Analyse des 6 dernières heures
```bash
python manage.py analyze_logs --hours 6
```

#### Seulement les événements de sécurité
```bash
python manage.py analyze_logs --security-only
```

#### Export vers un fichier
```bash
python manage.py analyze_logs --export rapport.txt
```

### Surveillance automatique

#### Vérification ponctuelle
```bash
python scripts/monitor_logs.py
```

#### Vérification avec alertes email
```bash
python scripts/monitor_logs.py --email
```

#### Mode démon (surveillance continue)
```bash
python scripts/monitor_logs.py --daemon
```

## Types d'événements loggés

### Authentification
- `CONNEXION_SUCCES` - Connexion réussie
- `CONNEXION_ECHEC` - Tentative de connexion échouée
- `DECONNEXION` - Déconnexion utilisateur
- `INSCRIPTION_SUCCES` - Nouvelle inscription
- `CHANGEMENT_MOT_DE_PASSE` - Modification de mot de passe

### Gestion des utilisateurs
- `CREATION_UTILISATEUR` - Nouvel utilisateur créé
- `MODIFICATION_UTILISATEUR` - Profil utilisateur modifié
- `SUPPRESSION_COMPTE` - Compte utilisateur supprimé
- `CHANGEMENT_PERMISSIONS` - Modifications des rôles/permissions

### Contenu
- `CREATION` - Création d'article/commentaire/catégorie/tag
- `MODIFICATION` - Modification de contenu
- `SUPPRESSION` - Suppression de contenu
- `ECHEC_CREATION` - Échec de création (validation)

### Sécurité
- `TENTATIVE_ACCES_NON_AUTORISE` - Accès refusé
- `ACTIVITE_SUSPECTE` - Activité anormale détectée
- `SCAN_SUSPECT` - Tentative de scan de vulnérabilités
- `SUPPRESSION_SENSIBLE` - Suppression d'éléments critiques

### Administration
- `ACCES_GESTION` - Accès aux interfaces d'administration
- `MODIFICATION_SYSTEME` - Modifications de configuration
- `EXPORT_DONNEES` - Export de données

## Surveillance et alertes

### Seuils d'alerte configurés
- **Critique** : Plus de 5 tentatives de connexion échouées par heure
- **Avertissement** : Plus de 3 activités suspectes par heure
- **Avertissement** : Plus de 2 tentatives d'accès non autorisées par heure
- **Avertissement** : Ratio échecs/succès de connexion > 30%

### Configuration des alertes email
Dans `scripts/monitor_logs.py`, configurez :
```python
smtp_server = "votre.serveur.smtp"
smtp_port = 587
sender_email = "alerts@votre-domaine.com"
receiver_emails = ["admin@votre-domaine.com"]
```

## Maintenance

### Rotation des logs
Ajoutez dans crontab pour rotation automatique :
```bash
# Rotation hebdomadaire des logs
0 0 * * 0 cd /path/to/project && python manage.py rotate_logs
```

### Nettoyage automatique
```bash
# Suppression des logs > 30 jours
find logs/ -name "*.log" -mtime +30 -delete
```

### Surveillance continue
Ajoutez dans crontab :
```bash
# Vérification chaque heure
0 * * * * cd /path/to/project && python scripts/monitor_logs.py

# Rapport quotidien par email
0 8 * * * cd /path/to/project && python scripts/monitor_logs.py --hours 24 --email
```

## Analyse et rapports

### Métriques disponibles
- Nombre d'événements par type et période
- Top des adresses IP les plus actives
- Ratios de succès/échec pour les connexions
- Évolution des activités suspectes
- Statistiques d'utilisation par utilisateur

### Exemples de requêtes d'analyse
```bash
# Événements des 7 derniers jours
python manage.py analyze_logs --hours 168

# Seulement la sécurité des dernières 2 heures
python manage.py analyze_logs --hours 2 --security-only

# Export pour archivage
python manage.py analyze_logs --hours 720 --export logs/rapport_mensuel.txt
```

## Personnalisation

### Ajouter de nouveaux types d'événements
1. Définir les constantes dans `logging_utils.py`
2. Ajouter les fonctions de logging appropriées
3. Mettre à jour les analyseurs dans `analyze_logs.py`

### Modifier les seuils d'alerte
Éditez `monitor_logs.py` dans la méthode `check_security_alerts()`

### Ajouter de nouveaux loggers
Dans `settings.py`, section `LOGGING['loggers']`

## Dépannage

### Logs manquants
- Vérifiez les permissions du répertoire `logs/`
- Contrôlez la configuration des handlers dans `settings.py`
- Vérifiez que le middleware est correctement configuré

### Performances
- Utilisez des niveaux de log appropriés (INFO/WARNING/ERROR)
- Configurez la rotation des logs en production
- Limitez les logs DEBUG en production

### Alertes non reçues
- Vérifiez la configuration SMTP
- Contrôlez les permissions du script de surveillance
- Vérifiez les logs du système pour les erreurs cron

## Sécurité

### Bonnes pratiques
- Ne loggez jamais de mots de passe ou données sensibles
- Limitez l'accès aux fichiers de logs
- Chiffrez les logs en transit si envoyés vers un serveur central
- Auditez régulièrement les accès aux logs

### Conformité
Ce système aide à la conformité RGPD en :
- Traçant les accès aux données personnelles
- Enregistrant les demandes de suppression
- Surveillant les tentatives d'accès non autorisées
- Fournissant des rapports d'audit

## Support

Pour toute question ou problème :
1. Consultez les logs d'erreur : `logs/errors.log`
2. Vérifiez la configuration Django
3. Testez les scripts en mode verbose
4. Consultez la documentation Django sur le logging