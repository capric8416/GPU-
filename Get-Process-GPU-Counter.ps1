# 命令行参数: 进程名
param(
    [Parameter()]
    [String]$process,  # 进程名
    [Int32]$interval   # 执行一次查询后等待的秒数
)

# 每秒输出一次，实际上间隔可能大于1秒
$p = Get-Process $process

$engtype = ".*_(engtype.*)\)\\(.*)"
$memorytype = ".*\\(gpu.*)\(.*\)\\(.*)"

while ($true) {
    # 记录任务开始时间
    $time = [string]::Format('"time": "{0}"', $(Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"))
    Write-Output "{$time}"
    
    $names = Get-Counter -ListSet 'GPU*' | findstr 'CounterSetName'
    ForEach ($line in $names -split "`r`n") {
        $parts = $line -split ":"
        $counterSet = $parts[1].Trim() -replace '.*\[\d+(;\d+)?m'

        $kv = @{}
        if ($counterSet -eq "GPU Engine") {
            # GPU引擎占用
            (
                (Get-Counter "\$($counterSet)(pid_$($p.id)*engtype*)\*").CounterSamples  | Where-Object CookedValue
            ) | ForEach-Object {
                $k = $_.Path -replace $engtype, '$1 $2'
                if (!$kv.ContainsKey($k)) {
                    $kv[$k] = 0
                }
                $kv[$k] += $_.CookedValue
            }
        }
        else {
            # GPU内存占用
            (
                (Get-Counter "\$($counterSet)(pid_$($p.id)*)\*").CounterSamples | Where-Object CookedValue
            ) | ForEach-Object {
                $k = $_.Path -replace $memorytype, '$1 $2'
                if (!$kv.ContainsKey($k)) {
                    $kv[$k] = 0
                }
                $kv[$k] += $_.CookedValue
            }
        }
        
        $kv.GetEnumerator() | ForEach-Object {
            $readability = ""
            if ($_.Key -match "engtype") {
                # percentage
                if ($_.Key -match "percentage") {
                    $readability = "$([math]::Round($_.Value, 2))%"
                }
                # running time
                else {
                    # 如何获取时间基础
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

    Write-Output ""

    # 等待一秒
    Start-Sleep -Seconds $interval
}

