[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$auditScript = (Resolve-Path -LiteralPath $PSCommandPath).Path
$violations = [System.Collections.Generic.List[string]]::new()

function Get-RelativePath {
    param([Parameter(Mandatory)][string]$Path)

    return $Path.Substring($repositoryRoot.Length + 1).Replace("\", "/")
}

function Add-Violation {
    param(
        [Parameter(Mandatory)][string]$Rule,
        [Parameter(Mandatory)][string]$Path
    )

    $violations.Add("[$Rule] $Path")
}

$files = @(
    Get-ChildItem -LiteralPath $repositoryRoot -File -Recurse -Force |
        Where-Object { $_.FullName -notmatch "[\\/]\.git[\\/]" } |
        Sort-Object FullName
)

$blockedExtensions = @(
    ".apk", ".aab", ".apks", ".xapk",
    ".jks", ".keystore", ".p12", ".pfx", ".pem", ".key",
    ".crt", ".cer", ".der",
    ".nes", ".sfc", ".smc", ".gb", ".gbc", ".gba", ".bin",
    ".gen", ".sms", ".rom", ".cue", ".chd", ".iso",
    ".so", ".dll", ".dylib",
    ".zip", ".7z", ".rar", ".tar", ".tgz", ".gz",
    ".log", ".dmp", ".jsonl"
)

$blockedPathPattern =
    "(?i)(^|/)(roms?|bios|cores?|logs?|cache|caches|runtime|state|" +
    "captures?|reports/private|\.gradle|\.idea|\.vscode|\.secrets|__pycache__)(/|$)"

foreach ($file in $files) {
    $relative = Get-RelativePath -Path $file.FullName
    $extension = $file.Extension.ToLowerInvariant()

    if ($blockedExtensions -contains $extension) {
        Add-Violation -Rule "blocked-extension" -Path $relative
    }
    if ($file.Name -eq ".env" -or $file.Name.StartsWith(".env.")) {
        Add-Violation -Rule "blocked-environment-file" -Path $relative
    }
    if ($relative -match $blockedPathPattern) {
        Add-Violation -Rule "blocked-path" -Path $relative
    }
}

$textExtensions = @(
    ".java", ".xml", ".gradle", ".properties", ".pro", ".py",
    ".ps1", ".md", ".json", ".yml", ".yaml", ".txt"
)

$contentRules = [ordered]@{
    "private-ipv4" =
        "(?<!\d)(?:10\.(?:\d{1,3}\.){2}\d{1,3}|" +
        "192\.168\.(?:\d{1,3}\.)\d{1,3}|" +
        "172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3})(?!\d)"
    "mac-address" = "(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
    "local-user-path" = "(?i)(?:[a-z]:\\Users\\[^\\\s]+|/home/[^/\s]+|/Users/[^/\s]+)"
    "private-key" = "-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    "github-token" = "(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9_]{20,}"
    "aws-access-key" = "(?<![A-Z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])"
    "hardcoded-parent-pin" = '(?i)(?:SILENTIUM_PARENT_PIN|PARENT_PIN)\s*[:=]\s*[''"]\d{4}[''"]'
    "device-serial-assignment" = "(?i)(?:ANDROID_SERIAL|ro\.serialno|device[_ -]?serial)\s*[:=]\s*\S+"
}

foreach ($file in $files) {
    if ($file.FullName -eq $auditScript) {
        continue
    }

    if (($textExtensions -notcontains $file.Extension.ToLowerInvariant()) -and
            ($file.Name -ne ".gitignore")) {
        continue
    }

    $relative = Get-RelativePath -Path $file.FullName
    $content = [System.IO.File]::ReadAllText($file.FullName)
    foreach ($rule in $contentRules.GetEnumerator()) {
        if ([regex]::IsMatch($content, $rule.Value)) {
            Add-Violation -Rule $rule.Key -Path $relative
        }
    }
}

$manifestPath = Join-Path $repositoryRoot "PUBLIC_IMPORT_MANIFEST.json"
if (-not (Test-Path -LiteralPath $manifestPath)) {
    Add-Violation -Rule "manifest-missing" -Path "PUBLIC_IMPORT_MANIFEST.json"
} else {
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    $actualByPath = @{}
    foreach ($file in $files) {
        if ($file.FullName -eq $manifestPath) {
            continue
        }
        $actualByPath[(Get-RelativePath -Path $file.FullName)] = $file.Length
    }

    $listedByPath = @{}
    foreach ($entry in $manifest.files) {
        if ($listedByPath.ContainsKey($entry.path)) {
            Add-Violation -Rule "manifest-duplicate" -Path $entry.path
            continue
        }
        $listedByPath[$entry.path] = [long]$entry.bytes
    }

    foreach ($path in $actualByPath.Keys) {
        if (-not $listedByPath.ContainsKey($path)) {
            Add-Violation -Rule "manifest-unlisted" -Path $path
        } elseif ($listedByPath[$path] -ne $actualByPath[$path]) {
            Add-Violation -Rule "manifest-size" -Path $path
        }
    }
    foreach ($path in $listedByPath.Keys) {
        if (-not $actualByPath.ContainsKey($path)) {
            Add-Violation -Rule "manifest-stale" -Path $path
        }
    }
}

if ($violations.Count -gt 0) {
    Write-Host "Public-release audit failed:" -ForegroundColor Red
    $violations | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" }
    exit 1
}

Write-Host "Public-release audit passed." -ForegroundColor Green
Write-Host "Files checked: $($files.Count)"
Write-Host "No blocked artifacts or sensitive public-text patterns were found."
