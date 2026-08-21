# 本地环境修复脚本
# 在运行任何Django命令之前先运行此脚本

# 修复PATH环境变量 - 将带空格的路径转换为短路径
function Global:Fix-LocalPath {
    $originalPath = $env:PATH
    $paths = $originalPath -split ';'
    $fixedPaths = @()
    
    foreach ($p in $paths) {
        # 检查是否包含 "Sean Lu" 的路径
        if ($p -match 'Sean Lu') {
            if (Test-Path $p) {
                # 使用cmd的for命令获取短路径
                $shortPath = (Get-Item $p).FullName
                # 替换 "Sean Lu" 为 "SEANLU~1"
                $shortPath = $shortPath -replace 'Sean Lu', 'SEANLU~1'
                $fixedPaths += $shortPath
            }
        } else {
            $fixedPaths += $p
        }
    }
    
    # 更新环境变量
    $env:PATH = $fixedPaths -join ';'
}

# 立即执行修复
Fix-LocalPath

Write-Host "PATH已修复，现在可以运行Django命令了" -ForegroundColor Green