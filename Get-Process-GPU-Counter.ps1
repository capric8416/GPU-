# 命令行参数: 进程名
param(
    [Parameter()]
    [String]$name, # 进程名
    [Int32]$interval   # 执行一次查询后等待的秒数
)

# 进程名为空则退出
if ([string]::IsNullOrEmpty($name)) {
    Write-Error "Empty process name was not allowed!"
    Exit(-1)
}

# 如果interval参数值过小，实际上间隔可能大于指定的秒数
if ($interval -eq 0) {
    $interval = 1
}

$engtype = ".*_(engtype.*)\)\\(.*)"
$memorytype = ".*\\(gpu.*)\(.*\)\\(.*)"

while ($true) {
    # 如果找不到进程则重试
    $p = Get-Process $name
    if (!$p) {
        Write-Error "Process was not found!"
        Start-Sleep -Seconds ($interval * 3)
        continue
    }

    # 记录任务开始时间
    $time = [string]::Format('"time": "{0}"', $(Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"))
    Write-Output "{$time}"

    # CPU占用
    (Get-Counter "\Process($name)\% Processor Time").CounterSamples | ForEach-Object {
        $json = [string]::Format('"counter": "cpu percentage", "value": {0}, "text": "{1}"', $_.CookedValue, "$([math]::Round($_.CookedValue, 2))%")
        Write-Output "{$json}"
    }

    # 内存使用
    $ws = 0
    $p | ForEach-Object {
        $ws += $_.WS
    }
    $json = [string]::Format('"counter": "memory usage", "value": {0}, "text": "{1}"', $ws, "$([math]::Round($ws/1MB, 2))MB")
    Write-Output "{$json}"
    
    # 获取GPU Unit列表
    $names = Get-Counter -ListSet 'GPU*' | findstr 'CounterSetName'
    ForEach ($line in $names -split "`r`n") {
        $parts = $line -split ":"
        $counterSet = $parts[1].Trim() -replace '.*\[\d+(;\d+)?m'

        # 获取每个GPU Unit使用或者占用
        $kv = @{}
        if ($counterSet -eq "GPU Engine") {
            # GPU引擎占用
            $p | ForEach-Object {
                (Get-Counter "\$($counterSet)(pid_$($_.id)*engtype*)\*").CounterSamples  | Where-Object CookedValue  | ForEach-Object {
                    $k = $_.Path -replace $engtype, '$1 $2'
                    $k = "gpu " + $k
                    if (!$kv.ContainsKey($k)) {
                        $kv[$k] = 0
                    }
                    $kv[$k] += $_.CookedValue
                }
            }
        }
        else {
            # GPU内存使用
            $p | ForEach-Object {
                (
                    (Get-Counter "\$($counterSet)(pid_$($_.id)*)\*").CounterSamples | Where-Object CookedValue
                ) | ForEach-Object {
                    $k = $_.Path -replace $memorytype, '$1 $2'
                    if (!$kv.ContainsKey($k)) {
                        $kv[$k] = 0
                    }
                    $kv[$k] += $_.CookedValue
                }
            }
        }
        
        # 格式化输出每个GPU Unit的使用或者占用情况
        $kv.GetEnumerator() | ForEach-Object {
            $readability = ""
            if ($_.Key -match "engtype") {
                # percentage
                if ($_.Key -match "percentage") {
                    $readability = "$([math]::Round($_.Value, 2))%"
                }
                # running time
                else {
                    # 如何获取时间基
                    # $counter = Get-Counter "counter path"
                    # $counter.CounterSamples | Format-List -Property TimeBase
                    $readability = "$([math]::Round($_.Value/10000000, 0))ms"
                }
            }
            else {
                # memory usage
                $readability = "$([math]::Round($_.Value/1MB, 2))MB"
            }
            $json = [string]::Format('"counter": "{0}", "value": {1}, "text": "{2}"', $_.Key, $_.Value, $readability)
            Write-Output "{$json}"
        }
    }

    # 输出空行
    Write-Output ""

    # # 等待若干秒
    # Start-Sleep -Seconds $interval
}

