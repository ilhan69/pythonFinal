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
from pythonFinal.logging_utils import (
    log_content_action, log_error, log_security_event, log_view_access
)

@login_required
@require_POST
@log_view_access('comments')
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
            
            # Log de l'ajout de commentaire
            target_object = f"{content_type.model} ID:{object_id}"
            log_content_action(request, 'CREATION', 'Commentaire', comment.id,
                             f"Sur: {target_object}, Contenu: {comment.content[:50]}...")
            
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
            log_error(request, f"ContentType inexistant: ID {content_type_id}", 
                     "Erreur lors de l'ajout de commentaire")
            return JsonResponse({
                'success': False,
                'message': str(_('Erreur lors de l\'ajout du commentaire.'))
            })
        except Exception as e:
            log_error(request, e, "Erreur lors de l'ajout de commentaire")
            return JsonResponse({
                'success': False,
                'message': str(_('Une erreur est survenue.'))
            })
    else:
        # Log des erreurs de validation
        log_content_action(request, 'ECHEC_CREATION', 'Commentaire', None,
                         f"Erreurs de validation: {form.errors}")
        return JsonResponse({
            'success': False,
            'message': str(_('Veuillez corriger les erreurs dans le formulaire.')),
            'errors': form.errors
        })

@comment_owner_required
@log_view_access('comments')
def delete_comment(request, comment_id):
    """Supprimer un commentaire"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Vérification supplémentaire des permissions
    if not request.user.can_delete_comment(comment):
        log_security_event(request, 'TENTATIVE_SUPPRESSION_COMMENTAIRE_NON_AUTORISEE', 'WARNING',
                         f"Commentaire ID: {comment_id}, Auteur: {comment.author.username}")
        messages.error(request, _('Vous n\'avez pas le droit de supprimer ce commentaire.'))
        return redirect('blog:home')
    
    if request.method == 'POST':
        try:
            comment_content = comment.content[:50] + "..." if len(comment.content) > 50 else comment.content
            target_object = f"{comment.content_type.model} ID:{comment.object_id}"
            
            comment.delete()
            
            # Log de la suppression de commentaire
            log_content_action(request, 'SUPPRESSION', 'Commentaire', comment_id,
                             f"Contenu supprimé: {comment_content}, Sur: {target_object}")
            log_security_event(request, 'SUPPRESSION_COMMENTAIRE', 'INFO',
                             f"Commentaire supprimé (ID: {comment_id}) sur {target_object}")
            
            messages.success(request, _('Commentaire supprimé avec succès !'))
            return JsonResponse({'success': True})
        except Exception as e:
            log_error(request, e, f"Erreur lors de la suppression du commentaire {comment_id}")
            return JsonResponse({'success': False, 'message': str(_('Erreur lors de la suppression.'))})
    
    return JsonResponse({'success': False})

@comment_owner_required
@log_view_access('comments')
def edit_comment(request, comment_id):
    """Modifier un commentaire"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Vérification supplémentaire des permissions
    if not request.user.can_edit_comment(comment):
        log_security_event(request, 'TENTATIVE_MODIFICATION_COMMENTAIRE_NON_AUTORISEE', 'WARNING',
                         f"Commentaire ID: {comment_id}, Auteur: {comment.author.username}")
        messages.error(request, _('Vous n\'avez pas le droit de modifier ce commentaire.'))
        return redirect('blog:home')
    
    if request.method == 'POST':
        old_content = comment.content
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            try:
                form.save()
                
                # Log de la modification de commentaire
                target_object = f"{comment.content_type.model} ID:{comment.object_id}"
                log_content_action(request, 'MODIFICATION', 'Commentaire', comment_id,
                                 f"Sur: {target_object}, Ancien: {old_content[:30]}..., Nouveau: {comment.content[:30]}...")
                
                return JsonResponse({
                    'success': True,
                    'message': str(_('Commentaire modifié avec succès !')),
                    'comment': {
                        'id': comment.id,
                        'content': comment.content,
                        'updated_at': comment.updated_at.strftime('%d/%m/%Y %H:%M')
                    }
                })
            except Exception as e:
                log_error(request, e, f"Erreur lors de la modification du commentaire {comment_id}")
                return JsonResponse({
                    'success': False,
                    'message': str(_('Une erreur est survenue lors de la modification.'))
                })
        else:
            # Log des erreurs de modification
            log_content_action(request, 'ECHEC_MODIFICATION', 'Commentaire', comment_id,
                             f"Erreurs de validation: {form.errors}")
            return JsonResponse({
                'success': False,
                'message': str(_('Veuillez corriger les erreurs dans le formulaire.')),
                'errors': form.errors
            })
    
    return JsonResponse({'success': False})
