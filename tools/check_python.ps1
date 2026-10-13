param(
    [Parameter(Mandatory = $true)][string]$Path
)

if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    Write-Host "ERROR: $Path was not found."
    exit 1
}
$signature = Get-AuthenticodeSignature -LiteralPath $Path
if ($signature.Status -eq 'Valid' -and $signature.SignerCertificate.Subject -match 'Python Software Foundation') {
    Write-Host "      $(Split-Path -Leaf $Path) is signed by the Python Software Foundation."
    exit 0
}
Write-Host "ERROR: $Path is not the signed python.org build (signature: $($signature.Status))."
Write-Host 'Windows 11 Smart App Control may block it. See docs/INSTALL.md section 1.2.'
exit 1
