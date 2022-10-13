from collections import defaultdict
import csv
import os

import fire
import matplotlib.pyplot as plt, mpld3
from matplotlib.ticker import MaxNLocator

from my_logger import *


logger = get_logger('FrameView', level=logging.INFO)
stdout = get_logger('FrameView1', level=logging.INFO, format='')



SUMMARY_FILTER_KEYS = {
    'Avg FPS': float,
    'Min FPS': float,
    'Max FPS': float,
    '90th %': float,
    '95th %': float,
    '99th %': float,
    'Time (ms)': float,
    'RenderPresentLatency (ms)': float,
}


APP_FILTER_KEYS = {
    'Dropped': int,
    'TimeInSeconds': float,
    'MsBetweenPresents': float,
    'MsBetweenDisplayChange': float,
    'MsInPresentAPI': float,
    'MsRenderPresentLatency': float,
    'MsUntilDisplayed': float,
    'Render Queue Depth': float,
}


def plt_summary(path_summary_csv, filter_date, filter_app, file_name, file_ext):
    path_dir = os.path.dirname(path_summary_csv)
    fig_name = f'{file_name}.{file_ext}'
    fig_path = os.path.join(path_dir, fig_name)

    path_app_csv = []
    with open(path_summary_csv) as fp:
        reader = csv.reader(fp)

        filter_columns = {}
        data_columns = defaultdict(list)
        for row_index, row_data in enumerate(reader):
            if row_index == 0:
                for column_index, column_data in enumerate(row_data):
                    if column_data in SUMMARY_FILTER_KEYS:
                        filter_columns[column_index] = column_data
            else:
                if filter_date:
                    if row_data[0] < filter_date:
                        continue
                if filter_app:
                    if row_data[1] != filter_app:
                        continue

                path_app_csv.append(os.path.join(path_dir, row_data[2]))

                for column_index, column_data in enumerate(row_data):
                    if column_index not in filter_columns:
                        continue

                    key = filter_columns[column_index]
                    value = SUMMARY_FILTER_KEYS[key](column_data)
                    data_columns[key].append(value)

        fig = plt.figure(figsize=(20, 10))
        fig.subplots_adjust(hspace=1, wspace=1)
        for index, (column_name, column_values) in enumerate(data_columns.items()):
            index += 1

            logger.info({'message': 'progress', 'current': index, 'totoal': len(SUMMARY_FILTER_KEYS), 'title': column_name})

            axes = fig.add_subplot(3, 3, index)
            
            xaxis_locators = MaxNLocator(len(column_values))
            axes.xaxis.set_major_locator(xaxis_locators)
            axes.xaxis.set_major_locator(xaxis_locators)
            
            yaxis_locators = MaxNLocator(8)
            axes.yaxis.set_minor_locator(yaxis_locators) 
            axes.yaxis.set_major_locator(yaxis_locators) 

            plt.title(column_name)

            plt.xlabel('player')
            plt.ylabel(column_name.rpartition(' ')[-1].strip('()'))

            plt.plot(list(range(len(column_values))), column_values, 'red')

        plt.savefig(fig_path)

        plt.close()

    return path_app_csv


def plt_app(path_app_csv, file_index, file_prefix, file_ext):
    path_dir = os.path.dirname(path_app_csv)
    fig_name = f'{file_prefix}_{file_index}.{file_ext}'
    fig_path = os.path.join(path_dir, fig_name)

    dropped_statistics = {}

    with open(path_app_csv) as fp:
        reader = csv.reader(fp)

        filter_columns = {}
        data_columns = defaultdict(list)
        for row_index, row_data in enumerate(reader):
            if row_index == 0:
                for column_index, column_data in enumerate(row_data):
                    if column_data in APP_FILTER_KEYS:
                        filter_columns[column_index] = column_data
            else:
                for column_index, column_data in enumerate(row_data):
                    if column_index not in filter_columns:
                        continue

                    key = filter_columns[column_index]
                    try:
                        value = APP_FILTER_KEYS[key](column_data)
                    except ValueError:
                        value = 0
                    data_columns[key].append(value)

        fig = plt.figure(figsize=(20, 5 * 8))
        fig.subplots_adjust(hspace=1, wspace=1)
        for index, (column_name, column_values) in enumerate(data_columns.items()):
            index += 1

            logger.info({'message': 'progress', 'current': index, 'totoal': len(APP_FILTER_KEYS), 'title': column_name})

            axes = fig.add_subplot(8, 1, index)
            
            if column_name == 'Dropped':
                xaxis_locators = MaxNLocator(1)
                axes.xaxis.set_major_locator(xaxis_locators) 
                axes.xaxis.set_major_locator(xaxis_locators) 

                dropped_frames = sum(column_values)
                played_frames = len(column_values)
                droped_percent = dropped_frames * 100 / played_frames

                plt.title(f'{column_name} ({droped_percent:.2f}% = {dropped_frames} / {played_frames})')
     
                dropped_statistics = {'percent': droped_percent, 'frames': played_frames}
            else:            
                xaxis_locators = MaxNLocator(20)
                axes.xaxis.set_major_locator(xaxis_locators) 
                axes.xaxis.set_major_locator(xaxis_locators) 

                yaxis_locators = MaxNLocator(10)
                axes.yaxis.set_minor_locator(yaxis_locators) 
                axes.yaxis.set_major_locator(yaxis_locators) 

                plt.title(column_name)

            plt.xlabel('frame')
            plt.ylabel(column_name.rpartition(' ')[-1].strip('()'))
     
            plt.plot(list(range(len(column_values))), column_values, 'red')

        plt.savefig(fig_path)

        plt.close()

        return dropped_statistics


def statistics(path_csv, filter_date, filter_app, file_ext):
    path_summary_csv = os.path.join(path_csv, 'FrameView_Summary.csv')

    stdout.info('=' * 80)
    logger.info({'message': 'summary', 'path': os.path.basename(path_summary_csv)})
    stdout.info('=' * 80)

    try:
        path_app_csv = plt_summary(
            path_summary_csv=path_summary_csv,
            filter_date=filter_date, filter_app=filter_app,
            file_name='summary', file_ext=file_ext
        )
    except UnicodeDecodeError:
        path_app_csv = plt_summary(
            path_summary_csv=path_summary_csv + '.bak',
            filter_date=filter_date, filter_app=filter_app,
            file_name='summary', file_ext=file_ext
        )

    dropped_statistics = []
    for index, path in enumerate(path_app_csv):
        if not os.path.exists(path):
            continue

        index += 1

        stdout.info('-' * 60)
        logger.info({'message': 'app', 'current': index, 'totoal': len(path_app_csv), 'path': os.path.basename(path)})
        stdout.info('-' * 60)

        if filter_app:
            filter_app = os.path.basename(path).partition('_')[-1].partition('_')[0]
  
        result = plt_app(path_app_csv=path, file_index=index, file_prefix=os.path.splitext(filter_app)[0], file_ext=file_ext)
        dropped_statistics.append(result)

    return dropped_statistics


def batch(path, seconds=300, fps=25, filter_date='', filter_app='', file_ext='svg'):
    expect_frames = fps * seconds

    csv_count = len(os.listdir(path=path))

    fig = plt.figure(figsize=(10, 5 * csv_count))
    fig.subplots_adjust(hspace=1, wspace=1)
    
    fig_path = os.path.join(path, f'dropped.{file_ext}')

    for index, path_csv in enumerate(sorted(os.listdir(path), key=lambda s: (int(s.split('-')[1]), s.split('-')[0], int(s.split('-')[2].strip('gpu'))))):
        stdout.info('*' * 100)
        logger.info({'message': 'subdir', 'path': path_csv})
        stdout.info('*' * 100)

        percent = {'dropped': [], 'played': []}
        for item in statistics(path_csv=os.path.join(path, path_csv), filter_date=filter_date, filter_app=filter_app, file_ext=file_ext):
            percent['dropped'].append(item['percent'])
            percent['played'].append(100 * item['frames'] / expect_frames)
        
        index += 1

        axes = fig.add_subplot(csv_count, 1, index)
        
        xaxis_locators = len(percent['dropped'])
        axes.xaxis.set_major_locator(MaxNLocator(xaxis_locators)) 
        axes.xaxis.set_major_locator(MaxNLocator(xaxis_locators))
        
        yaxis_locators = 10
        axes.yaxis.set_minor_locator(MaxNLocator(yaxis_locators)) 
        axes.yaxis.set_major_locator(MaxNLocator(yaxis_locators)) 

        plt.title(path_csv)

        plt.xlabel('player')
        plt.ylabel('percent')

        x = list(range(len(percent['dropped'])))
        plt.plot(x, percent['dropped'], marker='o', color='red')
        plt.plot(x, percent['played'], marker='o', color='blue')

        for a, b in zip(x, percent['dropped']):
            plt.text(a, int(b), int(b), ha='center', va='top')

        for a, b in zip(x, percent['played']):
            plt.text(a, int(b), int(b), ha='center', va='top')

        plt.legend(['dropped', 'played'])

        stdout.info('\n##################################################')
        stdout.info(f'#################### {index * 100 / csv_count:.2f}% ####################')
        stdout.info('##################################################\n')

    plt.savefig(fig_path)

    plt.close()



if __name__ == '__main__':
    # batch(path=r"C:\Users\Administrator\Documents\FrameView\mpv_on_intel_uhd630_20220916", filter_app="mpv.exe")
    # batch(path=r"C:\Users\Administrator\Documents\FrameView\mpv 15路10分钟测试\2022-09-09 1636\FrameView数据源", filter_app="MpvServer.exe")
    # batch(path=r"E:/MpvTests/FrameView/i5-1155g7", filter_app="mpv.exe")
    fire.Fire(batch)
