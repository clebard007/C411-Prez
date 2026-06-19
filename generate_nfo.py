from pymediainfo import MediaInfo
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description='Generate NFO file for a video file')
parser.add_argument('-f', '--video_file', required=True, help='Path to the video file')
parser.add_argument('-o', '--output', help='Path to the output file', default='film.nfo')

args = parser.parse_args()

infos = MediaInfo.parse(args.video_file, output="text", full=False)

def remove_blank_lines(file):
    file = Path(args.output)
    lines = file.read_text().splitlines()
    filtered = [
        line
        for line in lines
        if line.strip()
    ]
    file.write_text('\n'.join(filtered))

with open(args.output, 'w') as fp:
    fp.write(infos)

remove_blank_lines(args.output)