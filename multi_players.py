import multiprocessing
import subprocess
import threading
import time

import fire
import win32api
import win32con
import win32gui

from pool import ProcessPool


class MultiPlayers:
    def __init__(
            self,
            player_index: int = 0,
            player_name: str = 'ffplay',
            horizontal_ways: int = 1,
            vertical_ways: int = 1,
            input_url: str = '',
            player_extra: str = '--hwdec=d3d11va'
    ):
        """
        初始化播放器参数

        会启动 horizontal_ways * vertical_ways 个播放器

        参数
        ----------
        player_index : str
            播放器程序名后缀索引
        player_name : str
            播放器名字,
            目前支持 ffplay | vlc | mpv | potplayer,
            使用前安装好这些程序并将其执行程序所在的路径加到环境变量PATH中.
        horizontal_ways : int
            单行(水平方向上)放置多少个播放器
        vertical_ways : int
            单列(垂直方向上)放置多少个播放器
        input_url : str
            要传递给播放器打开的资源地址
        player_extra : str
            传递给播放器的其它参数
        """
        
        self.player_index = player_index

        if not player_name or not len(player_name.strip()):
            print('empty player_name was not allowed, available players: ffplay, vlc, mpv, potplayer')
            return

        if not input_url or not len(input_url.strip()):
            print('empty input_url was not allowed')
            return

        if horizontal_ways < 1 or horizontal_ways > 8:
            print('horizontal_ways must be in range [1, 8]')
            return

        if vertical_ways < 1 or vertical_ways > 8:
            print('vertical_ways must be in range [1, 8]')
            return

        self.player_name = player_name
        self.player_launcher = {
            'ffplay': self.launch_ffplay,
            'vlc': self.launch_vlc,
            'mpv': self.launch_mpv,
            'potplayer': self.launch_potplayer
        }[self.player_name]

        self.horizontal_ways = horizontal_ways
        self.vertical_ways = vertical_ways
        self.input_url = input_url
        self.player_extra = player_extra
        self.screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)  # 获得主屏幕分辨率X轴
        self.screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)  # 获得主屏幕分辨率Y轴

        self.process_pool = ProcessPool(max_workers=self.horizontal_ways * self.vertical_ways)

    def start(self):
        """
        根据初始化播放器参数的启动多个播放器
        """

        # 每个播放器的宽高
        width = self.screen_width // self.horizontal_ways
        height = self.screen_height // self.vertical_ways

        # 多进程共享变量和锁
        share_locker = multiprocessing.Manager().Lock()
        share_tasks = multiprocessing.Manager().dict()

        # 启动播放器
        top = 0
        index = 0
        for row in range(self.vertical_ways):
            left = 0
            for col in range(self.horizontal_ways):
                kwargs = dict(
                    index=index, left=left, top=top, width=width, height=height, input_url=self.input_url,
                    player_extra=self.player_extra, share_locker=share_locker, share_tasks=share_tasks
                )
                self.process_pool.submit(notify=None, task=self.player_launcher, **kwargs)
                left += width
                index += 1

            top += height

        # 等待播放器进程都启动起来
        while True:
            with share_locker:
                if len(share_tasks) < self.horizontal_ways * self.vertical_ways:
                    time.sleep(0.5)  # 等待0.5s
                else:
                    break

        # 等待播放器进程都退出
        self.process_pool.stop()

    @staticmethod
    def launch_ffplay(player_index, index, left, top, width, height, input_url, player_extra, share_locker, share_tasks):
        window_title = MultiPlayers.build_window_title('ffplay', index, left, top, width, height)

        MultiPlayers.process_launched(share_locker, share_tasks, index, window_title)

        cmd_line = f'ffplay -x {width} -y {height} -left {left} -top {top} -window_title "{window_title}" {player_extra} -i "{input_url}"'
        MultiPlayers.run_process(cmd_line)

    @staticmethod
    def launch_vlc(player_index, index, left, top, width, height, input_url, player_extra, share_locker, share_tasks):
        window_title = MultiPlayers.build_window_title('vlc', index, left, top, width, height)

        MultiPlayers.process_launched(share_locker, share_tasks, index, window_title)

        MultiPlayers.find_and_move_window(window_title, left, top, width, height)

        """
        --avcodec-hw=d3d11va
        --avcodec-hw=dxva2
        """
        cmd_line = f'start cmd /c vlc --no-embedded-video --video-on-top --video-title="{window_title}" {player_extra} "{input_url}" -v ^> "{window_title}-try-{player_extra.partition("=")[-1]}.log"'
        MultiPlayers.run_process(cmd_line)

    @staticmethod
    def launch_mpv(player_index, index, left, top, width, height, input_url, player_extra, share_locker, share_tasks):
        window_title = MultiPlayers.build_window_title('mpv', index, left, top, width, height)

        MultiPlayers.process_launched(share_locker, share_tasks, index, window_title)

        MultiPlayers.find_and_move_window(window_title, left, top, width, height)

        """
        --hwdec=d3d11va
        --hwdec=dxva2
        """
        # cmd_line = f'start cmd /c mpv --title="{window_title}" --geometry="{width}x{height}" {player_extra} "{input_url}" -v ^> "{window_title}-try-{player_extra.partition("=")[-1]}.log"'
        cmd_line = f'mpv{player_index} --title="{window_title}" --geometry="{width}x{height}" {player_extra} "{input_url}" -v'
        MultiPlayers.run_process(cmd_line)

    @staticmethod
    def launch_potplayer(player_index, index, left, top, width, height, input_url, player_extra, share_locker, share_tasks):
        window_title = MultiPlayers.build_window_title('potplayer', index, left, top, width, height)

        MultiPlayers.process_launched(share_locker, share_tasks, index, window_title)

        MultiPlayers.find_and_move_window(window_title + ' - PotPlayer', left, top, width, height)

        cmd_line = f'PotPlayerMini64 "{input_url}" {player_extra} /title="{window_title}"'
        MultiPlayers.run_process(cmd_line)

    @staticmethod
    def build_window_title(player, index, left, top, width, height):
        return f'{player}#{index}@{left}.{top}.{width}.{height}'''

    @staticmethod
    def process_launched(share_locker, share_tasks, index, window_title):
        with share_locker:
            share_tasks[index] = window_title

    @staticmethod
    def run_process(cmd_line):
        print(cmd_line)
        subprocess.run(cmd_line)

    @staticmethod
    def find_and_move_window(window_title, left, top, width, height):
        threading.Thread(
            target=MultiPlayers.move_player_window,
            kwargs=dict(window_title=window_title, left=left, top=top, width=width, height=height)
        ).start()

    @staticmethod
    def move_player_window(window_title, left, top, width, height):
        # 如果无法根据窗口标题找到窗口
        # 可以根据win32gui.EnumWindows与win32process.GetWindowThreadProcessId来匹配
        # 注意subprocess.Popen当shell参数为False时返回值.pid才是播放器进程id
        tries = 0
        while True:
            hwnd = win32gui.FindWindow(None, window_title)
            if hwnd:
                win32gui.MoveWindow(hwnd, left, top, width, height, False)
                tries += 1
                if tries > 10:
                    break
            time.sleep(0.5)


if __name__ == '__main__':
    """
    python multi_players.py start --player_name=mpv --horizontal_ways=1 --vertical_ways=1 --input_url="test.265" --player_extra="--hwdec=dxva2"
    """
    fire.Fire(MultiPlayers)
