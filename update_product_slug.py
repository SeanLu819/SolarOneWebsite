"""
直接更新数据库中的产品slug
不依赖命令行输出，直接操作SQLite数据库
"""
import sqlite3
import os

# 数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 步骤1：检查当前状态
cursor.execute("SELECT id, name, slug FROM pages_product WHERE slug IN ('rt400-series', 'rt400hb') ORDER BY id")
results = cursor.fetchall()

# 步骤2：更新slug
# 将 rt400-series 改为 rt400hb
cursor.execute("UPDATE pages_product SET slug='rt400hb' WHERE slug='rt400-series'")
rows_affected = cursor.rowcount

# 步骤3：提交更改
conn.commit()

# 步骤4：验证更新
cursor.execute("SELECT id, name, slug FROM pages_product WHERE slug='rt400hb' ORDER BY id")
final_results = cursor.fetchall()

# 关闭连接
conn.close()

# 输出结果到文件（避免终端输出问题）
output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_result.txt')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=== 数据库更新结果 ===\n\n")
    f.write(f"更新前:\n")
    for r in results:
        f.write(f"  id={r[0]} name={r[1]} slug={r[2]}\n")
    
    f.write(f"\n更新的行数: {rows_affected}\n")
    
    f.write(f"\n更新后 (rt400hb):\n")
    for r in final_results:
        f.write(f"  id={r[0]} name={r[1]} slug={r[2]}\n")
    
    f.write(f"\n=== 更新完成 ===\n")
    f.write(f"请重启开发服务器以使更改生效\n")