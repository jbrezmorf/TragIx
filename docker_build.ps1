# Build a songbook variant inside Docker.
# Usage: .\docker_build.ps1 <variant> [target] [edition]
# Example: .\docker_build.ps1 zboznej all 2026
#          .\docker_build.ps1 nezboznej rebuild 2025
#          .\docker_build.ps1 zboznej rebuild          (legacy: reads from input/)

param(
    [Parameter(Mandatory=$true)][string]$Variant,
    [string]$Target = "all",
    [string]$Edition = ""
)

$ImageName = "tragix-songbook"

docker build -t $ImageName .

$EditionArg = if ($Edition) { "--edition $Edition" } else { "" }

docker run --rm `
    -v "${PWD}/${Variant}/build:/songbook/${Variant}/build" `
    $ImageName `
    --variant $Variant --target $Target $EditionArg

Write-Host "Done. Output in ${Variant}/build/"
