$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$databasePath = Join-Path $projectRoot "data\warehousekeeper-server.db"
$pythonExe = (Get-Command python -ErrorAction Stop).Source

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $databasePath) | Out-Null

$env:WAREHOUSE_DB_PATH = $databasePath
$env:WAREHOUSE_BOARD_SOURCE_URL = "http://10.141.97.252:8000"
$env:WAREHOUSE_COLLECTOR_STATE_PATH = (Join-Path $projectRoot "data\collector-state.json")
$env:WAREHOUSE_SYNC_INTERVAL_SEC = "5"
$env:WAREHOUSE_ALLOW_DEMO_LOGIN = "true"

Set-Location $projectRoot
python -m backend.common.init_db --db-path $databasePath
python -m uvicorn backend.api_service.main:app --host 0.0.0.0 --port 8000
