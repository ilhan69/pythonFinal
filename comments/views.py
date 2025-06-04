from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from .models import Comment
from .forms import CommentForm
from users.decorators import comment_owner_required

@login_required
@require_POST
def add_comment(request):
    """Ajouter un commentaire via AJAX"""
    form = CommentForm(request.POST)
    if form.is_valid():
        content_type_id = request.POST.get('content_type_id')
        object_id = request.POST.get('object_id')
        
        try:
            content_type = ContentType.objects.get(id=content_type_id)
            
            comment = form.save(commit=False)
            comment.author = request.user
            comment.content_type = content_type
            comment.object_id = object_id
            comment.save()
            
            return JsonResponse({
                'success': True,
                'message': str(_('Commentaire ajouté avec succès !')),
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'author': comment.author.username,
                    'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
                }
            })
        except ContentType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': str(_('Erreur lors de l\'ajout du commentaire.'))
            })
    else:
        return JsonResponse({
            'success': False,
            'message': str(_('Veuillez corriger les erreurs dans le formulaire.')),
            'errors': form.errors
        })

@comment_owner_required
def delete_comment(request, comment_id):
    """Supprimer un commentaire"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Vérification supplémentaire des permissions
    if not request.user.can_delete_comment(comment):
        messages.error(request, _('Vous n\'avez pas le droit de supprimer ce commentaire.'))
        return redirect('blog:home')
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, _('Commentaire supprimé avec succès !'))
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@comment_owner_required
def edit_comment(request, comment_id):
    """Modifier un commentaire"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Vérification supplémentaire des permissions
    if not request.user.can_edit_comment(comment):
        messages.error(request, _('Vous n\'avez pas le droit de modifier ce commentaire.'))
        return redirect('blog:home')
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': str(_('Commentaire modifié avec succès !')),
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'updated_at': comment.updated_at.strftime('%d/%m/%Y %H:%M')
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': str(_('Veuillez corriger les erreurs dans le formulaire.')),
                'errors': form.errors
            })
    
    return JsonResponse({'success': False})
