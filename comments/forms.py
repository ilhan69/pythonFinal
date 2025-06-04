from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Comment

class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Écrivez votre commentaire...'),
            'class': 'form-control'
        }),
        label=_('Commentaire')
    )

    class Meta:
        model = Comment
        fields = ('content',)