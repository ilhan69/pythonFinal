from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from .models import Like, Share, View

# Create your views here.

@require_POST
@login_required
def like_object(request):
    """Vue pour gérer les likes d'objets via AJAX"""
    content_type_id = request.POST.get('content_type_id')
    object_id = request.POST.get('object_id')
    
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
        
        # Vérifier si l'utilisateur a déjà liké cet objet
        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        )
        
        if created:
            # Nouveau like
            liked = True
            message = _('Contenu liké avec succès!')
        else:
            # Unlike - supprimer le like existant
            like.delete()
            liked = False
            message = _('Like retiré avec succès!')
        
        # Mettre à jour le compteur sur l'objet
        likes_count = Like.objects.filter(
            content_type=content_type, 
            object_id=object_id
        ).count()
        
        # Mettre à jour le compteur dans l'objet si il a un attribut likes_count
        if hasattr(content_object, 'likes_count'):
            content_object.likes_count = likes_count
            content_object.save(update_fields=['likes_count'])
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': likes_count,
            'message': str(message)
        })
        
    except (ContentType.DoesNotExist, content_type.model_class().DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': str(_('Objet non trouvé.'))
        })

@require_POST  
def share_object(request):
    """Vue pour gérer les partages d'objets via AJAX"""
    content_type_id = request.POST.get('content_type_id')
    object_id = request.POST.get('object_id')
    
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
        
        # Récupérer l'adresse IP et le user agent
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Créer un enregistrement de partage
        share = Share.objects.create(
            user=request.user if request.user.is_authenticated else None,
            content_type=content_type,
            object_id=object_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Compter les partages
        shares_count = Share.objects.filter(
            content_type=content_type, 
            object_id=object_id
        ).count()
        
        # Mettre à jour le compteur dans l'objet si il a un attribut shares_count
        if hasattr(content_object, 'shares_count'):
            content_object.shares_count = shares_count
            content_object.save(update_fields=['shares_count'])
        
        return JsonResponse({
            'success': True,
            'shares_count': shares_count,
            'message': str(_('Contenu partagé avec succès!'))
        })
        
    except (ContentType.DoesNotExist, content_type.model_class().DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': str(_('Objet non trouvé.'))
        })

def record_view(request):
    """Vue pour enregistrer une vue d'objet"""
    content_type_id = request.POST.get('content_type_id')
    object_id = request.POST.get('object_id')
    
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
        
        # Récupérer l'adresse IP et le user agent
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Créer un enregistrement de vue
        view = View.objects.create(
            user=request.user if request.user.is_authenticated else None,
            content_type=content_type,
            object_id=object_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Compter les vues
        views_count = View.objects.filter(
            content_type=content_type, 
            object_id=object_id
        ).count()
        
        # Mettre à jour le compteur dans l'objet si il a un attribut views_count
        if hasattr(content_object, 'views_count'):
            content_object.views_count = views_count
            content_object.save(update_fields=['views_count'])
        
        return JsonResponse({
            'success': True,
            'views_count': views_count
        })
        
    except (ContentType.DoesNotExist, content_type.model_class().DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': str(_('Objet non trouvé.'))
        })
