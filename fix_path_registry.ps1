# 彻底修复PATH环境变量
# 通过直接修改注册表来修复带空格的路径

Write-Host "=== 彻底修复PATH环境变量 ===" -ForegroundColor Green

# 获取用户PATH（从注册表）
$userPathKey = "HKCU:\Environment"
$userPath = (Get-ItemProperty -Path $userPathKey -Name PATH -ErrorAction SilentlyContinue).PATH

if ($userPath) {
    Write-Host "`n当前用户PATH (从注册表读取):" -ForegroundColor Yellow
    
    # 分割PATH并检查每个路径
    $paths = $userPath -split ';'
    $fixedPaths = @()
    
    foreach ($p in $paths) {
        if ($p -match 'Sean Lu') {
            Write-Host "发现带空格的路径: $p" -ForegroundColor Red
            
            # 尝试转换为短路径
            if (Test-Path $p) {
                $fso = New-Object -ComObject Scripting.FileSystemObject
                try {
                    $folder = $fso.GetFolder($p)
                    $shortPath = $folder.ShortPath
                    Write-Host "转换为短路径: $shortPath" -ForegroundColor Green
                    $fixedPaths += $shortPath
                } catch {
                    Write-Host "转换失败，保留原路径" -ForegroundColor Yellow
                    $fixedPaths += $p
                }
            } else {
                Write-Host "路径不存在，移除" -ForegroundColor Yellow
            }
        } else {
            $fixedPaths += $p
        }
    }
    
    # 重新组合PATH
    $newPath = $fixedPaths -join ';'
    
    # 保存到注册表
    Set-ItemProperty -Path $userPathKey -Name PATH -Value $newPath
    
    Write-Host "`n修复后的用户PATH:" -ForegroundColor Yellow
    Write-Host $newPath
    
    Write-Host "`n=== 修复完成 ===" -ForegroundColor Green
    Write-Host "请执行以下步骤使更改生效:" -ForegroundColor Cyan
    Write-Host "1. 关闭所有终端窗口" -ForegroundColor Cyan
    Write-Host "2. 重新打开终端" -ForegroundColor Cyan
    Write-Host "3. 运行: refreshenv 或重新启动终端" -ForegroundColor Cyan
} else {
    Write-Host "未找到用户PATH环境变量" -ForegroundColor Red
}