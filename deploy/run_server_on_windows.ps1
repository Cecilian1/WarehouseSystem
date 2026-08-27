$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonCandidates = @()
if ($env:WAREHOUSE_PYTHON) {
    $pythonCandidates += $env:WAREHOUSE_PYTHON
}
if ($env:CONDA_PREFIX) {
    $pythonCandidates += (Join-Path $env:CONDA_PREFIX "python.exe")
}
$pythonCandidates += @(where.exe python 2>$null)
$pythonCandidates += @(
    Get-Command python -All -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Source
)

$pythonExe = $null
foreach ($candidate in ($pythonCandidates | Select-Object -Unique)) {
    if (-not $candidate -or -not (Test-Path -LiteralPath $candidate)) { continue }
    if ($candidate -like "*\Microsoft\WindowsApps\python.exe") { continue }
    & $candidate -c "import fastapi, uvicorn" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pythonExe = $candidate
        break
    }
}
if (-not $pythonExe) {
    throw "未找到可用的 Python（需要已安装 fastapi 和 uvicorn）。可通过 WAREHOUSE_PYTHON 指定 python.exe。"
}

# 让 Python 以 UTF-8 输出，否则日志里的中文在 GBK 控制台会显示为乱码
$env:PYTHONIOENCODING = "utf-8"

# 从仓库根目录的 .env 加载配置（复制 .env.example 为 .env 后按需修改）
$envFile = Join-Path $projectRoot ".env"
if (Test-Path $envFile) {
    # 必须显式指定 UTF8：Windows PowerShell 5.1 默认按 ANSI(GBK) 解码，.env 里的
    # 中文注释会被错误解码并吞掉紧随其后的一行配置。
    Get-Content $envFile -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        $pair = $line -split "=", 2
        if ($pair.Count -eq 2) {
            $key = $pair[0].Trim()
            $value = $pair[1].Trim()
            if ($value -ne "") {
                Set-Item -Path "Env:$key" -Value $value
            }
        }
    }
} else {
    Write-Warning ".env 不存在，使用内置默认值（可复制 .env.example 为 .env 后自定义）"
}

if (-not $env:WAREHOUSE_DB_PATH) { $env:WAREHOUSE_DB_PATH = "data\warehousekeeper-server.db" }
if (-not $env:WAREHOUSE_COLLECTOR_STATE_PATH) { $env:WAREHOUSE_COLLECTOR_STATE_PATH = "data\collector-state.json" }
if (-not $env:WAREHOUSE_SYNC_INTERVAL_SEC) { $env:WAREHOUSE_SYNC_INTERVAL_SEC = "5" }
if (-not $env:WAREHOUSE_ALLOW_DEMO_LOGIN) { $env:WAREHOUSE_ALLOW_DEMO_LOGIN = "true" }

# 相对路径统一相对项目根目录解析
if (-not [System.IO.Path]::IsPathRooted($env:WAREHOUSE_DB_PATH)) {
    $env:WAREHOUSE_DB_PATH = Join-Path $projectRoot $env:WAREHOUSE_DB_PATH
}
if (-not [System.IO.Path]::IsPathRooted($env:WAREHOUSE_COLLECTOR_STATE_PATH)) {
    $env:WAREHOUSE_COLLECTOR_STATE_PATH = Join-Path $projectRoot $env:WAREHOUSE_COLLECTOR_STATE_PATH
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $env:WAREHOUSE_DB_PATH) | Out-Null

Set-Location $projectRoot
& $pythonExe -m backend.common.init_db --db-path $env:WAREHOUSE_DB_PATH
& $pythonExe -m uvicorn backend.api_service.main:app --host 0.0.0.0 --port 8000
