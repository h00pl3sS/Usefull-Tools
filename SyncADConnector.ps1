$ServidorRemoto = ""

Write-Host "--- Sincronización AD para $ServidorRemoto ---" -ForegroundColor Cyan

# Pedir credenciales en el mismo shell
$user = Read-Host "Introduce el usuario (ej: DOMINIO\admin)"
$password = Read-Host "Introduce la contraseña" -AsSecureString
$cred = New-Object System.Management.Automation.PSCredential($user, $password)

Write-Host "`nConectando a $ServidorRemoto..." -ForegroundColor Yellow

try {
    # Guardamos el resultado del comando en una variable
    $resultado = Invoke-Command -ComputerName $ServidorRemoto -ScriptBlock {
        Import-Module ADSync
        # Ejecutamos y devolvemos el objeto de resultado
        return Start-ADSyncSyncCycle -PolicyType Delta
    } -Credential $cred -ErrorAction Stop

    # Mostramos el resultado devuelto por el servidor
    if ($resultado) {
        Write-Host "`nRespuesta del servidor:" -ForegroundColor Green
        $resultado | Format-List | Out-String | Write-Host -ForegroundColor White
    } else {
        Write-Host "`nEl comando se ejecutó pero no devolvió datos (esto es normal si ya hay un ciclo en curso)." -ForegroundColor Gray
    }
}
catch {
    # Si falla la conexión o el comando, mostramos el error detallado
    Write-Host "`n[ERROR]" -ForegroundColor Red
    Write-Host "Mensaje: $($_.Exception.Message)" -ForegroundColor White
    Write-Host "Detalle: $($_.ScriptStackTrace)" -ForegroundColor Gray
}

Write-Host "`nPresione cualquier tecla para salir..."
$null = [Console]::ReadKey($true)