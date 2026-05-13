param(
    [string]$Target = "lordofall@gobaan.com",
    [string]$RemoteDir = "~/AudioLanguage",
    [int]$Port = 8000,
    [string]$ServiceName = "audiolanguage"
)

$ErrorActionPreference = "Stop"

$ProjectDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$ArchivePath = Join-Path ([System.IO.Path]::GetTempPath()) "audiolanguage-deploy.tar.gz"
$RemoteTmp = "/tmp/audiolanguage-deploy.tar.gz"

Write-Host "Packaging $ProjectDir"
if (Test-Path $ArchivePath) {
    Remove-Item -LiteralPath $ArchivePath -Force
}

Push-Location $ProjectDir
try {
    tar `
        --exclude=".git" `
        --exclude=".venv" `
        --exclude="venv" `
        --exclude="env" `
        --exclude="node_modules" `
        --exclude="__pycache__" `
        --exclude="*.pyc" `
        --exclude="server.log" `
        --exclude="server.err.log" `
        --exclude="config/secrets.local.json" `
        -czf $ArchivePath .
}
finally {
    Pop-Location
}

Write-Host "Uploading archive to $Target"
scp $ArchivePath "${Target}:$RemoteTmp"

$RemoteScript = @"
set -euo pipefail

REMOTE_DIR="$RemoteDir"
REMOTE_DIR="`$(eval echo "`$REMOTE_DIR")"
PORT="$Port"
SERVICE_NAME="$ServiceName"

mkdir -p "`$REMOTE_DIR"
tar -xzf "$RemoteTmp" -C "`$REMOTE_DIR"
cd "`$REMOTE_DIR"

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

cat > run_server.sh <<'RUNNER'
#!/usr/bin/env bash
set -euo pipefail
cd "`$(dirname "`$0")"
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi
exec .venv/bin/python scripts/launch_server.py --host 0.0.0.0 --port __PORT__ --no-port-fallback
RUNNER
sed -i "s/__PORT__/$Port/g" run_server.sh
chmod +x run_server.sh

mkdir -p "`$HOME/.config/systemd/user"
cat > "`$HOME/.config/systemd/user/`$SERVICE_NAME.service" <<SERVICE
[Unit]
Description=Audio Language
After=network.target

[Service]
Type=simple
WorkingDirectory=`$REMOTE_DIR
ExecStart=`$REMOTE_DIR/run_server.sh
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
SERVICE

if command -v systemctl >/dev/null 2>&1 && systemctl --user daemon-reload; then
  systemctl --user enable "`$SERVICE_NAME.service"
  systemctl --user restart "`$SERVICE_NAME.service"
  systemctl --user --no-pager --full status "`$SERVICE_NAME.service" || true
else
  pkill -f "scripts/launch_server.py --host 0.0.0.0 --port `$PORT" || true
  nohup ./run_server.sh > server.log 2> server.err.log &
  echo "Started with nohup on port `$PORT"
fi

rm -f "$RemoteTmp"
echo "Deployed to http://`$(hostname -f 2>/dev/null || hostname):`$PORT"
"@

Write-Host "Installing and restarting app on $Target"
$RemoteScript | ssh $Target "bash -s"

Write-Host "Done."
