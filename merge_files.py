import os
import traceback

import fire

def merge_files(dir_path, file_template, target_name, max_errors_allowd = 0):
    if not os.path.exists(dir_path):
        print(f'path "{dir_path}" was not found')
        return

    if not os.path.isdir(dir_path):
        print(f'path "{dir_path}" is not a directory')
        return

    errors = 0
    with open(f'{dir_path}.{target_name}', 'wb') as fp_merged:
        i = 0
        while True:
            try:
                with open(f'{dir_path}/{file_template.format(i)}', 'rb') as fp:
                    fp_merged.write(fp.read())
            except Exception as _:
                traceback.print_exc()
                errors += 1
                if errors >= max_errors_allowd:
                    print(f'{errors} occurs, break')
                    break

            i += 1


if __name__ == '__main__':
    """
    python merge_files.py --dir_path="C:/Users/Administrator/AppData/Roaming/MpvHelper/ch_tmp/wangjinqiangji02_2208241400.frames" --file_template="{}.265" --target_name="merged.265" --max_errors_allowd=0
    """
    fire.Fire(merge_files)
