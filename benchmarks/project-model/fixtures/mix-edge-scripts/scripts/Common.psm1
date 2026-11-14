function Write-Log {
    param([string] $Message)
    Write-Host ("{0:u} {1}" -f (Get-Date).ToUniversalTime(), $Message)
}

function New-BackupArchive {
    param([string] $Source)
    $target = Join-Path ([System.IO.Path]::GetTempPath()) ("backup-{0:yyyyMMdd}.zip" -f (Get-Date))
    Compress-Archive -Path $Source -DestinationPath $target -Force
    return $target
}

Export-ModuleMember -Function Write-Log, New-BackupArchive
