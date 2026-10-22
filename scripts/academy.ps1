# Own wrapper. Requires Docker Compose 2.24.4+ for !override / !reset.
$composeArguments = $args
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtimeEnv = Join-Path $projectRoot 'docker/academy/.runtime/.env'
if (-not (Test-Path -LiteralPath $runtimeEnv)) {
    throw 'Run python scripts/prepare_academy.py first.'
}
& docker compose --project-directory $projectRoot --env-file $runtimeEnv `
    --project-name videoflix-academy `
    -f (Join-Path $projectRoot 'docker/academy/original/docker-compose.yml') `
    -f (Join-Path $projectRoot 'docker/academy/compose.compat.yaml') @composeArguments
exit $LASTEXITCODE
