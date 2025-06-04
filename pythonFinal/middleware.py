"""
Middleware de logging de sécurité pour l'application pythonFinal
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from pythonFinal.logging_utils import log_security_event, get_client_ip

security_logger = logging.getLogger('security')

class SecurityLoggingMiddleware(MiddlewareMixin):
    """Middleware pour capturer les événements de sécurité"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Traitement de la requête entrante"""
        # Détecter les tentatives d'accès à des URLs sensibles
        sensitive_paths = [
            '/admin/',
            '/users/manage/',
            '/api/',
        ]
        
        if any(request.path.startswith(path) for path in sensitive_paths):
            if not request.user.is_authenticated:
                security_logger.warning(
                    f"[ACCÈS NON AUTORISÉ] Tentative d'accès à {request.path} "
                    f"- IP: {get_client_ip(request)} "
                    f"- User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')[:100]}"
                )
        
        return None
    
    def process_response(self, request, response):
        """Traitement de la réponse"""
        # Logger les erreurs 403 et 404 pour détecter les tentatives malveillantes
        if response.status_code == 403:
            security_logger.warning(
                f"[ACCÈS REFUSÉ] 403 sur {request.path} "
                f"- Utilisateur: {getattr(request.user, 'username', 'Anonymous')} "
                f"- IP: {get_client_ip(request)}"
            )
        elif response.status_code == 404 and any(suspicious in request.path.lower() for suspicious in 
                                                ['.php', '.asp', 'wp-admin', 'phpmyadmin', '.env']):
            security_logger.warning(
                f"[SCAN SUSPECT] 404 sur chemin suspect {request.path} "
                f"- IP: {get_client_ip(request)} "
                f"- User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')[:100]}"
            )
        
        return response

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Signal handler pour les échecs de connexion"""
    username = credentials.get('username', 'Unknown')
    ip = get_client_ip(request)
    
    security_logger.warning(
        f"[ÉCHEC CONNEXION] Tentative échouée pour {username} "
        f"- IP: {ip} "
        f"- User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')[:100]}"
    )