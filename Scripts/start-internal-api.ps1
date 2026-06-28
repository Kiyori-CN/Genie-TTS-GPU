param(
    [string]$HostName = '127.0.0.1',
    [int]$Port = 8000,
    [ValidateSet('cpu', 'cuda', 'directml', 'auto')]
    [string]$Runtime = 'cuda'
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot 'Runtime\.venv\Scripts\python.exe'
$RuntimePython = Join-Path $RepoRoot 'Runtime\Python'
$RuntimeVenvScripts = Join-Path $RepoRoot 'Runtime\.venv\Scripts'
$SitePackages = Join-Path $RepoRoot 'Runtime\.venv\Lib\site-packages'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Internal Python was not found: $Python"
}

$env:PYTHONNOUSERSITE = '1'
$env:PYTHONPATH = $RepoRoot
$env:GENIE_DATA_DIR = Join-Path $RepoRoot 'GenieData'

$InternalPathParts = @(
    $RuntimeVenvScripts,
    $RuntimePython,
    (Join-Path $RuntimePython 'Scripts'),
    "$env:SystemRoot\System32",
    $env:SystemRoot
)

$NvidiaRoot = Join-Path $SitePackages 'nvidia'
if (Test-Path -LiteralPath $NvidiaRoot) {
    Get-ChildItem -LiteralPath $NvidiaRoot -Directory | ForEach-Object {
        $bin = Join-Path $_.FullName 'bin'
        if (Test-Path -LiteralPath $bin) {
            $InternalPathParts = @($bin) + $InternalPathParts
        }
    }
}

$env:PATH = $InternalPathParts -join ';'

@'
import argparse

import genie_tts as genie

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=8000)
parser.add_argument('--runtime', default='cuda')
args = parser.parse_args()

print('runtime=', genie.configure_runtime(args.runtime))
genie.start_server(host=args.host, port=args.port, workers=1)
'@ | & $Python - --host $HostName --port $Port --runtime $Runtime
