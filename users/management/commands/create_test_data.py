from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from blog.models import Article, Category, Tag
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée des données de test avec différents rôles d\'utilisateurs'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Création des données de test...'))

        # Créer un administrateur
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'bio': 'Administrateur du blog'
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Administrateur créé: {admin_user.username}'))

        # Créer des auteurs
        auteur_users = []
        for i in range(1, 4):
            auteur, created = User.objects.get_or_create(
                username=f'auteur{i}',
                defaults={
                    'email': f'auteur{i}@example.com',
                    'role': 'auteur',
                    'first_name': f'Auteur',
                    'last_name': f'{i}',
                    'bio': f'Auteur passionné d\'écriture #{i}'
                }
            )
            if created:
                auteur.set_password('auteur123')
                auteur.save()
                auteur_users.append(auteur)
                self.stdout.write(self.style.SUCCESS(f'Auteur créé: {auteur.username}'))

        # Créer des visiteurs
        visiteur_users = []
        for i in range(1, 6):
            visiteur, created = User.objects.get_or_create(
                username=f'visiteur{i}',
                defaults={
                    'email': f'visiteur{i}@example.com',
                    'role': 'visiteur',
                    'first_name': f'Visiteur',
                    'last_name': f'{i}',
                    'bio': f'Lecteur assidu du blog #{i}'
                }
            )
            if created:
                visiteur.set_password('visiteur123')
                visiteur.save()
                visiteur_users.append(visiteur)
                self.stdout.write(self.style.SUCCESS(f'Visiteur créé: {visiteur.username}'))

        # Créer des catégories
        categories = []
        category_data = [
            ('Technologie', 'Articles sur la technologie et l\'innovation'),
            ('Science', 'Découvertes scientifiques et recherches'),
            ('Culture', 'Art, littérature et événements culturels'),
            ('Sport', 'Actualités sportives et compétitions'),
            ('Voyage', 'Guides de voyage et découvertes')
        ]
        for name, description in category_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            categories.append(category)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Catégorie créée: {category.name}'))

        # Créer des tags
        tags = []
        tag_names = ['python', 'django', 'web', 'frontend', 'backend', 'api', 'mobile', 'design']
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            tags.append(tag)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Tag créé: {tag.name}'))

        # Créer des articles pour les auteurs
        if auteur_users and categories and tags:
            import random
            article_titles = [
                'Introduction au développement web',
                'Les bonnes pratiques en Python',
                'Django vs Flask: comparaison',
                'L\'avenir de l\'intelligence artificielle',
                'Optimisation des performances web',
                'Guide du développeur débutant',
                'Sécurité des applications web',
                'Les frameworks JavaScript modernes'
            ]

            for i, title in enumerate(article_titles):
                if i < len(auteur_users):
                    author = auteur_users[i % len(auteur_users)]
                else:
                    author = random.choice(auteur_users)
                
                article, created = Article.objects.get_or_create(
                    title=title,
                    defaults={
                        'author': author,
                        'category': random.choice(categories),
                        'content': f'<p>Contenu détaillé de l\'article "{title}".</p><p>Ceci est un exemple d\'article créé par {author.username} pour démontrer le système de rôles du blog.</p><p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>',
                        'excerpt': f'Résumé de l\'article "{title}" - Un guide complet pour les développeurs.',
                        'status': 'published',
                        'views_count': random.randint(10, 1000),
                        'likes_count': random.randint(0, 50),
                        'shares_count': random.randint(0, 20)
                    }
                )
                if created:
                    # Ajouter des tags aléatoires
                    article.tags.set(random.sample(tags, random.randint(1, 3)))
                    self.stdout.write(self.style.SUCCESS(f'Article créé: {article.title} par {author.username}'))

        self.stdout.write(
            self.style.SUCCESS(
                '\n' + '='*60 + '\n'
                'DONNÉES DE TEST CRÉÉES AVEC SUCCÈS!\n'
                '='*60 + '\n'
                'Comptes utilisateurs disponibles:\n'
                '• Admin: admin / admin123 (Accès complet)\n'
                '• Auteurs: auteur1-3 / auteur123 (Création d\'articles)\n'
                '• Visiteurs: visiteur1-5 / visiteur123 (Lecture seule)\n'
                '='*60
            )
        )