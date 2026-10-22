$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $folder 'Launch_Machine_Fault_Diagnosis_App.bat'
$desktop = [Environment]::GetFolderPath('Desktop')
$link = Join-Path $desktop 'Machine Fault Diagnosis.lnk'
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($link)
$s.TargetPath = $target
$s.WorkingDirectory = $folder
$s.Description = 'Machine Fault Diagnosis'
$s.IconLocation = Join-Path $folder 'MachineFaultDiagnosis.ico'
$s.Save()
Write-Host "Desktop shortcut created: $link"
Read-Host 'Press Enter to close'
