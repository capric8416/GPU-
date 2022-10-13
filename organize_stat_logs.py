import json
import os
from turtle import color
import numpy
import re

import fire

import matplotlib
import matplotlib.pyplot as plt, mpld3
from matplotlib.ticker import MaxNLocator

from my_logger import *


logger = get_logger('organize')


# 设置 matplotlib 正常显示中文和负号
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False


def origanize_client(path_log, gt_datetime, eq_index, path_save_as_log, date_time_start_index=1, date_time_end_index=24):
    pattern = re.compile(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\].*sent: \d+KB')
    with open(path_log) as fp:
        data = []
        for line in fp:
            if gt_datetime and line[date_time_start_index:date_time_end_index] < gt_datetime:
                continue
            if 'Statistics' not in line:
                continue
            if f'm_index: {eq_index}' not in line:
                continue
            result = re.search(pattern=pattern, string=line)
            if not result:
                continue
            line = line[result.span()[0]:]
            line = f'''time: {line.partition(' [INFO]')[0].lstrip('[').rstrip(']')}, sent:{line.partition('sent:')[-1].rstrip().rstrip(',')}'''
            data.append({part.partition(':')[0].strip(): part.partition(':')[-1].strip() for part in line.split(',')})
        
        with open(path_save_as_log, mode='w') as fp_save_as:
            json.dump(obj=data, fp=fp_save_as)


def origanize_server(path_log, gt_datetime, path_save_as_log, date_time_start_index=1, date_time_end_index=24):
    pattern = re.compile(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\].*received: \d+KB')
    with open(path_log) as fp:
        data = []
        for line in fp:
            if gt_datetime and line[date_time_start_index:date_time_end_index] < gt_datetime:
                continue
            if '[mpv]' not in line and 'Statistics' not in line:
                continue
            result = re.search(pattern=pattern, string=line)
            if not result:
                continue
            line = line[result.span()[0]:]
            line = f'''time: {line.partition(' [INFO]')[0].lstrip('[').rstrip(']')}, received:{line.partition('received:')[-1].rstrip().rstrip(',')}'''
            data.append({part.partition(':')[0].strip(): part.partition(':')[-1].strip() for part in line.split(',')})
            
        with open(path_save_as_log, mode='w') as fp_save_as:
            json.dump(obj=data, fp=fp_save_as)


# {"time": "2022-09-22 19:12:37.376", "sent": "113KB", "total sent": "72MB", "fps": "22"}
# {"time": "2022-09-22 19:15:08.633", "received": "43KB", "total received": "94MB", "receive fps": "8", "read": "43KB", "total read": "94MB", "read fps": "8"}
def visualize(path_save_dir, id_part, path_save_as_client_log, path_save_as_server_log, fig_width_inch, fig_height_inch):
    with open(path_save_as_client_log) as fp:
        data_client = json.load(fp)

    with open(path_save_as_server_log) as fp:
        data_server = json.load(fp)

    time_begin = data_client[0]['time']
    time_end = data_client[-1]['time']
    sent_kbytes_1s = []
    receive_kbytes_1s = []
    read_kbytes_1s = []
    
    sent_mbytes_total = []
    receive_mbytes_total = []
    read_mbytes_total = []

    sent_fps = []
    receive_fps = []
    read_fps = []

    for client_stat, server_stat in zip(data_client, data_server):
        sent_kbytes_1s.append(int(client_stat["sent"].rstrip('KB')))
        sent_mbytes_total.append(int(client_stat["total sent"].rstrip('MB')))
        sent_fps.append(int(client_stat["fps"]))

        receive_kbytes_1s.append(int(server_stat["received"].rstrip('KB')))
        receive_mbytes_total.append(int(server_stat["total received"].rstrip('MB')))
        receive_fps.append(int(server_stat["receive fps"]))

        read_kbytes_1s.append(int(server_stat["read"].rstrip('KB')))
        read_mbytes_total.append(int(server_stat["total read"].rstrip('MB')))
        read_fps.append(int(server_stat["read fps"]))

    fig = plt.figure(figsize=(fig_width_inch, fig_height_inch))
    fig.subplots_adjust(hspace=1, wspace=1)

    titles = ('每秒数据量 (KB)', '总数据量 (MB)', '帧率')
    x_labels = ('seconds',) * 3
    y_labels = ('KB', 'MB', '')
    colors = ('red', 'green', 'blue')
    legends = (
        ('FLV拉流 (sent_kbytes_1s)', '播放器送解码 (read_kbytes_1s)', '播放器收流 (receive_kbytes_1s)'),
        ('FLV拉流 (sent_mbytes_total)', '播放器收流 (receive_mbytes_total)', '播放器送解码 (read_mbytes_total)'),
        ('FLV拉流 (sent_fps)', '播放器收流 (receive_fps)', '播放器送解码 (read_fps)')
    )
    datas = (
        (sent_kbytes_1s, read_kbytes_1s, receive_kbytes_1s),
        (sent_mbytes_total, receive_mbytes_total, read_mbytes_total),
        (sent_fps, receive_fps, read_fps),
    )
    for index in range(0, 3):
        axes = fig.add_subplot(3, 1, index + 1)

        seconds = len(datas[index][0])

        xaxis_locators = 50
        axes.xaxis.set_major_locator(MaxNLocator(xaxis_locators)) 
        axes.xaxis.set_major_locator(MaxNLocator(xaxis_locators))
        
        yaxis_locators = 10
        axes.yaxis.set_minor_locator(MaxNLocator(yaxis_locators)) 
        axes.yaxis.set_major_locator(MaxNLocator(yaxis_locators)) 

        plt.title(titles[index])

        plt.xlabel(f'from {time_begin} to {time_end} play {seconds} {x_labels[index]}', loc='left')
        plt.ylabel(y_labels[index])

        y_max = 0
        for items in datas[index]:
            y_max = max(y_max, *items)
        stat = []
        for j, items in enumerate(datas[index]):
            plt.plot(list(range(len(items))), items, color=colors[j])

            stat.append(
                f'{legends[index][j]}    '
                f'平均值: {int(numpy.mean(items))}, '
                f'中位数: {int(numpy.median(items))}, '
                f'众数: {int(numpy.argmax(numpy.bincount(items)))}, '
                f'90分位数: {int(numpy.percentile(items, 0.90))}, '
                f'95分位数: {int(numpy.percentile(items, 0.95))}, '
                f'99分位数: {int(numpy.percentile(items, 0.99))}, '
                f'标准差: {int(numpy.std(items))}'
            )

        plt.text(x=0, y=y_max, s='\n\n'.join(stat))
            
        plt.legend(legends[index], loc='upper left')

    plt.savefig(os.path.join(path_save_dir, id_part + '.svg'), bbox_inches='tight')

    plt.close()


def organize(path_log_dir, client_log_name='client', server_log_name='server', eq_index=0, gt_datetime='', id_part='', path_save_as_dir=None, fig_width_inch=200, fig_height_inch=30):
    if not path_save_as_dir:
        path_save_as_dir = path_log_dir

    path_client_log = os.path.join(path_log_dir, f'{client_log_name}.log')
    path_server_log = os.path.join(path_log_dir, f'{server_log_name}.{eq_index}.log')

    path_save_as_client_log = os.path.join(path_save_as_dir, f'{client_log_name}.{id_part}.log')
    path_save_as_server_log = os.path.join(path_save_as_dir, f'{server_log_name}.{id_part}.log')

    origanize_client(path_log=path_client_log, gt_datetime=gt_datetime, eq_index=eq_index, path_save_as_log=path_save_as_client_log)
    origanize_server(path_log=path_server_log, gt_datetime=gt_datetime, path_save_as_log=path_save_as_server_log)

    visualize(path_save_dir=path_save_as_dir, id_part=id_part, path_save_as_client_log=path_save_as_client_log, path_save_as_server_log=path_save_as_server_log, fig_width_inch=fig_width_inch, fig_height_inch=fig_height_inch)


if __name__ == '__main__':
    # organize(
    #     path_log_dir=r'C:\Users\Administrator\AppData\Roaming\mpv_helper_client',
    #     eq_index=0, gt_datetime='2022-09-22 21:38:09.568', id_part='192.168.11.11',
    #     path_save_as_dir='stat_logs', fig_width_inch=100, fig_height_inch=30,
    # )
    fire.Fire(organize)
