# 修复PATH环境变量问题
# 将带空格的路径转换为短路径格式

Write-Host "=== 修复PATH环境变量 ===" -ForegroundColor Green

# 获取当前PATH
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
$systemPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")

Write-Host "`n当前用户PATH:" -ForegroundColor Yellow
Write-Host $currentPath

Write-Host "`n系统PATH:" -ForegroundColor Yellow  
Write-Host $systemPath

# 函数：将路径转换为短路径
function Convert-ToShortPath {
    param([string]$path)
    if (Test-Path $path) {
        $fso = New-Object -ComObject Scripting.FileSystemObject
        $folder = $fso.GetFolder($path)
        return $folder.ShortPath
    }
    return $path
}

# 修复用户PATH中的空格路径
Write-Host "`n=== 修复用户PATH ===" -ForegroundColor Green
$userPaths = $currentPath -split ';'
$fixedUserPaths = @()

foreach ($p in $userPaths) {
    if ($p -match 'Sean Lu') {
        Write-Host "发现带空格的路径: $p" -ForegroundColor Red
        $shortPath = Convert-ToShortPath $p
        Write-Host "转换为短路径: $shortPath" -ForegroundColor Green
        $fixedUserPaths += $shortPath
    } else {
        $fixedUserPaths += $p
    }
}

$newUserPath = $fixedUserPaths -join ';'

# 保存修复后的PATH
[Environment]::SetEnvironmentVariable("PATH", $newUserPath, "User")

Write-Host "`n修复后的用户PATH:" -ForegroundColor Yellow
Write-Host $newUserPath

Write-Host "`n=== 修复完成 ===" -ForegroundColor Green
Write-Host "请关闭所有终端窗口并重新打开，新的PATH才会生效" -ForegroundColor Cyan