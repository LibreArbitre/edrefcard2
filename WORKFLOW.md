# EDRefCard2 - Guide de Workflow & Collaboration

> **Note** : Document personnel - Ne pas commiter

## 📋 Architecture des Branches

```
upstream (brammmers/edrefcard2)
├── main (branche officielle)
└── librearbitre-pull-request (branche de travail temporaire)

origin (LibreArbitre/edrefcard2 - votre fork)
├── main (production - déploie sur edrefcard2.l0l.fr)
└── dev (staging - déploie sur edrefcard2-dev.l0l.fr)

local (votre machine)
└── main (UNIQUE branche locale - workflow simplifié)
```

---

## 🔄 Workflow de Développement Simplifié

### Principe
Vous travaillez **toujours sur `local/main`** et poussez vers les branches remote selon vos besoins.

```bash
# 1. Développer localement
git checkout main  # Toujours sur main
# ... coder, tester localement si besoin ...
git add .
git commit -m "feat: ma fonctionnalité"

# 2. Tester en STAGING (avant prod)
git push origin main:dev
# ↳ Pousse local/main vers origin/dev
# ↳ Dokploy auto-déploie sur https://edrefcard2-dev.l0l.fr

# 3. Vérifier en staging
# Tester sur https://edrefcard2-dev.l0l.fr

# 4. Si OK, déployer en PRODUCTION
git push origin main
# ↳ Pousse local/main vers origin/main
# ↳ Dokploy auto-déploie sur https://edrefcard2.l0l.fr
```

### Schéma du workflow

```
┌────────────────────────────────────────────────┐
│  VOTRE MACHINE                                 │
│                                                │
│  main (locale) ────┐                          │
│   ↑ commit         │                          │
│   │                │                          │
└───┼────────────────┼──────────────────────────┘
    │                │
    │                ├─┐ git push origin main:dev
    │                │ │
    │                │ └──► origin/dev (staging)
    │                │      └─ auto-deploy
    │                │         edrefcard2-dev.l0l.fr
    │                │
    │                └──► git push origin main
    │                     │
    │                     └──► origin/main (prod)
    │                          └─ auto-deploy
    test local                    edrefcard2.l0l.fr
  (optionnel)
```

---

## 🚀 Commandes Rapides

### Développement normal

```bash
# Coder et commiter
git add .
git commit -m "feat: description"

# Test staging
git push origin main:dev
# ➡️ Tester sur edrefcard2-dev.l0l.fr

# Si OK, push prod
git push origin main
# ➡️ Déploie sur edrefcard2.l0l.fr
```

### Expérimentation risquée (optionnel)

```bash
# Créer une branche temporaire
git checkout -b experiment
# ... coder ...

# Tester en staging
git push origin experiment:dev

# Si OK: merger dans main
git checkout main
git merge experiment
git branch -d experiment
git push origin main

# Si KO: abandonner
git checkout main
git branch -D experiment
```

---

## 🌐 Déploiement Dokploy

### Configuration

**Projet 1 : Production**
- Nom : `edrefcard-prod`
- Repo : `LibreArbitre/edrefcard2`
- Branche : `main`
- Compose : `docker-compose.prod.yml`
- URL : https://edrefcard2.l0l.fr

**Projet 2 : Staging/Dev**
- Nom : `edrefcard-dev`
- Repo : `LibreArbitre/edrefcard2`
- Branche : `dev`
- Compose : `docker-compose.prod.yml`
- URL : https://edrefcard2-dev.l0l.fr

### Pourquoi 2 projets Dokploy ?
- ✅ Tester en conditions réelles avant prod
- ✅ Déploiements indépendants
- ✅ Rollback facile
- ✅ Bases de données séparées

### ⚠️ Important : docker-compose.prod.yml

**PAS de mapping de ports** dans `docker-compose.prod.yml` !

Dokploy utilise Traefik qui gère automatiquement le routing. Le fichier doit ressembler à :

```yaml
services:
  edrefcard:
    build: .
    # PAS DE "ports:" - Traefik gère tout
    environment:
      - APP_URL  # Important : URL différente par projet
```

**Dans Dokploy**, configurez :
- Projet prod : Variable `APP_URL=https://edrefcard2.l0l.fr`
- Projet dev : Variable `APP_URL=https://edrefcard2-dev.l0l.fr`

### 📁 Fichiers docker-compose

| Fichier | Usage | Ports ? |
|---------|-------|---------|
| `docker-compose.yml` | Dev local | ✅ `8080:8000` |
| `docker-compose.prod.yml` | Dokploy (prod + staging) | ❌ Pas de ports |
| `docker-compose.multi.yml` | Multi-env local (optionnel) | ❌ Pas de ports |

---

## 📝 Conventions de Commits

```
feat: nouvelle fonctionnalité
fix: correction de bug
docs: documentation
refactor: refactoring code
chore: tâches de maintenance
perf: optimisation performance
security: amélioration sécurité
```

---

## 🔧 Fichiers Locaux (non commités)

Ces fichiers existent localement mais ne sont **pas** versionnés :

| Fichier | Usage | Gitignore |
|---------|-------|-----------|
| `docker-compose.multi.yml` | Config multi-env (si besoin local) | ✅ Oui |
| `DOKPLOY_GUIDE.md` | Guide perso Dokploy | ✅ Oui |
| `WORKFLOW.md` | Ce fichier | ✅ Oui |
| `.env` | Variables d'environnement | ✅ Oui |

---

## 🎯 PR vers Upstream - Checklist

Avant de créer une PR vers `brammmers/edrefcard2` :

- [ ] Code testé en staging (origin/dev)
- [ ] Code testé en prod (origin/main) si critique
- [ ] Aucun fichier de données utilisateur (`configs/`, `*.db`)
- [ ] Documentation à jour
- [ ] Commit squashé avec message clair
- [ ] Branche basée sur `upstream/librearbitre-pull-request`

### Commandes PR

```bash
# 1. Créer branche PR propre
git checkout -b pr-description upstream/librearbitre-pull-request

# 2. Copier code depuis main (sélectif)
git checkout main -- www/app.py www/web.py README.md
# (exclure configs/, *.db, fichiers personnels)

# 3. Commit
git add -A
git commit -m "feat: description détaillée"

# 4. Push
git push -u origin pr-description

# 5. Créer PR sur GitHub
# Base: brammmers/edrefcard2:librearbitre-pull-request
# Head: LibreArbitre/edrefcard2:pr-description
```

---

## 🔐 Synchronisation avec Upstream

### Périodiquement

```bash
# Récupérer les changements upstream
git fetch upstream

# Voir les différences
git log HEAD..upstream/main --oneline

# Merger dans votre main si nécessaire
git checkout main
git merge upstream/main
git push origin main
git push origin main:dev  # Aussi mettre à jour staging
```

---

## 📊 État Actuel (2026-01-11)

### Branches
- ✅ `local/main` : Branche unique de travail
- ✅ `origin/main` : Production (edrefcard2.l0l.fr)
- ✅ `origin/dev` : Staging (edrefcard2-dev.l0l.fr)
- 🔄 `origin/pr-v2.1-features` : PR en attente vers upstream

### PRs
- **PR #1** (mergée) : Migration Flask + Admin Panel
  - Status : ✅ Mergée dans `upstream/librearbitre-pull-request`
  
- **PR #2** (en attente) : v2.1 Features
  - Branche : `pr-v2.1-features`
  - Target : `upstream/librearbitre-pull-request`
  - Contenu : Stats, PDF, API, Security

---

## 💡 Astuces

### Reset staging = prod (en cas d'erreur)

```bash
# Remettre origin/dev identique à origin/main
git push -f origin main:dev
```

### Voir les différences staging vs prod

```bash
git diff origin/main origin/dev
```

### Rollback rapide en staging

```bash
# Revenir au commit précédent
git push -f origin main~1:dev
```

---

## 📞 Contacts & Ressources

- **Upstream** : https://github.com/brammmers/edrefcard2
- **Fork** : https://github.com/LibreArbitre/edrefcard2
- **Prod** : https://edrefcard2.l0l.fr
- **Staging** : https://edrefcard2-dev.l0l.fr

---

**Dernière mise à jour** : 11 janvier 2026 - Workflow simplifié (1 branche locale)
