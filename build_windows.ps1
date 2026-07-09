# [DEPRECATED] Este script foi descontinuado em favor do build.ps1 unificado.
# Por favor, utilize o script de compilação oficial: .\build.ps1
#
# Este wrapper delega automaticamente a execução para o build.ps1 para manter compatibilidade.

Write-Warning "=========================================================================="
Write-Warning " [DESCONTINUADO] build_windows.ps1 foi descontinuado em favor de build.ps1."
Write-Warning " Redirecionando a execução para o script de build unificado..."
Write-Warning "=========================================================================="
Write-Host ""

& .\build.ps1
exit $LastExitCode
