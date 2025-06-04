from django import forms
from .models import Article, Category, Tag
from ckeditor.widgets import CKEditorWidget

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'slug', 'couleur', 'icone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Généré automatiquement si vide'
            }),
            'couleur': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'icone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ex: fas fa-tag, bi bi-bookmark, etc.'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre le slug optionnel dans le formulaire
        self.fields['slug'].required = False

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'slug', 'couleur']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Généré automatiquement si vide'
            }),
            'couleur': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#6c757d'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre le slug optionnel dans le formulaire
        self.fields['slug'].required = False

class PostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Tags'
    )

    class Meta:
        model = Article
        fields = [
            'title', 'slug', 'content', 'excerpt', 'cover_image', 
            'category', 'tags', 'status', 'meta_title', 'meta_description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Généré automatiquement si vide'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Résumé de l\'article (généré automatiquement si vide)',
                'maxlength': 300
            }),
            'cover_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre SEO (généré automatiquement si vide)',
                'maxlength': 60
            }),
            'meta_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Description SEO (générée automatiquement si vide)',
                'maxlength': 160
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organiser les tags par ordre alphabétique
        self.fields['tags'].queryset = Tag.objects.all().order_by('name')
        # Rendre certains champs optionnels dans le formulaire
        self.fields['slug'].required = False
        self.fields['excerpt'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
