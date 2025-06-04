#!/usr/bin/env python3
"""
Script d'analyse des logs pour l'application pythonFinal
Usage: python manage.py runscript analyze_logs
"""

import os
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import django
from django.conf import settings

def analyze_log_file(log_file_path, hours=24):
    """Analyse un fichier de log pour les dernières heures spécifiées"""
    if not os.path.exists(log_file_path):
        return {}
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    stats = {
        'total_lines': 0,
        'recent_entries': 0,
        'errors': [],
        'warnings': [],
        'info': [],
        'debug': []
    }
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stats['total_lines'] += 1
                
                # Extraire la date de la ligne de log
                date_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if date_match:
                    try:
                        log_time = datetime.strptime(date_match.group(1), '%Y-%m-%d %H:%M:%S')
                        if log_time > cutoff_time:
                            stats['recent_entries'] += 1
                            
                            # Classer par niveau
                            if 'ERROR' in line:
                                stats['errors'].append(line.strip())
                            elif 'WARNING' in line:
                                stats['warnings'].append(line.strip())
                            elif 'INFO' in line:
                                stats['info'].append(line.strip())
                            elif 'DEBUG' in line:
                                stats['debug'].append(line.strip())
                    except ValueError:
                        continue
    except Exception as e:
        print(f"Erreur lors de la lecture de {log_file_path}: {e}")
    
    return stats

def analyze_security_logs(hours=24):
    """Analyse spécifique des logs de sécurité"""
    security_log = settings.BASE_DIR / 'logs' / 'security.log'
    stats = analyze_log_file(security_log, hours)
    
    security_events = {
        'failed_logins': [],
        'unauthorized_access': [],
        'suspicious_activity': [],
        'account_changes': []
    }
    
    for entry in stats['warnings'] + stats['errors']:
        if 'ÉCHEC CONNEXION' in entry or 'TENTATIVE_CONNEXION_ECHOUEE' in entry:
            security_events['failed_logins'].append(entry)
        elif 'ACCÈS NON AUTORISÉ' in entry or 'ACCÈS REFUSÉ' in entry:
            security_events['unauthorized_access'].append(entry)
        elif 'SCAN SUSPECT' in entry or 'TENTATIVE_' in entry:
            security_events['suspicious_activity'].append(entry)
        elif 'SUPPRESSION_COMPTE' in entry or 'DESACTIVATION_COMPTE' in entry:
            security_events['account_changes'].append(entry)
    
    return security_events

def analyze_auth_logs(hours=24):
    """Analyse des logs d'authentification"""
    auth_log = settings.BASE_DIR / 'logs' / 'auth.log'
    stats = analyze_log_file(auth_log, hours)
    
    auth_events = {
        'successful_logins': 0,
        'failed_logins': 0,
        'registrations': 0,
        'password_changes': 0,
        'profile_updates': 0
    }
    
    for entry in stats['info'] + stats['warnings']:
        if 'CONNEXION] SUCCÈS' in entry:
            auth_events['successful_logins'] += 1
        elif 'CONNEXION] ÉCHEC' in entry:
            auth_events['failed_logins'] += 1
        elif 'INSCRIPTION] SUCCÈS' in entry:
            auth_events['registrations'] += 1
        elif 'CHANGEMENT_MOT_DE_PASSE' in entry:
            auth_events['password_changes'] += 1
        elif 'MODIFICATION_PROFIL' in entry:
            auth_events['profile_updates'] += 1
    
    return auth_events

def analyze_admin_logs(hours=24):
    """Analyse des logs d'administration"""
    admin_log = settings.BASE_DIR / 'logs' / 'admin.log'
    stats = analyze_log_file(admin_log, hours)
    
    admin_events = {
        'user_management': 0,
        'content_management': 0,
        'category_management': 0,
        'tag_management': 0,
        'access_checks': 0
    }
    
    for entry in stats['info']:
        if 'UTILISATEUR' in entry:
            admin_events['user_management'] += 1
        elif 'CATEGORIE' in entry:
            admin_events['category_management'] += 1
        elif 'TAG' in entry:
            admin_events['tag_management'] += 1
        elif 'ACCES_GESTION' in entry:
            admin_events['access_checks'] += 1
        else:
            admin_events['content_management'] += 1
    
    return admin_events

def get_top_ips_from_logs(hours=24):
    """Extrait les adresses IP les plus fréquentes des logs"""
    logs_dir = settings.BASE_DIR / 'logs'
    ip_counter = Counter()
    
    for log_file in logs_dir.glob('*.log'):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # Rechercher les IPs dans les logs
                    ip_matches = re.findall(r'IP: (\d+\.\d+\.\d+\.\d+)', line)
                    for ip in ip_matches:
                        ip_counter[ip] += 1
        except Exception:
            continue
    
    return ip_counter.most_common(10)

def generate_report(hours=24):
    """Génère un rapport complet d'analyse des logs"""
    print(f"\n{'='*60}")
    print(f"RAPPORT D'ANALYSE DES LOGS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Période analysée: {hours} dernières heures")
    print(f"{'='*60}")
    
    # Analyse de sécurité
    security_events = analyze_security_logs(hours)
    print(f"\n🔒 ÉVÉNEMENTS DE SÉCURITÉ:")
    print(f"   Tentatives de connexion échouées: {len(security_events['failed_logins'])}")
    print(f"   Accès non autorisés: {len(security_events['unauthorized_access'])}")
    print(f"   Activités suspectes: {len(security_events['suspicious_activity'])}")
    print(f"   Changements de comptes: {len(security_events['account_changes'])}")
    
    # Analyse d'authentification
    auth_events = analyze_auth_logs(hours)
    print(f"\n👤 ÉVÉNEMENTS D'AUTHENTIFICATION:")
    print(f"   Connexions réussies: {auth_events['successful_logins']}")
    print(f"   Connexions échouées: {auth_events['failed_logins']}")
    print(f"   Nouvelles inscriptions: {auth_events['registrations']}")
    print(f"   Changements de mot de passe: {auth_events['password_changes']}")
    print(f"   Mises à jour de profil: {auth_events['profile_updates']}")
    
    # Analyse d'administration
    admin_events = analyze_admin_logs(hours)
    print(f"\n⚙️  ÉVÉNEMENTS D'ADMINISTRATION:")
    print(f"   Gestion des utilisateurs: {admin_events['user_management']}")
    print(f"   Gestion du contenu: {admin_events['content_management']}")
    print(f"   Gestion des catégories: {admin_events['category_management']}")
    print(f"   Gestion des tags: {admin_events['tag_management']}")
    print(f"   Vérifications d'accès: {admin_events['access_checks']}")
    
    # Top IPs
    top_ips = get_top_ips_from_logs(hours)
    if top_ips:
        print(f"\n🌐 TOP 5 ADRESSES IP:")
        for ip, count in top_ips[:5]:
            print(f"   {ip}: {count} requêtes")
    
    # Alertes de sécurité
    print(f"\n⚠️  ALERTES:")
    if len(security_events['failed_logins']) > 10:
        print(f"   🚨 ATTENTION: {len(security_events['failed_logins'])} tentatives de connexion échouées!")
    
    if len(security_events['suspicious_activity']) > 5:
        print(f"   🚨 ATTENTION: {len(security_events['suspicious_activity'])} activités suspectes détectées!")
    
    if auth_events['failed_logins'] > auth_events['successful_logins'] * 0.5:
        print(f"   🚨 ATTENTION: Ratio élevé d'échecs de connexion!")
    
    # Analyse des erreurs
    error_log = settings.BASE_DIR / 'logs' / 'errors.log'
    error_stats = analyze_log_file(error_log, hours)
    if error_stats['recent_entries'] > 0:
        print(f"\n❌ ERREURS RÉCENTES:")
        print(f"   Total: {error_stats['recent_entries']}")
        print(f"   Erreurs: {len(error_stats['errors'])}")
        print(f"   Avertissements: {len(error_stats['warnings'])}")
        
        # Afficher les 3 dernières erreurs
        if error_stats['errors']:
            print(f"\n   Dernières erreurs:")
            for error in error_stats['errors'][-3:]:
                print(f"   - {error[:100]}...")
    
    print(f"\n{'='*60}")

def run():
    """Point d'entrée du script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyse des logs de l\'application')
    parser.add_argument('--hours', type=int, default=24, 
                        help='Nombre d\'heures à analyser (défaut: 24)')
    parser.add_argument('--security-only', action='store_true',
                        help='Afficher uniquement les événements de sécurité')
    
    args = parser.parse_args()
    
    if args.security_only:
        security_events = analyze_security_logs(args.hours)
        print(f"\n🔒 ÉVÉNEMENTS DE SÉCURITÉ ({args.hours}h):")
        
        if security_events['failed_logins']:
            print(f"\nTentatives de connexion échouées ({len(security_events['failed_logins'])}):")
            for event in security_events['failed_logins'][-5:]:
                print(f"  - {event}")
        
        if security_events['suspicious_activity']:
            print(f"\nActivités suspectes ({len(security_events['suspicious_activity'])}):")
            for event in security_events['suspicious_activity'][-5:]:
                print(f"  - {event}")
    else:
        generate_report(args.hours)

if __name__ == '__main__':
    run()