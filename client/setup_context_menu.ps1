$exe = $args[0]
$menuLabel = -join ([char]0x5373, [char]0x30B7, [char]0x30A7, [char]0x30A2, [char]0x541B, [char]0x306B, [char]0x9001, [char]0x308B)
$cmdValue = "`"$exe`" --send-file `"%1`""

$classesKey = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Software\Classes\*\shell', $true)
if ($null -eq $classesKey) {
    $classesKey = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('Software\Classes\*\shell')
}
$classesKey.DeleteSubKeyTree('SokuShareKun', $false)
$sk = $classesKey.CreateSubKey('SokuShareKun')
$sk.SetValue('', $menuLabel)
$sk.SetValue('Icon', "`"$exe`",0")
$ck = $sk.CreateSubKey('command')
$ck.SetValue('', $cmdValue)
$ck.Close()
$sk.Close()
$classesKey.Close()
Write-Host "Context menu registered: $menuLabel"
