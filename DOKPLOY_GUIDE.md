# Guide de Déploiement Dokploy (Usage Interne)

Ce document décrit la procédure pour déployer EDRefCard v2.0 sur un VPS géré par Dokploy via Docker Compose.

## Prérequis

1. Un VPS avec Dokploy installé
2. Un domaine configuré pointant vers le VPS (ex: `edrefcard.info`)
3. Accès au panel Dokploy

## Configuration Dokploy

### 1. Création de l'application

1. Dans le dashboard Dokploy, aller dans votre projet.
2. Cliquer sur **"Create Service"** > **"Docker Compose"**.
3. Nommer le service `edrefcard`.

### 2. Configuration Docker Compose

Copier le contenu suivant dans l'onglet **"Docker Compose"** :

```yaml
version: '3.8'

services:
  app:
    image: edrefcard  # Utilisez votre image buildée ou build context
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
      # Credentials Admin (CHANGEZ CES VALEURS EN PROD !)
      - EDREFCARD_ADMIN_USER=${ADMIN_USER}
      - EDREFCARD_ADMIN_PASS=${ADMIN_PASS}
      - FLASK_SECRET_KEY=${FLASK_SECRET}
    volumes:
      - edrefcard_configs:/app/configs
      - edrefcard_data:/app/data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.edrefcard.rule=Host(`edrefcard.info`)"
      - "traefik.http.routers.edrefcard.entrypoints=websecure"
      - "traefik.http.routers.edrefcard.tls.certresolver=letsencrypt"
      - "traefik.http.services.edrefcard.loadbalancer.server.port=8000"

volumes:
  edrefcard_configs:
  edrefcard_data:
```

### 3. Variables d'environnement

Dans l'onglet **"Environment"**, ajouter les secrets :

```env
ADMIN_USER=admin
ADMIN_PASS=votre_mot_de_passe_tres_secr3t
FLASK_SECRET=une_cle_flask_longue_et_aleatoire
```

### 4. Build et Déploiement

1. Connecter le repository GitHub (onglet **"Source"**).
2. Sélectionner la branche `main` (ou `master`).
3. Activer **"Auto Deploy"** pour déployer à chaque push.
4. Cliquer sur **"Deploy"**.

## Gestion des Données

### Volumes Persistants

L'application utilise deux volumes importants :
- `edrefcard_configs`: Contient les images générées et fichiers .binds originaux.
- `edrefcard_data`: Contient la base de données SQLite `edrefcard.db`.

### Backups

Il est recommandé de configurer un backup automatique via Dokploy pour ces volumes, ou d'utiliser un script cron sur le VPS pour copier `/app/data/edrefcard.db`.

## Troubleshooting

### Logs

Pour voir les logs de l'application :
Aller dans l'onglet **"Logs"** du service `edrefcard`.

### Shell

Pour accéder au conteneur (ex: pour lancer une migration manuelle) :
1. Onglet **"Terminal"**
2. Commande :
   ```bash
   /bin/bash
   # ou
   flask --app app routes
   ```
