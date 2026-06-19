from pathlib import Path
from pymediainfo import MediaInfo


def generate_nfo(video_file):
    video_path = Path(video_file)

    if not video_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {video_path}")

    print(f"Analyse de : {video_path}")

    try:
        media_info = MediaInfo.parse(str(video_path))
    except Exception as e:
        print(f"Erreur MediaInfo : {e}")
        return

    if not media_info.tracks:
        print("Aucune piste détectée.")
        return

    nfo_path = video_path.with_suffix(".nfo")

    print(f"Création : {nfo_path}")

    with open(nfo_path, "w", encoding="utf-8") as f:

        audio_count = 0
        text_count = 0

        for track in media_info.tracks:

            if track.track_type == "General":
                title = "General"

            elif track.track_type == "Video":
                title = "Vidéo"

            elif track.track_type == "Audio":
                audio_count += 1
                title = f"Audio #{audio_count}"

            elif track.track_type == "Text":
                text_count += 1
                title = f"Texte #{text_count}"

            else:
                title = track.track_type

            f.write(title + "\n")

            for key, value in vars(track).items():

                if key.startswith("_"):
                    continue

                if value in (None, "", [], {}):
                    value = "N/A"

                f.write(f"{key:40} : {value}\n")

            f.write("\n")

    print(f"NFO généré : {nfo_path.resolve()}")


if __name__ == "__main__":
    generate_nfo(r"film.mkv")