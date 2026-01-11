# Guide: Créer un Template pour les 5 Contrôleurs Prioritaires

## Contrôleurs à Prioriser (40% des utilisateurs)

1. **VKB Gladiator NXT Premium Right** (664 configs, 13.3%)
2. **Saitek X56 Throttle** (423 configs, 8.5%)
3. **Saitek X56 Joystick** (415 configs, 8.3%)
4. **VKB Gladiator NXT Premium Left** (266 configs, 5.3%)
5. **VKB Gladiator NXT Left OTA** (264 configs, 5.3%)

---

## 1. VKB Gladiator NXT Premium Right

### Ressources Officielles

**Documentation:**
- Site officiel: https://vkb-sim.com/
- Manuel PDF: https://vkb-sim.com/download/manuals/ (chercher "Gladiator NXT")
- Configuration tool: VKBDevCfg (gratuit, téléchargeable sur le site)

**Images Haute Résolution:**
- Site VKB: https://vkb-sim.com/products/gladiator-evo-space-combat-edition/
- Review professionnelle: https://www.youtube.com/watch?v=... (chercher "VKB Gladiator NXT review")

### Device ID
- `231D0200` (déjà dans supportedDevices, mais pas de template visuel)

### Mapping des Boutons

**Référence rapide:**
```
Joy_1  → Trigger principal (index finger)
Joy_2  → Bouton rouge sur le dessus (A1)
Joy_3  → Bouton rouge latéral (A2)
Joy_4  → Bouton noir sur le dessus (A3)
Joy_5  → Bouton ministick press

Hats:
Joy_POV1Up/Right/Down/Left → Hat principal 8-way
Joy_7-10 → Hat supérieur (4-way)
Joy_11-14 → Hat latéral (4-way)

Axes:
Joy_XAxis → Roll (gauche-droite)
Joy_YAxis → Pitch (avant-arrière)
Joy_RZAxis → Twist (rotation)
Joy_UAxis → Throttle slider
```

### Processus de Création

1. **Obtenir l'image:**
   - Télécharger depuis le site VKB
   - Ou screenshot d'une review 4K YouTube
   - Redimensionner à 3840px largeur dans GIMP

2. **Tester le mapping:**
   - Installer VKBDevCfg
   - Connecter le joystick
   - Appuyer sur chaque bouton et noter le numéro

3. **Créer le template:**
   - Utiliser l'outil admin (quand disponible)
   - Ou manuellement dans GIMP, noter coordonnées X,Y

4. **Code Python:**
   ```python
   'VKB-Gladiator-NXT-Premium-Right': {
       'displayName': 'VKB Gladiator NXT Premium Right',
       'Joy_1': {'Type': 'Digital', 'x': 1234, 'y': 567, 'width': 800},
       # ... etc
   }
   ```

---

## 2. Saitek X56 Throttle

### Ressources Officielles

**Documentation:**
- Site Logitech G (propriétaire actuel): https://www.logitechg.com/en-us/products/space/x56-space-flight-vr-simulator-controller.html
- Manuel PDF: Téléchargeable depuis la page produit
- Legacy Saitek: https://support.logi.com/hc/en-us/articles/360025596274

**Images:**
- Marketing Logitech: Images officielles haute résolution
- Review Guru3D: https://www.guru3d.com/articles-pages/saitek-x-56-rhino-review,3.html

### Device IDs
- Throttle: `SaitekX56Throttle` ou `0738A221`
- **Template existe déjà!** (ligne 578 bindingsData.py)

**NOTE:** Ce contrôleur est DÉJÀ supporté avec template visuel complet ✅

---

## 3. Saitek X56 Joystick

### Device ID
- `SaitekX56Joystick` ou `07382221`

**Template existe déjà!** (ligne 525 bindingsData.py) ✅

---

## 4 & 5. VKB Gladiator NXT Premium Left / Left OTA

### Device IDs
- Left standard: `231D0201`
- Left OTA: `231d3201` (lowercase)

**NOTE:** Même configuration que le Right, mais image miroir

### Ressources

Identiques au Gladiator NXT Right, mais:
- Configuration main gauche (image inversée)  
- Mapping identique aux boutons près
- OTA = "Over The Air" firmware updates

### Astuce de Création

**Réutiliser le template Right:**
1. Copier l'image du Right
2. Faire un flip horizontal dans GIMP
3. Réutiliser les mêmes coordonnées (ajuster X pour le flip)
4. Device ID différent, template différent

---

## Processus Manuel Détaillé

### Étape 1: Préparation (15 min)

**Checklist:**
- [ ] Télécharger manuel PDF du fabricant
- [ ] Télécharger image haute résolution
- [ ] Installer GIMP (si pas déjà fait)
- [ ] Accéder à un fichier `.binds` test avec ce contrôleur

### Étape 2: Image Template (30 min)

**Dans GIMP:**

1. Ouvrir l'image source
2. `Image` → `Scale Image` → Largeur: 3840px
3. `Image` → `Flatten Image` (si transparence)
4. `File` → `Export As` → `www/layouts/nom-controleur.jpg`
5. Qualité: 90%

### Étape 3: Mapping des Coordonnées (1-2h)

**Méthode GIMP:**

1. Ouvrir l'image template
2. `Windows` → `Dockable Dialogs` → `Pointer`
3. Activer la grille: `View` → `Show Grid`
4. Pour chaque bouton:
   - Positionner curseur au centre du bouton
   - Noter X, Y dans le pointer dialog
   - Estimer largeur disponible pour texte
   
**Tableur de mapping:**
```
Bouton      | X    | Y    | Width | Type
------------|------|------|-------|----------
Joy_1       | 2124 | 618  | 642   | Digital
Joy_2       | 2084 | 208  | 792   | Digital
Joy_POV1Up  | 1684 | 288  | 1072  | Digital
Joy_XAxis   | 3194 | 1110 | 632   | Analogue
```

### Étape 4: Code Python (30 min)

**Dans `bindingsData.py`:**

1. Trouver la section `hotasDetails = {`
2. Ajouter nouvelle entrée:

```python
'231D0200': {  # Device ID
    'displayName': 'VKB Gladiator NXT Premium Right',
    
    # Boutons digitaux
    'Joy_1': {'Type': 'Digital', 'x': 2124, 'y': 618, 'width': 642},
    'Joy_2': {'Type': 'Digital', 'x': 2084, 'y': 208, 'width': 792},
    
    # Hats
    'Joy_POV1Up': {'Type': 'Digital', 'x': 1684, 'y': 288, 'width': 1072},
    'Joy_POV1Right': {'Type': 'Digital', 'x': 1684, 'y': 344, 'width': 1072},
    'Joy_POV1Down': {'Type': 'Digital', 'x': 1684, 'y': 400, 'width': 1072},
    'Joy_POV1Left': {'Type': 'Digital', 'x': 1684, 'y': 456, 'width': 1072},
    
    # Axes analogiques
    'Joy_XAxis': {'Type': 'Analogue', 'x': 3194, 'y': 1110, 'width': 632},
    'Joy_YAxis': {'Type': 'Analogue', 'x': 3194, 'y': 1054, 'width': 632},
    'Joy_RZAxis': {'Type': 'Analogue', 'x': 3194, 'y': 1166, 'width': 632},
    
    # ... continuer pour tous les boutons
},
```

### Étape 5: Test (15 min)

1. Uploader un fichier `.binds` avec le contrôleur
2. Vérifier que l'image s'affiche
3. Vérifier que tous les textes sont lisibles
4. Ajuster si nécessaire

---

## Astuces et Bonnes Pratiques

### Espacement des Textes
- **Minimum width:** 400px pour lisibilité
- **Optimal width:** 600-800px
- **Éviter:** Moins de 300px (texte trop serré)

### Type de Boutons
- `Digital`: Boutons on/off, hats
- `Analogue`: Axes, sliders, rotaries

### Hauteur Personnalisée
- Par défaut: 54px
- Si besoin plus d'espace: `'height': 108`

### Hats (POV)
- Toujours 4 directions: `Up`, `Right`, `Down`, `Left`
- Espacement vertical: ~56px entre chaque direction
- Largeur identique pour tous

### Organisation du Code
```python
# 1. Boutons principaux (trigger, etc.)
# 2. Hats organisés par groupe
# 3. Axes analogiques
# 4. Boutons secondaires
```

---

## Estimation de Temps Réaliste

| Contrôleur | Temps Total | Commentaire |
|------------|-------------|-------------|
| VKB Glad NXT Right | 3h | Premier, apprentissage |
| Saitek X56 Throttle | ✅ Déjà fait | 0h |
| Saitek X56 Joystick | ✅ Déjà fait | 0h |
| VKB Glad NXT Left | 1h | Réutilise Right, juste flip |
| VKB Glad NXT Left OTA | 30min | Identique au Left |

**Total réel nécessaire: ~4.5 heures** pour couvrir 40% des utilisateurs (car 2/5 déjà faits!)

---

## Prochaines Étapes

1. **Immédiat:** VKB Glad NXT Right (13% utilisateurs)
2. **Ensuite:** VKB Glad NXT Left (5%)  
3. **Bonus:** VKB Left OTA (5%) - quasi gratuit

Les Saitek X56 sont déjà complets, donc **priorité VKB uniquement**.

---

## Liens Rapides

**VKB:**
- Site: https://vkb-sim.com/
- Support: https://support.vkb-sim.pro/
- Forum: https://forum.vkb-sim.pro/

**Saitek/Logitech:**
- Support: https://support.logi.com/
- Drivers: https://support.logi.com/hc/en-us/articles/360025596274
