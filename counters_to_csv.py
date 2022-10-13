import csv
import json
import traceback

import fire


header = [
    'time',
    'cpu percentage (%)',
    'memory usage (MB)',
    'gpu engtype_3d utilization percentage (%)',
    'gpu engtype_videodecode utilization percentage (%)',
    'gpu process memory local usage (MB)',
    'gpu process memory dedicated usage (MB)',
    'gpu process memory shared usage (MB)',
]


def convert(file_path, date_time=''):
    with open(file=file_path + '.csv', mode='w', encoding='utf-8', newline='') as fp_csv:
        csv_writer = csv.writer(fp_csv)

        # 逐行处理比较复杂，因为会有字段缺失，所以直接加载进内存
        with open(file_path) as fp_counters:
            text = fp_counters.read()

         # 表头
        csv_writer.writerow(header)

        previous_row = []
        for block in text.split('\n\n'):
            current_row = []

            line_no = 0
            line_text = block.split('\n')
            for index, title in enumerate(header):
                line = line_text[line_no]
                if line.startswith(f'''{{"counter": "{title.partition(' (')[0]}"'''):
                    try:
                        # 从json解析
                        data = json.loads(line)
                        value = data['text']
                    except Exception as e:
                        # 从字符串分割
                        value = line.partition('"text": "')[-1].partition('"}')[0]

                    # 跳过大于某个日期时间的数据
                    if title == 'time' and date_time and value > date_time:
                        break

                    # 移除末尾的可读性符号
                    current_row.append(value.rstrip('%').rstrip('MB').rstrip('ms'))

                    line_no += 1
                else:
                    # 使用上一行的值填充空字段
                    if previous_row:
                        current_row.append(previous_row[index])
                    # 使用零值填充空字段
                    else:
                        current_row.append(0)

            if current_row:     
                csv_writer.writerow(current_row)
                # previous_row = current_row


if __name__ == '__main__':
    """
    python counters_to_csv.py --file_path='MpvHelperApp.counters' --date_time='2022-08-12 12:10:39.162'
    """
    # convert(file_path='MpvHelperApp.counters', date_time='2022-08-12 12:10:39.162')
    # convert(file_path='mpv.counters')
    fire.Fire(convert)
