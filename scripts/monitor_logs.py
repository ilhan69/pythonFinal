#!/usr/bin/env python3
"""
Script de surveillance automatique des logs
Peut être utilisé avec cron pour surveiller en continu
Usage: python scripts/monitor_logs.py
"""

import os
import sys
import django
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pythonFinal.settings')
django.setup()

from django.conf import settings
from scripts.analyze_logs import analyze_security_logs, analyze_auth_logs

class LogMonitor:
    def __init__(self):
        self.alerts_file = BASE_DIR / 'logs' / 'alerts.json'
        self.last_check_file = BASE_DIR / 'logs' / 'last_check.json'
        
    def load_last_check(self):
        """Charge le timestamp du dernier contrôle"""
        if self.last_check_file.exists():
            try:
                with open(self.last_check_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data.get('last_check', '2000-01-01T00:00:00'))
            except:
                pass
        return datetime.now()
    
    def save_last_check(self, timestamp=None):
        """Sauvegarde le timestamp du contrôle"""
        if timestamp is None:
            timestamp = datetime.now()
        
        data = {'last_check': timestamp.isoformat()}
        with open(self.last_check_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def check_security_alerts(self, hours=1):
        """Vérifie les alertes de sécurité"""
        security_events = analyze_security_logs(hours)
        auth_events = analyze_auth_logs(hours)
        
        alerts = []
        
        # Alertes de sécurité critiques
        failed_logins = len(security_events['failed_logins'])
        if failed_logins > 5:
            alerts.append({
                'type': 'CRITICAL',
                'message': f'🚨 {failed_logins} tentatives de connexion échouées en {hours}h',
                'details': security_events['failed_logins'][-3:]
            })
        
        suspicious_activities = len(security_events['suspicious_activity'])
        if suspicious_activities > 3:
            alerts.append({
                'type': 'WARNING',
                'message': f'⚠️ {suspicious_activities} activités suspectes détectées en {hours}h',
                'details': security_events['suspicious_activity'][-3:]
            })
        
        unauthorized_access = len(security_events['unauthorized_access'])
        if unauthorized_access > 2:
            alerts.append({
                'type': 'WARNING',
                'message': f'⚠️ {unauthorized_access} tentatives d\'accès non autorisées en {hours}h',
                'details': security_events['unauthorized_access'][-3:]
            })
        
        # Vérification du ratio échecs/succès de connexion
        if auth_events['failed_logins'] > 0 and auth_events['successful_logins'] > 0:
            ratio = auth_events['failed_logins'] / auth_events['successful_logins']
            if ratio > 0.3:  # Plus de 30% d'échecs
                alerts.append({
                    'type': 'WARNING',
                    'message': f'⚠️ Ratio élevé d\'échecs de connexion: {ratio:.1%} ({auth_events["failed_logins"]}/{auth_events["successful_logins"]})',
                    'details': []
                })
        
        # Suppression de comptes
        account_changes = len(security_events['account_changes'])
        if account_changes > 0:
            alerts.append({
                'type': 'INFO',
                'message': f'ℹ️ {account_changes} changement(s) de compte en {hours}h',
                'details': security_events['account_changes']
            })
        
        return alerts
    
    def send_alert_email(self, alerts):
        """Envoie une alerte par email (configuration à adapter)"""
        if not alerts:
            return
        
        # Configuration email (à adapter selon votre environnement)
        smtp_server = "localhost"  # Remplacez par votre serveur SMTP
        smtp_port = 587
        sender_email = "noreply@blog.local"
        receiver_emails = ["admin@blog.local"]  # Liste des administrateurs
        
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = ", ".join(receiver_emails)
            msg['Subject'] = f"[BLOG SECURITY] Alertes de sécurité - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Corps du message
            body = f"""
RAPPORT D'ALERTES DE SÉCURITÉ
=============================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
            
            for alert in alerts:
                body += f"\n{alert['type']}: {alert['message']}\n"
                if alert['details']:
                    body += "Détails:\n"
                    for detail in alert['details'][:3]:  # Limiter les détails
                        body += f"  - {detail[:100]}...\n"
                body += "\n"
            
            body += """
Veuillez vérifier les logs complets avec:
python manage.py analyze_logs --security-only

Cordialement,
Système de surveillance automatique
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Envoyer l'email (décommenté en production)
            # server = smtplib.SMTP(smtp_server, smtp_port)
            # server.starttls()
            # server.sendmail(sender_email, receiver_emails, msg.as_string())
            # server.quit()
            
            print(f"Alerte email préparée pour {len(alerts)} événement(s)")
            
        except Exception as e:
            print(f"Erreur lors de l'envoi d'email: {e}")
    
    def log_alert(self, alerts):
        """Enregistre les alertes dans un fichier dédié"""
        if not alerts:
            return
        
        alert_entry = {
            'timestamp': datetime.now().isoformat(),
            'alerts': alerts
        }
        
        # Charger les alertes existantes
        existing_alerts = []
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, 'r') as f:
                    existing_alerts = json.load(f)
            except:
                pass
        
        # Ajouter la nouvelle alerte
        existing_alerts.append(alert_entry)
        
        # Garder seulement les 100 dernières alertes
        existing_alerts = existing_alerts[-100:]
        
        # Sauvegarder
        with open(self.alerts_file, 'w') as f:
            json.dump(existing_alerts, f, indent=2, ensure_ascii=False)
    
    def run_check(self, hours=1, send_email=False):
        """Exécute une vérification complète"""
        print(f"🔍 Vérification des logs des {hours} dernière(s) heure(s)...")
        
        # Vérifier les alertes
        alerts = self.check_security_alerts(hours)
        
        if alerts:
            print(f"⚠️ {len(alerts)} alerte(s) détectée(s):")
            for alert in alerts:
                print(f"  - {alert['type']}: {alert['message']}")
            
            # Enregistrer les alertes
            self.log_alert(alerts)
            
            # Envoyer par email si demandé
            if send_email:
                self.send_alert_email(alerts)
        else:
            print("✅ Aucune alerte détectée")
        
        # Sauvegarder le timestamp
        self.save_last_check()
        
        return len(alerts)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Surveillance automatique des logs')
    parser.add_argument('--hours', type=int, default=1,
                        help='Nombre d\'heures à analyser (défaut: 1)')
    parser.add_argument('--email', action='store_true',
                        help='Envoyer les alertes par email')
    parser.add_argument('--daemon', action='store_true',
                        help='Mode démon (vérification continue)')
    
    args = parser.parse_args()
    
    monitor = LogMonitor()
    
    if args.daemon:
        print("🔄 Mode démon activé - Vérification toutes les heures")
        import time
        
        while True:
            try:
                monitor.run_check(args.hours, args.email)
                print(f"⏰ Prochaine vérification dans 1 heure...")
                time.sleep(3600)  # 1 heure
            except KeyboardInterrupt:
                print("\n👋 Arrêt du mode démon")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
                time.sleep(300)  # 5 minutes avant de réessayer
    else:
        alert_count = monitor.run_check(args.hours, args.email)
        exit(1 if alert_count > 0 else 0)

if __name__ == '__main__':
    main()