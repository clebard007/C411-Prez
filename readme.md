# 🎬 Generate Prez

Générateur automatique de présentations BBCode pour les trackers torrents à partir des métadonnées **TMDb** et des informations techniques extraites avec **MediaInfo**.

Le script génère automatiquement une présentation complète au format BBCode comprenant :

- Informations générales du film ou de la série
- Synopsis
- Affiche officielle
- Acteurs principaux
- Notes TMDb
- Liens TMDb / IMDb / Bande-annonce
- Informations techniques
- Pistes audio
- Sous-titres
- Nom de release normalisé
- Informations de release (taille, nombre de fichiers, etc.)

---

# ✨ Fonctionnalités

✅ Recherche automatique sur TMDb

✅ Support des :

- Films
- Séries TV

✅ Gestion des formats :

- Série complète
- Saison complète
- Épisode spécifique

✅ Extraction automatique via MediaInfo :

- Résolution vidéo
- Codec vidéo
- Débit vidéo
- Format du conteneur
- Pistes audio
- Sous-titres
- HDR / HDR10 / Dolby Vision
- Dolby Atmos

✅ Génération automatique :

- Nom de release
- Taille totale
- Nombre de fichiers
- Présentation BBCode complète

---

# 📋 Pré-requis

- Python 3.10 ou supérieur
- Une clé API TMDb
- MediaInfo installé sur la machine

---

# 🚀 Installation

## 1. Cloner le dépôt

```bash
git clone https://github.com/votre-compte/generate-prez.git

cd generate-prez
```
---

## 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

Si le fichier `requirements.txt` n'existe pas :

```bash
pip install pymediainfo tmdbsimple python-dotenv
```

---

# ⚙️ Configuration

Créer un fichier `.env` à la racine du projet.

Exemple :

```ini
TMDB_API_KEY=VotreCleAPI
TMDB_LANGUAGE=fr-FR
TMDB_REGION=FR
TMDB_INCLUDE_ADULT=False

FICHIER_TEMPLATE=./template/template.tmp

TEAM_NAME=C411

INFORMATIONS_GENERALE_URL=https://monsite/banner_info.png
SYNOPSIS_URL=https://monsite/banner_synopsis.png
DETAILS_TECHNIQUES_URL=https://monsite/banner_tech.png
LANGUES_URL=https://monsite/banner_audio.png
SOUS_TITRES_URL=https://monsite/banner_subs.png
TELECHARGEMENT_URL=https://monsite/banner_download.png
```

---

# 🔑 Obtenir une clé API TMDb

Créer gratuitement un compte :

https://www.themoviedb.org/

Puis :

1. Ouvrir **Paramètres**
2. Sélectionner **API**
3. Générer une clé API

---

# 🎥 Utilisation

## Génération d'une présentation

```bash
python generate_prez.py -f "C:\Films\Avatar.mkv"
```

ou

```bash
python generate_prez.py --video_file "C:\Films\Avatar.mkv"
```

---

# 🖥️ Exemple d'utilisation

```bash
python generate_prez.py -f "D:\Movies\Dune.Part.Two.2024.mkv"
```

Le script demandera :

```text
Entrez le nom du film ou de la série :
```

Exemple :

```text
Dune Part Two
```

Puis :

```text
--- Résultats trouvés ---

1. 🎬 [FILM] Dune : Deuxième Partie (2024)
2. 🎬 [FILM] Dune (2021)
```

Sélectionner simplement le numéro correspondant.

---

# 📄 Fichiers générés

Le script génère automatiquement :

```text
Nom Du Film.bbcode
```

---

# 📝 Génération d'un fichier NFO

Le projet contient également un générateur de fichier NFO.

## Utilisation

```bash
python generate_nfo.py -f "C:\Films\Avatar.mkv"
```

Par défaut, le fichier suivant sera créé :

```text
film.nfo
```

Pour spécifier un autre nom :

```bash
python generate_nfo.py -f "C:\Films\Avatar.mkv" -o "Avatar.nfo"
```

---

# 📁 Structure du projet

```text
.
├── generate_prez.py
├── generate_nfo.py
├── .env
├── template/
│   └── template.tmp
├── requirements.txt
└── README.md
```

---

# 🏷️ Exemple de release générée

```text
Dune.Part.Two.2024.MULTi.2160p.UHD.BluRay.DV.HDR.Atmos.HEVC-C411
```

---

# 📦 Dépendances

- pymediainfo
- tmdbsimple
- python-dotenv

```bash
pip install -r requirements.txt
```

---

## Erreur

```text
La clé API TMDB est introuvable
```

Vérifier la présence du fichier `.env` ainsi que la variable :

```ini
TMDB_API_KEY=
```


---

# 📜 Licence

Projet distribué sous licence MIT.