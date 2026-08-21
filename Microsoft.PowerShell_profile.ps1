# PowerShell Profile - 修复PATH环境变量问题
# 将此文件保存到: $PROFILE (通常是 C:\Users\Sean Lu\Documents\PowerShell\Microsoft.PowerShell_profile.ps1)

# 函数：修复PATH中的空格路径
function Fix-Path {
    $envPath = $env:PATH -split ';'
    $fixedPath = @()
    
    foreach ($p in $envPath) {
        # 如果路径包含空格且不是已引用的路径
        if ($p -match '\s' -and $p -notmatch '^".*"$') {
            # 检查路径是否存在
            if (Test-Path $p) {
                # 转换为短路径
                $fso = New-Object -ComObject Scripting.FileSystemObject
                try {
                    $folder = $fso.GetFolder($p)
                    $fixedPath += $folder.ShortPath
                } catch {
                    $fixedPath += $p
                }
            }
        } else {
            $fixedPath += $p
        }
    }
    
    $env:PATH = $fixedPath -join ';'
    Write-Host "PATH已修复，空格路径已转换为短路径格式" -ForegroundColor Green
}

# 自动修复PATH
Fix-Path