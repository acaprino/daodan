#Requires -Version 7.2
#Requires -Modules @{ ModuleName = "Az.Storage"; ModuleVersion = "6.1.0" }

param(
    [Parameter(Mandatory)] [string] $Account,
    [string] $Container = "backups"
)

Import-Module "$PSScriptRoot/Common.psm1"

$context = New-AzStorageContext -StorageAccountName $Account -UseConnectedAccount
$archive = New-BackupArchive -Source "./data"
Set-AzStorageBlobContent -File $archive -Container $Container -Context $context | Out-Null
Write-Log "uploaded $archive"
