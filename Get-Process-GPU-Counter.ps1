# 命令行参数: 进程名
param(
    [Parameter()]
    [String]$process
)

# 每秒输出一次，实际上间隔可能大于1秒
$p = Get-Process $process

$engtype = ".*_(engtype.*)\)\\.*"
$memorytype = ".*\\(gpu.*)\(.*\)\\(.*)"

while ($true) {
    # 记录开始时间
    $time = [string]::Format('"time": "{0}"', $(Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"))
    Write-Output "{$time}"
    
    $names = Get-Counter -ListSet 'GPU*' | findstr 'CounterSetName'
    ForEach ($line in $names -split "`r`n") {
        $parts = $Line -split ":"
        $counterSet = $parts[1].Trim() -replace '.*\[\d+(;\d+)?m'

        $kv = @{}
        if ($counterSet -eq "GPU Engine") {
            # 输出GPU引擎占用
            (
                (Get-Counter "\$($counterSet)(pid_$($p.id)*engtype*)\Utilization Percentage").CounterSamples  | Where-Object CookedValue
            ) | ForEach-Object {
                $k = "gpu $($_.Path -replace $engtype, '$1') usage"
                $kv[$k] =  $_.CookedValue
            }
        }
        else {
            # 输出GPU内存占用
            (
                (Get-Counter "\$($counterSet)(pid_$($p.id)*)\*").CounterSamples | Where-Object CookedValue
            ) | ForEach-Object {
                $k = $_.Path -replace $memorytype, '$1 $2'
                if(!$kv.ContainsKey($k)) {
                    $kv[$k] = 0
                }
                $kv[$k] += $_.CookedValue
            }
        }
        
        $kv.GetEnumerator() | ForEach-Object {
            $line = ""
            if($_.Key -match "engtype") {
                $line = [string]::Format('"entry": "{0}", "value": {1}, "text": "{2}"', $_.Key, $_.Value, "$([math]::Round($_.Value, 2))%")
            } else {
                $line = [string]::Format('"entry": "{0}", "value": {1}, "text": "{2}"', $_.Key, $_.Value, "$([math]::Round($_.Value/1MB, 2))MB")
            }
            Write-Output "{$line}"
        }
    }

    Write-Output ""

    # 等待一秒
    Start-Sleep -Seconds 1
}

