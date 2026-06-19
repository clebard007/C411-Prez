from pymediainfo import MediaInfo
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description='Generate NFO file for a video file')
parser.add_argument('-f', '--video_file', required=True, help='Path to the video file')
parser.add_argument('-o', '--output', help='Path to the output file', default='film.nfo')

# Get IMDB Infos
# Store everything in a dict
# add IMDB ID
# Get affiche (from IMDB ?)



