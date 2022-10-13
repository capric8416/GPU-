import os
import re
import subprocess

import fire

from my_logger import *


logger = get_logger('rename')


def rename(file_name):
    # partition name and extension
    name = file_name.partition('.')[0]
    ext = file_name.rpartition('.')[-1]

    # ffprobe video info
    process = subprocess.run(
        args=[
            'ffprobe', file_name,
            '-select_streams', 'v:0',
            '-count_frames',
            '-show_entries', 'stream=nb_read_frames'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stderr = process.stderr.strip()
    stdout = process.stdout.strip()
    
    # extract duration, bitrate
    result = re.search(pattern=r'Duration: (\d{2}:\d{2}:\d{2}.\d{2}),.*, bitrate: (\d+) kb/s', string=stderr)
    duration, bitrate = 0, 0
    if result:
        duration = result.group(1).replace(":", "").replace(".", "")
        bitrate = result.group(2)
        logger.debug({'message': 'probe', 'duration': duration, 'bitrate': bitrate})

    # extract codec, resolution, fps
    result = re.search(pattern=r'Stream .*?: Video: ([a-z]+\d*) .*?,.*?, (\d+x\d+).*, (\d+) fps', string=stderr)
    if result:
        codec = result.group(1)
        resolution = result.group(2)
        fps = result.group(3)
        logger.debug({'message': 'probe', 'codec': codec, 'resolution': resolution, 'fps': fps})

    # extract frames
    result = re.search(pattern=r'nb_read_frames=(\d+)', string=stdout)
    if result:
        frames = result.group(1)
        logger.debug({'message': 'probe', 'frames': frames})

    # calculate duration and bitrate of elementary stream according to frames and fps
    if not duration or not bitrate:
        milliseconds = int(frames) / int(fps)

        hours = milliseconds // 3600 % 24
        minutes = milliseconds // 60 % 60
        seconds = milliseconds % 60
        milliseconds = (milliseconds - int(milliseconds)) * 1000
        if milliseconds > 99:
            milliseconds //= 10
        duration = f'{int(hours):>02}{int(minutes):>02}{int(seconds):>02}{int(milliseconds):>02}'

        bitrate = os.path.getsize(filename=file_name) / (1024 * milliseconds)

        logger.debug({'message': 'calculate', 'duration': duration, 'bitrate': bitrate})

    # rename
    new_file_name = f'{name}.{resolution}.{codec}.{fps}fps.{frames}.{duration}.{bitrate}kbps.{ext}'
    if new_file_name != file_name:
        logger.info({'message': 'rename', 'from': file_name, 'to': new_file_name})
        os.rename(file_name, new_file_name)


def rename_video_according_to_info(path = './', include_extensions = ('.mp4', '.webm', '.264', '.265')):
    cwd = os.getcwd()
    os.chdir(path)

    # list files
    for file_name in os.listdir():
        # skip by file extension
        skip = True
        for ext in include_extensions:
            if file_name.endswith(ext):
                skip = False
                break
        if skip:
            continue

        # skip by frames
        file_name_parts = os.path.basename(file_name).split('.')
        if len(file_name_parts) > 4 and file_name_parts[4].isdigit() and len(file_name_parts[4]) != 8:
            continue

        logger.info({'message': 'listdir', 'file_name': file_name})

        rename(file_name=file_name)

    os.chdir(cwd)


if __name__ == '__main__':
    fire.Fire(rename_video_according_to_info)
