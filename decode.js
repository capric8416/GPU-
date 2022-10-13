/*
2022-07-29 丁家佳
这是一个命令行脚本，不走ffi交互，仅供用于可行性验证
*/

/* 变更历史
2022-07-29 创建
    一个命令行脚本，将指定的url按照指定的帧率转换成图片
    输出图片文件到磁盘，可以指定清理间隔
    -> 存在3个问题
        a. 清理太快，导致electron读的比较慢，图片已经被清理了
        b. 支持硬解码配置
        c. 提供给接口给外部调用来清理图片文件

2022-08-01 变更
    a. 更好的与electron集成，结束时退出ffmpeg子进程
    b. 提供接口给外部调用来清理文件
    c. 支持硬解码配置

2022-08-03 沟通
    Q: 会不会发生ffmpeg解码或者输出太慢，而electron读取太快，导致没有读取到图片
    A: 会，当electron没有读取图片时，不应该更新img标签的src属性，也许还可以叠加一个loading.gif
*/

// 官方文档
// https://trac.ffmpeg.org/wiki/Create%20a%20thumbnail%20image%20every%20X%20seconds%20of%20the%20video


const lib_fs = require("fs")
const lib_path = require("path")
const lib_child_process = require("child_process")


class FFmpegDecoderCli {
    /*
    使用说明：
    1. 通过构造函数传递 Object 来配置
    2. 开始使用时调用 start
    3. 结束使用时调用 stop
    4. 使用过程中间定期调用 remove_image_files 来清理图片文件
    */
    constructor(options) {
        // 配置ffmpeg
        this.configure(options || {})

        // 内部使用：ffmpeg子进程
        this.ffmpeg_process = null
    }

    /*
    配置ffmpeg参数
    */
    configure(options) {
        // 必选配置：ffmpeg可执行文件路径, 默认为当前目录下的ffmpeg.exe
        if (typeof (options.ffmpeg_path) == 'string') {
            this.ffmpeg_path = options.ffmpeg_path
        } else {
            this.ffmpeg_path = 'ffmpeg.exe'
        }

        // 必选配置：输入视频流或者文件，比如说rtsp流/http流/本地文件
        if (typeof (options.input_video_url) == 'string') {
            this.input_video_url = options.input_video_url
        } else {
            this.input_video_url = 'rtsp://admin:haikang0088@192.168.29.101/ch1/main/av_stream'
        }

        // 必选配置：输出图片路径，此目录需要手动创建，建议放在系统临时路径
        if (typeof (options.output_images_dir) == 'string') {
            this.output_images_dir = options.output_images_dir
        } else {
            this.output_images_dir = 'C:/Users/Administrator/AppData/Local/Temp/zzzzzzzzzzzzz'
        }

        // 必选配置：输出图片文件通配名
        if (typeof (options.output_image_file_pattern) == 'string') {
            this.output_image_file_pattern = options.output_image_file_pattern
        } else {
            this.output_image_file_pattern = '%d.png'
        }

        // 内部使用
        // ffmpeg视频帧输出图片完整路径(带通配符)
        this.__output_image_files_pattern = lib_path.join(this.output_images_dir, this.output_image_file_pattern)

        // fps (frame rate per second) = fps_number / fps_den
        // 比如说一秒钟输出一帧，fps_number = 1, fps_den = 1
        // 再比如说一分钟输出一帧，fps_number = 1, fps_den = 60
        // 必选配置
        if (typeof (options.fps_number) == 'number') {
            this.fps_number = options.fps_number
        } else {
            this.fps_number = 1
        }
        // 必选配置
        if (typeof (options.fps_den) == 'number') {
            this.fps_den = options.fps_den
        } else {
            this.fps_den = 1
        }

        // 必选配置：指定硬件加速，默认dxva2，可选d3d11va (Windows)
        if (typeof (options.hwaccel) == 'string') {
            this.hwaccel = options.hwaccel
        } else {
            this.hwaccel = 'dxva2'  // or d3d11va
        }

        // 可选配置：其它ffmpeg参数
        if (typeof (options.extra_parameters) == 'object') {
            this.extra_parameters = options.extra_parameters
        } else {
            this.extra_parameters = []
        }

        // 可选配置：ffmpeg标准输出
        if (typeof (options.on_ffmpeg_stdout) == 'function') {
            this.on_ffmpeg_stdout = options.on_ffmpeg_stdout
        } else if (options.on_ffmpeg_stdout === undefined) {
            this.on_ffmpeg_stdout = null
        } else {
            this.on_ffmpeg_stdout = (data) => {
                console.log(`ffmpeg stdout: ${data}`)
            }
        }
        // 可选配置：ffmpeg错误输出
        if (typeof (options.on_ffmpeg_stderr) == 'function') {
            this.on_ffmpeg_stderr = options.on_ffmpeg_stderr
        } else if (options.on_ffmpeg_stderr === undefined) {
            this.on_ffmpeg_stderr = null
        } else {
            this.on_ffmpeg_stderr = (data) => {
                console.log(`ffmpeg stderr: ${data}`)
            }
        }
        // 可选配置：ffmpeg退出码
        if (typeof (options.on_ffmpeg_exit) == 'function') {
            this.on_ffmpeg_exit = options.on_ffmpeg_exit
        } else if (options.on_ffmpeg_exit === undefined) {
            this.on_ffmpeg_exit = null
        } else {
            this.on_ffmpeg_exit = (code, signal) => {
                console.log(`ffmpeg exit with code: ${code}`)
            }
        }
    }

    /*
    启动
    */
    start() {
        this.start_ffmpeg_process()
    }

    /*
    停止
    */
    stop() {
        this.stop_ffmpeg_process()

        this.remove_image_files()
    }

    /*
    启动ffmpeg子进程
    */
    start_ffmpeg_process() {
        // 运行ffmpeg子进程

        // 构建命令行参数
        let args = [
            '-loglevel', 'warning',
            '-hwaccel', this.hwaccel,
            '-i', this.input_video_url,
            '-vf',
            `fps=${this.fps_number / this.fps_den}`
        ]
        args.push(...this.extra_parameters)
        args.push(this.__output_image_files_pattern)
        console.log(this.ffmpeg_path, args)

        this.ffmpeg_process = lib_child_process.spawn(this.ffmpeg_path, args)

        // 捕获标准输出
        if (this.on_ffmpeg_stdout) {
            this.ffmpeg_process.stdout.on('data', this.on_ffmpeg_stdout)
        }

        // 捕获标准错误输出
        if (this.on_ffmpeg_stderr) {
            this.ffmpeg_process.stderr.on('data', this.on_ffmpeg_stderr)
        }

        // 注册子进程关闭事件 
        if (this.on_ffmpeg_exit) {
            this.ffmpeg_process.on('exit', this.on_ffmpeg_exit)
        }
    }

    /*
    停止ffmpeg子进程
    */
    stop_ffmpeg_process() {
        if (this.ffmpeg_process) {
            this.ffmpeg_process.stdin.pause();
            this.ffmpeg_process.kill();
        }
    }

    /*
    遍历图片输出目录
    如果设置了birthtimeMs，则删除早于birthtimeMs的文件
    否则，直接清理文件
    */
    remove_image_files({ birthtimeMs } = {}) {
        let _this = this

        if (_this.__removing_files) {
            return
        }

        let files = lib_fs.readdirSync(_this.output_images_dir)
        let count = files.length
        if (count == 0) {
            return
        }

        _this.__removing_files = true

        files.forEach((file_name) => {
            let path = lib_path.join(_this.output_images_dir, file_name)
            if (lib_fs.existsSync(path)) {
                let stat = lib_fs.statSync(path)
                if (stat.isFile()) {
                    if (!birthtimeMs) {
                        _this.try_to_remove_file({ path: path })
                    } else {
                        if (stat.birthtimeMs < birthtimeMs) {
                            _this.try_to_remove_file({ path: path })
                        }
                    }
                }
            }

            count--
            if (count <= 0) {
                _this.__removing_files = false
            }
        })
    }

    /*
    尝试去删除文件，可设置成功/失败回调
    */
    try_to_remove_file({ path, on_error, on_ok }) {
        lib_fs.unlink(path, (error) => {
            if (error) {
                if (typeof (on_error) == 'function') {
                    on_error(error, path)
                } else {
                    console.error(`try_to_remove_file, path: ${path}, error: ${error}`)
                }
            } else {
                if (typeof (on_ok) == 'function') {
                    on_ok(path)
                }
            }
        })
    }
}


// 示例/最佳实践：请在外部配置参数，而不是使用内部默认参数
let cli = new FFmpegDecoderCli({
    ffmpeg_path: 'ffmpeg.exe',
    input_video_url: 'rtsp://admin:haikang0088@192.168.29.101/ch1/main/av_stream',
    output_images_dir: 'C:/Users/Administrator/AppData/Local/Temp/zzzzzzzzzzzzz',
    output_image_file_pattern: '%d.png',
    fps_number: 25,
    fps_den: 1,
    hwaccel: 'd3d11va',
    extra_parameters: [],
    on_ffmpeg_stdout: (data) => {
        console.log(`ffmpeg stdout: ${data}`)
    },
    on_ffmpeg_stderr: (data) => {
        console.log(`ffmpeg stderr: ${data}`)
    },
    on_ffmpeg_exit: (code, signal) => {
        console.log(`ffmpeg exit with code: ${code}`)
    }
})
cli.start()


// 示例：清理5秒前的图片
let interval = 1000 * 5
let timer = setInterval(() => {
    let ts = (new Date()).getTime() - interval // 毫秒时间戳
    cli.remove_image_files.apply(cli, [{ birthtimeMs: ts }])
}, interval)


// 示例：运行30秒后停止
let timeout = 1000 * 30
setTimeout(() => {
    clearInterval(timer)

    cli.stop()

}, timeout);

