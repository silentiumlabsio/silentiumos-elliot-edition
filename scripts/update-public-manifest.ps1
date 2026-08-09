[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$manifestPath = Join-Path $repositoryRoot "PUBLIC_IMPORT_MANIFEST.json"

$entries = @(
    Get-ChildItem -LiteralPath $repositoryRoot -File -Recurse -Force |
        Where-Object {
            $_.FullName -ne $manifestPath -and
            $_.FullName -notmatch "[\\/]\.git[\\/]"
        } |
        Sort-Object FullName |
        ForEach-Object {
            [ordered]@{
                path = $_.FullName.Substring($repositoryRoot.Length + 1).Replace("\", "/")
                bytes = $_.Length
            }
        }
)

$manifest = [ordered]@{
    project = [string]::Concat("SilentiumOS ", [char]0x2014, " Elliot Edition")
    version = "0.7.7-public-source"
    files = $entries
}

$json = $manifest | ConvertTo-Json -Depth 5
$utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($manifestPath, $json + "`n", $utf8WithoutBom)

Write-Host "Updated PUBLIC_IMPORT_MANIFEST.json with $($entries.Count) files."
