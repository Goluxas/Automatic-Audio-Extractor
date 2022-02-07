"""
Given a folder as an argument, extracts the Japanese audio track from all files using ffmpeg.
Extracted audio is formatted as MP3.
(Maybe) move the extracted audio to the Plex server's extract folder.

ffmpeg commands:

ffprobe <filename>
    Will output information about the video file. Use to determine the Japanese audio track. Fall back to user input if it fails.

    Example output:
    Input #0, matroska,webm, from '.\Dragon.Ball.KAI.-.90.-.1080p.BluRay.x264.DHD.mkv':
    Metadata:
        encoder         : libebml v1.2.3 + libmatroska v1.3.0
        creation_time   : 2012-07-08T10:46:22.000000Z
    Duration: 00:23:02.17, start: 0.000000, bitrate: 4555 kb/s
    Stream #0:0: Video: h264 (High), yuv420p(progressive), 1440x1080 [SAR 1:1 DAR 4:3], 23.98 fps, 23.98 tbr, 1k tbn, 47.95 tbc (default)
    Stream #0:1(eng): Audio: aac (LC), 48000 Hz, 5.1, fltp (default)
    Stream #0:2(jpn): Audio: aac (LC), 48000 Hz, stereo, fltp
    Stream #0:3(eng): Subtitle: subrip (default)

ffmpeg -i <filename> -q:a 0 -map <stream index> <output_filename>
    -map picks the track to extract. matches the index above, eg. -map 0:2
    in the above case, ffprobe showed the track as Stream #0:2, but it's the second audio track (index 1)
    FFmpeg will automatically try to convert to the output filename's extension, so just make sure it ends in MP3
"""

import subprocess
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

VIDEO_EXTS = (".mkv", ".mp4")
AUDIO_STREAM_RE = re.compile(r"Stream #(\d:\d)\(([a-zA-Z]+)\): Audio")


class JapaneseNotFoundException(Exception):
    pass


def get_japanese_audio_track(video_file: Path) -> str:
    """
    Returns the index ready to plug into ffmpeg

    Args:
        video_file (Path): path to the video file to check

    Returns:
        index (str): eg. "0:2"

    Raises:
        JapaneseNotFoundException: If no track labeled for Japanese is found
    """
    video = str(video_file)
    cmd = f'ffprobe "{video}"'
    output = subprocess.run(cmd, capture_output=True)

    # streams will be a list of tuples of the capture groups
    # eg. [ ("0:1", "eng"), ("0:2", "jpn") ]
    streams = AUDIO_STREAM_RE.findall(str(output.stderr))

    # if there's only one stream, assume it's Japanese
    if len(streams) == 0:
        raise JapaneseNotFoundException

    if len(streams) == 1:
        return streams[0][0]

    # otherwise, look for Japanese
    for index, language in streams:
        if language.lower() == "jpn":
            return index

    raise JapaneseNotFoundException


def extract_audio(video_file: Path) -> None:
    # find the Japanese audio track
    try:
        track_index = get_japanese_audio_track(video_file)
    except JapaneseNotFoundException:
        print("No Japanese audio track found.")
        # TODO manual selection
        return

    # use ffmpeg to convert to mp3
    # print(track_index)

    input_filename = str(video_file)
    output_filename = video_file.parent / (video_file.stem + ".mp3")
    output_filename = str(output_filename)
    cmd = f'ffmpeg -i "{video_file}" -q:a 0 -map {track_index} "{output_filename}"'

    print(f"Extracting audio from {input_filename}\n")
    subprocess.run(cmd, capture_output=True)


def main(folder_to_convert: str) -> None:
    folder_to_convert = Path(folder_to_convert)

    print("Scanning folder for video files")
    video_files = [
        video_file
        for video_file in folder_to_convert.iterdir()
        if video_file.is_file() and video_file.suffix.lower() in VIDEO_EXTS
    ]

    with ThreadPoolExecutor() as executor:
        executor.map(extract_audio, video_files)

    print("Conversion complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("folder_to_convert")
    args = parser.parse_args()

    import timeit

    start = timeit.default_timer()
    main(args.folder_to_convert)
    end = timeit.default_timer()
    print(end - start)
