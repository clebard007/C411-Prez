import os
import re
from string import Template
from dotenv import load_dotenv
from pymediainfo import MediaInfo
import tmdbsimple as tmdb
import argparse
import math

# =====================================================================
# 1. CONFIGURATION INITIALE
# =====================================================================

parser = argparse.ArgumentParser(description='Generer Presentation pour un film ou une série à partir de TMDB')
parser.add_argument('-f', '--video_file', required=True, help='Path to the video file')

args = parser.parse_args()

load_dotenv()
tmdb.API_KEY = os.getenv("TMDB_API_KEY")
TMDB_LANGUAGE = os.getenv("TMDB_LANGUAGE", "fr-FR")
TMDB_REGION = os.getenv("TMDB_REGION", "FR")

valeur_adulte_env = os.getenv("TMDB_INCLUDE_ADULT", "False").strip().lower()
INCLUDE_ADULT = valeur_adulte_env in ['true', '1', 'yes', 'oui']

BASE_IMAGE_URL = "https://image.tmdb.org/t/p/"
TAILLE_PHOTO_ACTEUR = "original"  
TAILLE_AFFICHE = "original"

NOM_FICHIER_TEMPLATE = os.getenv("FICHIER_TEMPLATE", "./template/template.tmp")

# Bannières depuis le .env
BANNER_INFO = os.getenv("INFORMATIONS_GENERALE_URL", "")
BANNER_SYNOPSIS = os.getenv("SYNOPSIS_URL", "")
BANNER_TECH = os.getenv("DETAILS_TECHNIQUES_URL", "")
BANNER_AUDIO = os.getenv("LANGUES_URL", "")
BANNER_SUBS = os.getenv("SOUS_TITRES_URL", "")
BANNER_DOWNLOAD = os.getenv("TELECHARGEMENT_URL", "")
TEAM_NAME = os.getenv("TEAM_NAME", "C411-Prez")

# =====================================================================
# 2. FONCTIONS UTILITAIRES
# =====================================================================
def generer_etoiles(vote_average):
    if not vote_average: return "Aucune note"
    return f"https://img.streetprez.com/note/{round(vote_average * 10)}.svg"

def bytes_to_gib(size_bytes):
    return round(size_bytes / (1024 ** 3), 2)

def analyser_release_infos(fichier_media):
    """
    Analyse MediaInfo pour récupérer :
    - langues
    - MULTi
    - HDR
    - Atmos
    """

    media_info = MediaInfo.parse(fichier_media)

    langues = set()

    hdr = []
    atmos = False

    for track in media_info.tracks:

        # Audio
        if track.track_type == "Audio":

            if track.language:
                langues.add(track.language.upper())

            format_commercial = (
                getattr(track, "commercial_name", "") or ""
            ).upper()

            format_audio = (
                getattr(track, "format", "") or ""
            ).upper()

            if (
                "ATMOS" in format_commercial
                or "ATMOS" in format_audio
            ):
                atmos = True

        # Vidéo
        elif track.track_type == "Video":

            hdr_format = (
                getattr(track, "hdr_format", "") or ""
            ).upper()

            hdr_format_string = (
                getattr(track, "hdr_format_string", "") or ""
            ).upper()

            complete_name = hdr_format + " " + hdr_format_string

            if "DOLBY VISION" in complete_name:
                hdr.append("DV")

            if "HDR10+" in complete_name:
                hdr.append("HDR10+")

            elif "HDR10" in complete_name:
                hdr.append("HDR")

    # Détermination du tag langue
    langues = sorted(list(langues))

    if len(langues) > 1:
        langue_tag = "MULTi"

    elif len(langues) == 1:

        langue = langues[0]

        mapping = {
            "FR": "FRENCH",
            "EN": "VOSTFR",
            "JA": "JAPANESE",
            "ES": "SPANISH",
            "IT": "ITALIAN"
        }

        langue_tag = mapping.get(langue, langue)

    else:
        langue_tag = "MULTi"

    return {
        "langue_tag": langue_tag,
        "hdr": ".".join(dict.fromkeys(hdr)),
        "atmos": "Atmos" if atmos else ""
    }

def generer_infos_techniques(fichier_media):
    """
    Récupère les informations techniques depuis MediaInfo.
    """

    media_info = MediaInfo.parse(fichier_media)

    source = "WEB"
    quality = "N/A"
    file_format = os.path.splitext(fichier_media)[1][1:].upper()
    video_codec = "N/A"
    video_debit = "N/A"

    for track in media_info.tracks:

        # Piste vidéo
        if track.track_type == "Video":

            largeur = getattr(track, "width", 0)

            if largeur:
                largeur = int(largeur)

                if largeur >= 3800:
                    quality = "2160p UHD"
                elif largeur >= 1900:
                    quality = "1080p"
                elif largeur >= 1200:
                    quality = "720p"

            if track.format:
                video_codec = track.format

            if track.bit_rate:
                video_debit = f"{int(track.bit_rate) // 1000} kb/s"

        # Piste générale
        elif track.track_type == "General":

            nom = os.path.basename(fichier_media).lower()

            if "bluray" in nom or "blu-ray" in nom:
                source = "BluRay"
            elif "web-dl" in nom:
                source = "WEB-DL"
            elif "webrip" in nom:
                source = "WEBRip"
            elif "hdtv" in nom:
                source = "HDTV"

    return {
        "source": source,
        "quality": quality,
        "file_format": file_format,
        "video_codec": video_codec,
        "video_debit": video_debit
    }


def generer_release_name(
        titre,
        annee,
        quality,
        source,
        video_codec,
        fichier_media,
        groupe_release):

    infos = analyser_release_infos(fichier_media)

    titre = re.sub(
        r'[^A-Za-z0-9]+',
        '.',
        titre
    ).strip('.')

    morceaux = [
        titre,
        str(annee),
        infos["langue_tag"],
        quality.replace(" UHD", "").replace(" ", "."),
        source
    ]

    if infos["hdr"]:
        morceaux.append(infos["hdr"])

    if infos["atmos"]:
        morceaux.append(infos["atmos"])

    morceaux.append(video_codec)

    release = ".".join(
        morceau
        for morceau in morceaux
        if morceau
    )

    return f"{release}-{groupe_release}"


def recuperer_infos_fichiers(chemin):
    """
    Retourne :
        nb_files
        size
    """

    if os.path.isfile(chemin):
        nb_files = 1
        total_size = os.path.getsize(chemin)

    else:
        nb_files = 0
        total_size = 0

        for root, dirs, files in os.walk(chemin):
            nb_files += len(files)

            for fichier in files:
                total_size += os.path.getsize(
                    os.path.join(root, fichier)
                )

    return nb_files, bytes_to_gib(total_size)

def formater_duree(duree_minutes):
    if not duree_minutes: return "Non disponible"
    total_secondes = int(float(duree_minutes) * 60)
    h, m = divmod(total_secondes // 60, 60)
    return f"{h:02d} heure(s) {m:02d} minute(s)"

def nettoyer_nom_fichier(nom):
    return re.sub(r'[\\/*?:"<>|]', "", nom)

def determiner_type_sous_titre(track):
    """
    Détermine le type de sous-titre :
    - SDH
    - Forcés
    - Complets
    """

    titre = (track.title or "").lower()

    if (
        "sdh" in titre
        or "malentendant" in titre
        or "hearing impaired" in titre
    ):
        return "SDH"

    if (
        getattr(track, "forced", "No") == "Yes"
        or "forced" in titre
        or "forcé" in titre
    ):
        return "Forcés"

    return "Complets"


def generer_tableau_sous_titres(fichier_media):
    """
    Analyse les pistes de sous-titres et retourne les lignes BBCode.
    """

    flags = {
        "fr": "fr",
        "en": "gb",
        "ja": "jp",
        "es": "es",
        "it": "it",
        "de": "de",
        "ru": "ru",
        "ko": "kr",
        "zh": "cn",
        "pt": "pt",
        "ar": "sa"
    }

    media_info = MediaInfo.parse(fichier_media)

    lignes = []
    index = 1

    for track in media_info.tracks:

        if track.track_type != "Text":
            continue

        langue = track.language or "Inconnue"
        format_st = track.format or "N/A"

        # Réutilisation de la logique existante pour le drapeau
        country_short_name = flags.get(
            langue.lower(),
            langue.lower()[:2]
        )

        type_st = determiner_type_sous_titre(track)

        ligne = (
            f"[tr]"
            f"[td]{index}[/td]"
            f"[td][img=32x24]"
            f"https://flagcdn.com/32x24/{country_short_name}.png"
            f"[/img] {langue.capitalize()}[/td]"
            f"[td]{format_st}[/td]"
            f"[td]{type_st}[/td]"
            f"[/tr]"
        )

        lignes.append(ligne)
        index += 1

    return "\n".join(lignes)
    
def generer_tableau_audio(fichier_media):
    """
    Analyse les pistes audio et retourne les lignes BBCode du tableau.
    """

    # Correspondance langue -> drapeau
    flags = {
        "fr": "fr",
        "en": "gb",
        "ja": "jp",
        "es": "es",
        "it": "it",
        "de": "de",
        "ru": "ru",
        "ko": "kr",
        "zh": "cn",
        "pt": "pt",
        "ar": "sa"
    }

    media_info = MediaInfo.parse(fichier_media)

    lignes = []
    index = 1

    for track in media_info.tracks:
        if track.track_type != "Audio":
            continue

        langue = track.language or "Inconnue"
        codec = track.format or "N/A"

        # Nombre de canaux
        canaux = str(track.channel_s) if track.channel_s else "N/A"

        # Bitrate audio
        bitrate = "N/A"
        if track.bit_rate:
            bitrate = str(int(track.bit_rate) // 1000)

        # Drapeau
        country_short_name = flags.get(
            langue.lower(),
            langue.lower()[:2]
        )

        ligne = (
            f"[tr]"
            f"[td]{index}[/td]"
            f"[td][img=32x24]"
            f"https://flagcdn.com/32x24/{country_short_name}.png"
            f"[/img] {langue.capitalize()}[/td]"
            f"[td]{codec}[/td]"
            f"[td]{canaux}[/td]"
            f"[td]{bitrate} kb/s[/td]"
            f"[/tr]"
        )

        lignes.append(ligne)
        index += 1

    return "\n".join(lignes)
# =====================================================================
# 3. PROGRAMME PRINCIPAL
# =====================================================================
if not os.path.exists(NOM_FICHIER_TEMPLATE):
    print(f"❌ Erreur : Le fichier '{NOM_FICHIER_TEMPLATE}' est introuvable.")
    print("Veuillez vérifier le chemin du template.")
    exit()

if not tmdb.API_KEY:
    print("❌ Erreur : La clé API TMDB est introuvable. Vérifiez votre fichier .env.")
else:
    try:
        recherche_utilisateur = input("Entrez le nom du film ou de la série : ")
        
        search = tmdb.Search()
        search.multi(query=recherche_utilisateur, language=TMDB_LANGUAGE, region=TMDB_REGION, include_adult=INCLUDE_ADULT)
        
        resultats = [res for res in search.results if res.get('media_type') in ['movie', 'tv']]
        
        if not resultats:
            print(f"Aucun résultat trouvé pour '{recherche_utilisateur}'.")
        else:
            print(f"\n--- Résultats trouvés ---")
            resultats_a_afficher = resultats[:10]
            
            for index, res in enumerate(resultats_a_afficher, 1):
                media_type = res.get('media_type')
                tag_xxx = "[XXX] " if res.get('adult', False) else ""
                
                num = f"{index:<2} ."
                if media_type == 'movie':
                    titre = res.get('title', 'Inconnu')
                    annee = res.get('release_date', 'Inconnue')[:4]
                    print(f"{num} {tag_xxx}🎬 {'[FILM]':<8} {titre} ({annee})")
                else:
                    titre = res.get('name', 'Inconnu')
                    annee = res.get('first_air_date', 'Inconnue')[:4]
                    print(f"{num} {tag_xxx}📺 {'[SÉRIE]':<8} {titre} ({annee})")

            # --- SÉLECTION INTERACTIVE ---
            choix = -1
            while True:
                try:
                    saisie = input(f"\nEntrez le numéro (1-{len(resultats_a_afficher)}) : ")
                    choix = int(saisie)
                    if 1 <= choix <= len(resultats_a_afficher):
                        break
                except ValueError:
                    pass

            selection = resultats_a_afficher[choix - 1]
            media_type = selection['media_type']
            
            # --- RÉCUPÉRATION DES DÉTAILS COMPLETS ---
            print("\nRécupération des métadonnées en cours...")
            media = tmdb.Movies(selection['id']) if media_type == 'movie' else tmdb.TV(selection['id'])
            infos = media.info(language=TMDB_LANGUAGE, append_to_response="credits,videos,external_ids,release_dates,content_ratings")
            
            # =================================================================
            # VARIABLES DE BASE AVEC FALLBACK "Non disponible"
            # =================================================================
            titre_principal = infos.get('title') if media_type == 'movie' else infos.get('name')
            titre_principal = titre_principal or "Non disponible"
            annee_sortie = (infos.get('release_date') or infos.get('first_air_date') or "0000")[:4]
            
            titre_original = infos.get('original_title') if media_type == 'movie' else infos.get('original_name')
            titre_original = titre_original or "Non disponible"
            
            date_sortie = infos.get('release_date') if media_type == 'movie' else infos.get('first_air_date')
            date_sortie = date_sortie or "Non disponible"
            
            synopsis = infos.get('overview') or "Non disponible"
            
            note_moyenne = infos.get('vote_average', 0)
            nb_votes = infos.get('vote_count', 0)
            
            chemin_affiche = infos.get('poster_path')
            url_affiche = f"{BASE_IMAGE_URL}{TAILLE_AFFICHE}{chemin_affiche}" if chemin_affiche else ""

            classification = "Non disponible"
            if media_type == 'movie':
                results = infos.get('release_dates', {}).get('results', [])
                for rd in results:
                    if rd.get('iso_3166_1') == TMDB_REGION:
                        for cert in rd.get('release_dates', []):
                            if cert.get('certification'):
                                classification = cert.get('certification')
                                break
                        break
            else:
                results = infos.get('content_ratings', {}).get('results', [])
                for cr in results:
                    if cr.get('iso_3166_1') == TMDB_REGION:
                        classification = cr.get('rating')
                        break
            
            # Pays
            pays_list = [p.get('name') for p in infos.get('production_countries', [])]
            if not pays_list:
                pays_list = infos.get('origin_country', [])
            pays_str = ", ".join(pays_list) if pays_list else "Non disponible"
            
            # Genres
            genres_list = [g['name'] for g in infos.get('genres', [])]
            genres_str = ", ".join(genres_list) if genres_list else "Non disponible"
            
            # =================================================================
            # GESTION DE LA DURÉE ET FORMAT DE L'UPLOAD (SÉRIES)
            # =================================================================
            if media_type == 'movie':
                duree_str = formater_duree(infos.get('runtime', 0))
            else:
                durees = infos.get('episode_run_time', [])
                avg_runtime = durees[0] if durees else (infos.get('last_episode_to_air', {}).get('runtime') or 0)
                
                status = infos.get('status', '')
                is_ended = status in ['Ended', 'Canceled']
                
                print("\n--- FORMAT DE L'UPLOAD ---")
                options = []
                if is_ended:
                    options.append("Série Intégrale")
                options.append("Saison Complète")
                options.append("Épisode Spécifique")
                
                for i, opt in enumerate(options, 1):
                    print(f"{i}. {opt}")
                
                while True:
                    try:
                        choix_format = int(input(f"Choisissez le format (1-{len(options)}) : ")) - 1
                        if 0 <= choix_format < len(options):
                            break
                    except ValueError:
                        pass
                        
                selection_format = options[choix_format]
                total_minutes = 0
                nb_episodes_calcul = 0
                
                if selection_format == "Série Intégrale":
                    print("\nCalcul du temps total exact...")
                    saisons = [s for s in infos.get('seasons', []) if s.get('season_number') > 0]
                    
                    for s in saisons:
                        try:
                            s_info = tmdb.TV_Seasons(selection['id'], s.get('season_number')).info(language=TMDB_LANGUAGE)
                            for ep in s_info.get('episodes', []):
                                nb_episodes_calcul += 1
                                total_minutes += ep.get('runtime') or avg_runtime
                        except:
                            nb_episodes = s.get('episode_count', 0)
                            nb_episodes_calcul += nb_episodes
                            total_minutes += (nb_episodes * avg_runtime)
                    
                    titre_principal += " - Intégrale"
                    
                elif selection_format == "Saison Complète":
                    saisons = [s for s in infos.get('seasons', []) if s.get('season_number') > 0]
                    print("\nSaisons disponibles :")
                    for i, s in enumerate(saisons, 1):
                        print(f"{i}. Saison {s.get('season_number')} ({s.get('episode_count')} épisodes)")
                    
                    while True:
                        try:
                            num_s = int(input("\nEntrez le numéro de la saison : "))
                            saison_choisie = next((s for s in saisons if s.get('season_number') == num_s), None)
                            if saison_choisie:
                                print(f"Récupération des métadonnées de la saison {num_s:02d}...")
                                try:
                                    s_info = tmdb.TV_Seasons(selection['id'], num_s).info(language=TMDB_LANGUAGE)
                                    
                                    if s_info.get('overview'): synopsis = s_info.get('overview')
                                    if s_info.get('air_date'): date_sortie = s_info.get('air_date')
                                    if s_info.get('poster_path'): url_affiche = f"{BASE_IMAGE_URL}{TAILLE_AFFICHE}{s_info.get('poster_path')}"
                                    
                                    for ep in s_info.get('episodes', []):
                                        nb_episodes_calcul += 1
                                        total_minutes += ep.get('runtime') or avg_runtime
                                except:
                                    nb_episodes_calcul = saison_choisie.get('episode_count', 1)
                                    total_minutes = nb_episodes_calcul * avg_runtime
                                    
                                titre_principal += f" - Saison {num_s:02d}"
                                break
                            else:
                                print("Saison introuvable.")
                        except ValueError:
                            pass
                            
                elif selection_format == "Épisode Spécifique":
                    saisons = [s for s in infos.get('seasons', []) if s.get('season_number') > 0]
                    print("\nSaisons disponibles :")
                    for i, s in enumerate(saisons, 1):
                        print(f"{i}. Saison {s.get('season_number')} ({s.get('episode_count')} épisodes)")
                        
                    while True:
                        try:
                            num_s = int(input("\nNuméro de la saison : "))
                            saison_choisie = next((s for s in saisons if s.get('season_number') == num_s), None)
                            if saison_choisie:
                                max_ep = saison_choisie.get('episode_count')
                                num_e = int(input(f"Numéro de l'épisode (1-{max_ep}) : "))
                                
                                titre_principal += f" - S{num_s:02d}E{num_e:02d}"
                                nb_episodes_calcul = 1
                                
                                try:
                                    episode_info = tmdb.TV_Episodes(selection['id'], num_s, num_e).info(language=TMDB_LANGUAGE)
                                    total_minutes = episode_info.get('runtime') or avg_runtime
                                    
                                    if episode_info.get('name'):
                                        titre_principal += f" ({episode_info.get('name')})"
                                        
                                    if episode_info.get('overview'):
                                        synopsis = episode_info.get('overview')
                                        
                                    if episode_info.get('air_date'):
                                        date_sortie = episode_info.get('air_date')
                                        
                                    if episode_info.get('vote_average'):
                                        note_moyenne = episode_info.get('vote_average')
                                        nb_votes = episode_info.get('vote_count', 0)
                                        
                                    if episode_info.get('still_path'):
                                        url_affiche = f"{BASE_IMAGE_URL}{TAILLE_AFFICHE}{episode_info.get('still_path')}"
                                        
                                except Exception as e:
                                    print(f"Détails de l'épisode introuvables : {e}")
                                    total_minutes = avg_runtime
                                break
                            else:
                                print("Saison introuvable. Veuillez réessayer.")
                        except ValueError:
                            pass
                
                duree_str = formater_duree(total_minutes)
                if nb_episodes_calcul > 1 and total_minutes > 0:
                    duree_str += f" (Total cumulé pour {nb_episodes_calcul} épisodes)"

            # =================================================================
            # PRÉPARATION DES DERNIÈRES DONNÉES (Notes, Liens, Acteurs)
            # =================================================================
            
            pourcentage = int(round(note_moyenne * 10))
            url_etoiles = generer_etoiles(note_moyenne)
            
            lien_tmdb = f"https://www.themoviedb.org/{media_type}/{selection['id']}"
            bbcode_tmdb = f"[url={lien_tmdb}]TMDb[/url]"
            
            imdb_id = infos.get('external_ids', {}).get('imdb_id') or infos.get('imdb_id')
            if imdb_id:
                bbcode_imdb = f"[url=https://www.imdb.com/title/{imdb_id}/]IMDb[/url]"
            else:
                bbcode_imdb = "IMDb (Non disponible)"
            
            bbcode_trailer = "Bande-annonce (Non disponible)"
            for video in infos.get('videos', {}).get('results', []):
                if video.get('site') == 'YouTube' and video.get('type') == 'Trailer':
                    lien_yt = f"https://www.youtube.com/watch?v={video.get('key')}"
                    bbcode_trailer = f"[url={lien_yt}]Bande-annonce[/url]"
                    break
                    
            liens_complets = f"{bbcode_tmdb} - {bbcode_imdb} - {bbcode_trailer}"
            
            # =================================================================
            # RÉCUPÉRATION DU BUDGET (Seulement pour les films)
            # =================================================================
            if media_type == 'movie':
                budget_brut = infos.get('budget', 0)
                if budget_brut > 0:
                    # Formate avec des espaces (ex: 150000000 -> 150 000 000 $)
                    bbcode_budget = f"{budget_brut:,} $".replace(",", " ")
                else:
                    bbcode_budget = "Non disponible"
            else:
                bbcode_budget = "Non disponible (Série)"

            # Réalisateurs / Créateurs
            if media_type == 'movie':
                realisateurs = [m['name'] for m in infos.get('credits', {}).get('crew', []) if m.get('job') == 'Director']
                realisateur_str = ", ".join(realisateurs) if realisateurs else "Non disponible"
            else:
                createurs = [c['name'] for c in infos.get('created_by', [])]
                realisateur_str = ", ".join(createurs) if createurs else "Non disponible"

            # Acteurs avec forçage du ratio
            images_acteurs_bbcode = ""
            noms_acteurs_bbcode = ""
            
            cast_list = infos.get('credits', {}).get('cast', [])[:6]
            if not cast_list:
                noms_acteurs_bbcode = "Non disponible"
            else:
                for acteur in cast_list:
                    chemin_photo = acteur.get('profile_path')
                    if chemin_photo:
                        url_photo = f"{BASE_IMAGE_URL}{TAILLE_PHOTO_ACTEUR}{chemin_photo}"
                        # Ici on force l'affichage à 150x225 (ratio 2:3 parfait)
                        images_acteurs_bbcode += f"[img=150x225]{url_photo}[/img] "
                    
                    nom = acteur.get('name', 'Inconnu')
                    role = acteur.get('character', '')
                    noms_acteurs_bbcode += f"[b]{nom}[/b] ({role}) • "

                images_acteurs_bbcode = images_acteurs_bbcode.strip()
                noms_acteurs_bbcode = noms_acteurs_bbcode.strip(" • ")
            
            audio_tracks_bbcode = generer_tableau_audio(args.video_file)
            subtitle_tracks_bbcode = generer_tableau_sous_titres(args.video_file)

            infos_tech = generer_infos_techniques(args.video_file)

            release_name = generer_release_name(
                titre_principal,
                annee_sortie,
                infos_tech["quality"],
                infos_tech["source"],
                infos_tech["video_codec"],
                args.video_file,
                TEAM_NAME
            )

            nb_files, size = recuperer_infos_fichiers(args.video_file)
            # =================================================================
            # INJECTION DANS LE TEMPLATE
            # =================================================================
            
            donnees_template = {
                "title": titre_principal,
                "year": annee_sortie,
                "affiche": url_affiche,
                "original_title": titre_original,
                "country": pays_str,
                "genres": genres_str,
                "classification": classification,
                "release_date": date_sortie,
                "duration": duree_str,
                "url_etoiles": url_etoiles,
                "pourcentage": str(pourcentage),
                "nb_votes": str(nb_votes),
                "liens": liens_complets,
                "director": realisateur_str,
                "actors_images": images_acteurs_bbcode,
                "actors_names": noms_acteurs_bbcode,
                "synopsis": synopsis,
                "budget": bbcode_budget,
                
                # Champs techniques à définir par l'utilisateur
                "source": infos_tech["source"],
                "quality": infos_tech["quality"],
                "format": infos_tech["file_format"],
                "video_codec": infos_tech["video_codec"],
                "video_debit": infos_tech["video_debit"],

                "Release_name": release_name,
                "nb_files": str(nb_files),
                "size": str(size),
                "audio_tracks": audio_tracks_bbcode,
                "subtitle_tracks": subtitle_tracks_bbcode,
                
                # Bannières
                "banner_info": BANNER_INFO,
                "banner_synopsis": BANNER_SYNOPSIS,
                "banner_tech": BANNER_TECH,
                "banner_audio": BANNER_AUDIO,
                "banner_subs": BANNER_SUBS,
                "banner_download": BANNER_DOWNLOAD,

                # Autres informations
                "team_name": TEAM_NAME
            }
            
            with open(NOM_FICHIER_TEMPLATE, 'r', encoding='utf-8') as f:
                contenu_brut = f.read()
                
            template_obj = Template(contenu_brut)
            contenu_final = template_obj.safe_substitute(donnees_template)
            
            nom_fichier_final = f"{nettoyer_nom_fichier(titre_principal)}.bbcode"
            with open(nom_fichier_final, "w", encoding="utf-8") as fichier:
                fichier.write(contenu_final)
                
            print(f"\n✅ Fichier généré avec succès : {nom_fichier_final}")

    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")