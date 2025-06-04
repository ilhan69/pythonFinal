"""
Utilitaires de logging pour l'application pythonFinal
"""
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from functools import wraps

User = get_user_model()

# Configuration des loggers
blog_logger = logging.getLogger('blog')
users_logger = logging.getLogger('users')
security_logger = logging.getLogger('security')
admin_logger = logging.getLogger('admin_actions')
comments_logger = logging.getLogger('comments')
stats_logger = logging.getLogger('stats')

def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_info(user):
    """Récupère les informations utilisateur pour le logging"""
    if user and user.is_authenticated:
        return f"{user.username} (ID: {user.id}, Role: {user.role})"
    return "Utilisateur anonyme"

def log_auth_event(request, event_type, username=None, success=True, extra_info=None):
    """Log des événements d'authentification"""
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    if success:
        level = logging.INFO
        status = "SUCCÈS"
    else:
        level = logging.WARNING
        status = "ÉCHEC"
    
    message = f"[{event_type}] {status} - Utilisateur: {username or 'N/A'} - IP: {ip} - User-Agent: {user_agent[:100]}"
    if extra_info:
        message += f" - Info: {extra_info}"
    
    users_logger.log(level, message)

def log_admin_action(request, action, target_object=None, extra_info=None):
    """Log des actions administratives"""
    user_info = get_user_info(request.user)
    ip = get_client_ip(request)
    
    message = f"[ACTION ADMIN] {action} - Par: {user_info} - IP: {ip}"
    if target_object:
        message += f" - Cible: {target_object}"
    if extra_info:
        message += f" - Info: {extra_info}"
    
    admin_logger.info(message)

def log_security_event(request, event_type, severity='WARNING', extra_info=None):
    """Log des événements de sécurité"""
    user_info = get_user_info(request.user)
    ip = get_client_ip(request)
    
    message = f"[SÉCURITÉ] {event_type} - Utilisateur: {user_info} - IP: {ip}"
    if extra_info:
        message += f" - Info: {extra_info}"
    
    if severity == 'CRITICAL':
        security_logger.critical(message)
    elif severity == 'ERROR':
        security_logger.error(message)
    else:
        security_logger.warning(message)

def log_content_action(request, action, content_type, content_id=None, extra_info=None):
    """Log des actions sur le contenu (articles, commentaires, etc.)"""
    user_info = get_user_info(request.user)
    ip = get_client_ip(request)
    
    message = f"[CONTENU] {action} - {content_type} - Par: {user_info} - IP: {ip}"
    if content_id:
        message += f" - ID: {content_id}"
    if extra_info:
        message += f" - Info: {extra_info}"
    
    if content_type.lower() == 'article':
        blog_logger.info(message)
    elif content_type.lower() == 'commentaire':
        comments_logger.info(message)
    else:
        blog_logger.info(message)

def log_error(request, error, context=None):
    """Log des erreurs avec contexte"""
    user_info = get_user_info(request.user) if request and hasattr(request, 'user') else "N/A"
    ip = get_client_ip(request) if request else "N/A"
    
    message = f"[ERREUR] {str(error)} - Utilisateur: {user_info} - IP: {ip}"
    if context:
        message += f" - Contexte: {context}"
    
    logging.error(message, exc_info=True)

def log_view_access(logger_name='django'):
    """Décorateur pour logger l'accès aux vues"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            start_time = timezone.now()
            logger = logging.getLogger(logger_name)
            
            # Log de l'accès
            user_info = get_user_info(request.user)
            ip = get_client_ip(request)
            view_name = f"{view_func.__module__}.{view_func.__name__}"
            
            logger.info(f"[ACCÈS VUE] {view_name} - Utilisateur: {user_info} - IP: {ip} - Méthode: {request.method}")
            
            try:
                response = view_func(request, *args, **kwargs)
                
                # Calculer le temps de traitement
                processing_time = timezone.now() - start_time
                
                logger.info(f"[VUE TERMINÉE] {view_name} - Status: {getattr(response, 'status_code', 'N/A')} - Temps: {processing_time.total_seconds():.2f}s")
                
                return response
            except Exception as e:
                processing_time = timezone.now() - start_time
                logger.error(f"[ERREUR VUE] {view_name} - Erreur: {str(e)} - Temps: {processing_time.total_seconds():.2f}s", exc_info=True)
                raise
                
        return wrapper
    return decorator