param([switch]$Install)
$ErrorActionPreference='Stop'
$combatRuntime = Join-Path $PSScriptRoot '../../../server-data/resources/cidade_core'
$combatResults = @()
foreach ($combatPosture in @('ajoelhado','deitado','sentado')) {
    $combatFolder = Join-Path $PSScriptRoot ($combatPosture+'_v6')
    $combatAsset = Join-Path $combatFolder ('cidade_'+$combatPosture+'_v6_ak.ycd')
    $combatCheck = Get-Content -LiteralPath (Join-Path $combatFolder 'binary_validation.json') -Raw | ConvertFrom-Json
    if (-not $combatCheck.binary_decode -or -not $combatCheck.native_rest_preserved -or $combatCheck.endpoint_pose_error -ge 0.002 -or $combatCheck.max_barrel_vertical_component -ge 0.002) { throw "Pose verification failed: $combatPosture" }
    if ((Get-FileHash -LiteralPath $combatAsset -Algorithm SHA256).Hash.ToLowerInvariant() -ne $combatCheck.binary_sha256) { throw "Asset changed since verification: $combatPosture" }
    if ($combatCheck.hand_crossings.PSObject.Properties.Value | Where-Object { $_ -ne 0 }) { throw "Hand penetrates rifle: $combatPosture" }
    $combatResults += @{posture=$combatPosture;file=$combatAsset;sha256=$combatCheck.binary_sha256;native_bones=98;binary_verified=$true}
}
$combatTests=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'runtime_v6_checks.json') -Raw | ConvertFrom-Json
if ($combatTests.repeated_reload_cycles -lt 72 -or -not $combatTests.recoil_recovery -or -not $combatTests.cleanup_and_prone_exit) { throw 'Controller tests incomplete' }
if ($Install) {
    foreach ($combatResult in $combatResults) { Copy-Item -LiteralPath $combatResult.file -Destination (Join-Path $combatRuntime 'stream') }
}
@{revision='v6-apoio-transicoes';installed_on_disk=[bool]$Install;game_tested=$false;server_restarted=$false;rifle='WEAPON_ASSAULTRIFLE';assets=$combatResults;mock_tests=$combatTests} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'v6_installation.json') -Encoding utf8
Write-Output 'V6 files verified. No running game or server was restarted.'
