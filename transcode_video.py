import os
import shutil
import subprocess

import fire

from timeit import *
from my_logger import *


logger = get_logger('ffmpeg', level=logging.DEBUG)


def count_files_in_dir(path):
    return len(os.listdir(path=path))


def build_output_dir_path(input_name, output_dir_path, output_ext, output_resolution, silent_remove):
    if output_dir_path != '/dev/null':
        output_dir_path = f'{output_dir_path}/{input_name.partition(".")[0]}/{output_resolution}'
        if os.path.exists(output_dir_path):
            output_file_counts = count_files_in_dir(path=output_dir_path)
            if output_file_counts > 0:
                will_remove = True
                if not silent_remove:
                    will_remove = input(
                        f'There are {output_file_counts} {output_ext} files in {output_dir_path}, '
                        f'are you sure to remove them? press y|yes|ok|sure to remove: '
                    ) in ('y', 'yes', 'ok', 'sure')
                else:
                    logger.debug({
                        'message': 'remove files', 'count': output_file_counts,
                        'type': output_ext, 'path': output_dir_path
                    })
                if will_remove:
                    shutil.rmtree(path=output_dir_path, ignore_errors=True)
        os.makedirs(output_dir_path, exist_ok=True)

    return output_dir_path


@timeit
def run_ffmpeg_process(
    index,
    debug,
    loglevel,
    hwaccel,
    hwaccel_output_format,
    hwaccel_device,
    hwaccel_vf_scale,
    extra_hw_frames,
    input_url,
    input_video_codec,
    output_video_codec,
    output_video_bitrate,
    output_dir_path,
    output_name_pattern,
    output_resolution,
    is_need_scale
):
    args = [
        'ffmpeg',
        '-loglevel', loglevel,
        '-vsync', '0'
    ]
    if hwaccel:
        args += ('-hwaccel', hwaccel)
    if hwaccel_output_format:
        args += ('-hwaccel_output_format', hwaccel_output_format)
    if str(hwaccel_device):
        args += ('-hwaccel_device', str(hwaccel_device))
    if str(extra_hw_frames):
        args += ('-extra_hw_frames', str(extra_hw_frames))
    if input_video_codec:
        args += ('-c:v', input_video_codec)
    if input_url:
        args += ('-i', input_url)
    if output_video_codec:
        args += ('-c:v', output_video_codec)
    if output_video_bitrate:
        args += ('-b:v', output_video_bitrate)
    if is_need_scale and hwaccel_vf_scale and output_resolution:
        args += ('-vf', f'scale_{hwaccel_vf_scale}={output_resolution.replace("x", ":")}')

    if output_dir_path == '/dev/null':
        args.append(output_dir_path)
    else:
        args.append(f'{output_dir_path}/{output_name_pattern}')

    if not debug:
        logger.debug({'message': 'subprocess run', 'index': index, 'args': args})

        subprocess.run(args=args)
    else:
        logger.debug({'message': ' '.join(args)})


def transcode(
    index=0,
    debug=False,
    loglevel='warning',
    hwaccel='',
    hwaccel_output_format='',
    hwaccel_device='',
    hwaccel_vf_scale='',
    extra_hw_frames='',
    input_url='',
    input_video_codec='',
    output_video_codec='',
    output_video_bitrate='',
    output_dir_path='',
    output_name_pattern='',
    output_resolution='',
    silent_remove=False
):
    # 转换成完整路径
    input_url = os.path.abspath(input_url)
    output_dir_path = os.path.abspath(output_dir_path)

    # 获取输入文件名
    input_name = os.path.basename(input_url)
    output_ext = output_name_pattern.rpartition('.')[-1]

    # 从输入文件名提取分辨率
    is_need_scale = False
    input_resolution = input_name.split('.')[1]
    if not output_resolution:
        output_resolution = input_resolution
    else:
        is_need_scale = output_resolution != input_resolution

    # 拼接输出文件路径，如果路径不存在则去创建，如果文件已存在，提示清理
    output_dir_path = build_output_dir_path(
        input_name=input_name, output_dir_path=output_dir_path,
        output_ext=output_ext, output_resolution=output_resolution,
        silent_remove=silent_remove
    )

    # 启动ffmpg转码
    elasped_seconds, *_ = run_ffmpeg_process(
        index=index,
        debug=debug,
        loglevel=loglevel,
        hwaccel=hwaccel,
        hwaccel_output_format=hwaccel_output_format,
        hwaccel_device=hwaccel_device,
        hwaccel_vf_scale=hwaccel_vf_scale,
        extra_hw_frames=extra_hw_frames,
        input_url=input_url,
        input_video_codec=input_video_codec,
        output_video_codec=output_video_codec,
        output_video_bitrate=output_video_bitrate,
        output_dir_path=output_dir_path,
        output_name_pattern=output_name_pattern,
        output_resolution=output_resolution,
        is_need_scale=is_need_scale
    )

    # 统计输出目录文件数
    if any([
        output_name_pattern.endswith('.png'),
        output_name_pattern.endswith('.webp'),
        output_name_pattern.endswith('.jpg'),
        output_name_pattern.endswith('.jpeg'),
        output_name_pattern.endswith('.bmp')
    ]):
        output_file_counts = count_files_in_dir(output_dir_path)
    else:
        output_file_counts = int(input_name.split('.')[4])
    logger.debug({
        'message': 'transcode to files', 'count': output_file_counts,
        'type': output_ext, 'resolution': output_resolution,
        'is_scaled': is_need_scale,
        'elasped_seconds': elasped_seconds,
        'speed_per_second': output_file_counts / elasped_seconds
    })

    return elasped_seconds, output_file_counts, output_resolution, output_ext, is_need_scale


def benchmark(times=1, **kwargs):
    elasped_seconds = 0.0
    output_files = 0
    output_resolution = ''
    output_extension = ''
    is_ouput_scaled = False
    for index in range(times):
        elasped, count, output_resolution, output_extension, is_ouput_scaled = \
            transcode(index=index, **kwargs)
        elasped_seconds += elasped
        output_files += count

    logger.info({
        'message': 'transcode to files', 'count': output_files,
        'type': output_extension, 'resolution': output_resolution,
        'is_scaled': is_ouput_scaled,
        'elasped_seconds': elasped_seconds,
        'speed_per_second': output_files / elasped_seconds
    })


if __name__ == '__main__':
    # python transcode_video.py --loglevel=warning --hwaccel=cuda --hwaccel_output_format=cuda --hwaccel_device=0 --hwaccel_vf_scale=npp --extra_hw_frames=8 --input_url="../video/UnrealEngine4ElementalDemo.1920x1080.h264.60fps.9844.00024407.4608kbps.mp4" --output_video_codec=h264_nvenc --output_video_bitrate=2M --output_dir_path="../image" --output_name_pattern="test.264" --output_resolution="640x480" --silent_remove=True --times=1 --debug=True

    # python transcode_video.py --loglevel=warning --hwaccel=qsv --hwaccel_output_format=cuda --hwaccel_vf_scale=qsv --input_url="../video/UnrealEngine4ElementalDemo.1920x1080.h264.60fps.9844.00024407.4608kbps.mp4" --output_video_codec=h264_qsv --output_video_bitrate=2M --output_dir_path="../image" --output_name_pattern="test.264" --output_resolution="640x480" --silent_remove=True --times=1 --debug=True

    # benchmark(
    #     loglevel='verbose',
    #     hwaccel='cuda',
    #     hwaccel_output_format='cuda',
    #     hwaccel_device='0',
    #     hwaccel_vf_scale='npp',
    #     extra_hw_frames='8',
    #     input_url='../video/UnrealEngine4ElementalDemo.1920x1080.h264.60fps.9844.00024407.4608kbps.mp4',
    #     output_video_codec='h264_nvenc',
    #     output_video_bitrate='2M',
    #     output_dir_path='../image',
    #     output_name_pattern='test.264',
    #     output_resolution='640x480',
    #     silent_remove=True,
    #     times=1,
    #     debug=False
    # )

    fire.Fire(benchmark)
