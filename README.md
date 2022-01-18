# Automatic-Audio-Extractor

Scans a folder for video files and attempts to extract each file's Japanese audio track to an mp3.
Audio files are output with the same name as the video file with an mp3 extension. Beware of overwriting
existing mp3s.

The method to detect Japanese is pretty naive. In summary:

1. If there is only one audio track, extract it.
2. If there are multiple audio tracks, look for one tagged "jpn" and extract it.
3. Failing that, raise an exception and end execution.

## Requirements

Python 3.6+  
ffmpeg - Must be installed and in the user's PATH.  
ffprobe - Comes with the ffmpeg package.

## Usage

python extract_from_folder.py <folder of video files>
