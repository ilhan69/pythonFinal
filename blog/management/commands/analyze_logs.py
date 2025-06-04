from django.core.management.base import BaseCommand
from django.conf import settings
import sys
import os

# Ajouter le répertoire scripts au path pour importer notre analyseur
scripts_dir = settings.BASE_DIR / 'scripts'
sys.path.insert(0, str(scripts_dir))

from analyze_logs import generate_report, analyze_security_logs

class Command(BaseCommand):
    help = 'Analyse les logs de l\'application et génère un rapport'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Nombre d\'heures à analyser (défaut: 24)'
        )
        parser.add_argument(
            '--security-only',
            action='store_true',
            help='Afficher uniquement les événements de sécurité'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Exporter le rapport vers un fichier'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        security_only = options['security_only']
        export_file = options.get('export')

        # Capturer la sortie si on doit l'exporter
        if export_file:
            import io
            from contextlib import redirect_stdout
            
            output = io.StringIO()
            with redirect_stdout(output):
                if security_only:
                    self._display_security_only(hours)
                else:
                    generate_report(hours)
            
            # Écrire dans le fichier
            try:
                with open(export_file, 'w', encoding='utf-8') as f:
                    f.write(output.getvalue())
                self.stdout.write(
                    self.style.SUCCESS(f'Rapport exporté vers {export_file}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur lors de l\'export: {e}')
                )
        else:
            if security_only:
                self._display_security_only(hours)
            else:
                generate_report(hours)

    def _display_security_only(self, hours):
        """Affiche uniquement les événements de sécurité"""
        security_events = analyze_security_logs(hours)
        
        self.stdout.write(f"\n🔒 ÉVÉNEMENTS DE SÉCURITÉ ({hours}h):")
        
        if security_events['failed_logins']:
            self.stdout.write(f"\nTentatives de connexion échouées ({len(security_events['failed_logins'])}):")
            for event in security_events['failed_logins'][-5:]:
                self.stdout.write(f"  - {event}")
        
        if security_events['unauthorized_access']:
            self.stdout.write(f"\nAccès non autorisés ({len(security_events['unauthorized_access'])}):")
            for event in security_events['unauthorized_access'][-5:]:
                self.stdout.write(f"  - {event}")
        
        if security_events['suspicious_activity']:
            self.stdout.write(f"\nActivités suspectes ({len(security_events['suspicious_activity'])}):")
            for event in security_events['suspicious_activity'][-5:]:
                self.stdout.write(f"  - {event}")
        
        if security_events['account_changes']:
            self.stdout.write(f"\nChangements de comptes ({len(security_events['account_changes'])}):")
            for event in security_events['account_changes'][-5:]:
                self.stdout.write(f"  - {event}")
        
        # Alertes
        total_events = sum(len(events) for events in security_events.values())
        if total_events == 0:
            self.stdout.write(
                self.style.SUCCESS("\n✅ Aucun événement de sécurité détecté.")
            )
        elif len(security_events['failed_logins']) > 10:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️ ATTENTION: {len(security_events['failed_logins'])} tentatives de connexion échouées!")
            )
        elif len(security_events['suspicious_activity']) > 5:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️ ATTENTION: {len(security_events['suspicious_activity'])} activités suspectes!")
            )