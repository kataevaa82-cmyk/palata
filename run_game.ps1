$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$godot = Join-Path $projectRoot 'tools\godot\Godot_v4.7.1-stable_win64.exe'
$project = Join-Path $projectRoot 'project'

if (-not (Test-Path -LiteralPath $godot)) {
    throw "Godot executable not found: $godot"
}

& $godot --path $project

