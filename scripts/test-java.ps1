[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$javaExecutableName = if ($IsWindows -or $env:OS -eq "Windows_NT") {
    "java.exe"
} else {
    "java"
}
$javacExecutableName = if ($IsWindows -or $env:OS -eq "Windows_NT") {
    "javac.exe"
} else {
    "javac"
}

if ($env:JAVA_HOME) {
    $java = Join-Path $env:JAVA_HOME "bin/$javaExecutableName"
    $javac = Join-Path $env:JAVA_HOME "bin/$javacExecutableName"
} else {
    $java = (Get-Command java -ErrorAction Stop).Source
    $javac = (Get-Command javac -ErrorAction Stop).Source
}

if (-not (Test-Path -LiteralPath $java) -or
    -not (Test-Path -LiteralPath $javac)) {
    throw "A complete JDK with java and javac is required."
}

$classes = Join-Path (
    [System.IO.Path]::GetTempPath()
) ("silentium-java-tests-" + [guid]::NewGuid().ToString("N"))

$sources = @(
    "app/src/main/java/com/silentiumlabs/silentiumos/SystemDefinition.java",
    "app/src/main/java/com/silentiumlabs/silentiumos/GameEntry.java",
    "app/src/main/java/com/silentiumlabs/silentiumos/GameCatalog.java",
    "tests/java/com/silentiumlabs/silentiumos/GameCatalogContractTest.java"
) | ForEach-Object { Join-Path $repositoryRoot $_ }

try {
    New-Item -ItemType Directory -Path $classes | Out-Null
    & $javac -encoding UTF-8 -d $classes @sources
    if ($LASTEXITCODE -ne 0) {
        throw "Java test compilation failed."
    }

    & $java -ea -cp $classes com.silentiumlabs.silentiumos.GameCatalogContractTest
    if ($LASTEXITCODE -ne 0) {
        throw "Java contract tests failed."
    }
} finally {
    if (Test-Path -LiteralPath $classes) {
        $resolvedClasses = (Resolve-Path -LiteralPath $classes).Path
        $tempRoot = [System.IO.Path]::GetTempPath().TrimEnd(
            [System.IO.Path]::DirectorySeparatorChar
        )
        if (-not $resolvedClasses.StartsWith(
                $tempRoot + [System.IO.Path]::DirectorySeparatorChar,
                [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean a Java test path outside the temp directory."
        }
        Remove-Item -LiteralPath $resolvedClasses -Recurse -Force
    }
}
