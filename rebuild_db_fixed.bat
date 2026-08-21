@echo off
REM 完整的数据库重建脚本，包含PATH修复

echo === 修复PATH环境变量 ===
powershell -Command "$paths = $env:PATH -split ';'; $fixed = @(); foreach($p in $paths) { if($p -match 'Sean Lu') { $fixed += ($p -replace 'Sean Lu', 'SEANLU~1') } else { $fixed += $p } }; $env:PATH = $fixed -join ';'"

echo === PATH修复完成 ===

echo === 删除旧数据库 ===
if exist db.sqlite3 (
    del db.sqlite3
    echo 数据库已删除
) else (
    echo 数据库文件不存在
)

echo === 运行数据库迁移 ===
python manage.py migrate

echo === 加载种子数据 ===
python manage.py loaddata seed_data.json

echo === 验证产品数据 ===
python manage.py shell -c "from pages.models import Product; [print(f'id={p.pk} name={p.name} slug={p.slug}') for p in Product.objects.all().order_by('pk')]"

echo === 完成 ===
pause