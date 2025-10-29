# ==========================================================
# Unlock_Static_Folder.ps1
# Ξεκλειδώνει τον φάκελο EURO_GOALS/static για πλήρη πρόσβαση
# ==========================================================

$path = "$PSScriptRoot\static"
Write-Host "`n[EURO_GOALS] 🔓 Ξεκλείδωμα φακέλου: $path"

try {
    if (Test-Path $path) {
        attrib -r -h -s "$path" /S /D | Out-Null

        $acl = Get-Acl $path
        $user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($user, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
        $acl.SetAccessRule($rule)
        Set-Acl $path $acl

        Write-Host "[EURO_GOALS] ✅ Επιτυχία! Ο φάκελος είναι πλήρως προσβάσιμος.`n"
    } else {
        Write-Host "[EURO_GOALS] ❌ Ο φάκελος δεν βρέθηκε: $path"
    }
}
catch {
    Write-Host "[EURO_GOALS] ⚠️ Σφάλμα: $($_.Exception.Message)"
}

# Περιμένει για επιβεβαίωση πριν κλείσει
Write-Host "`nΠάτησε Enter για έξοδο..."
Read-Host | Out-Null
