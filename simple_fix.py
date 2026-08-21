import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'simple_fix_output.txt')

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

output = []

# 检查是否存在 rt400-series
cursor.execute("SELECT id, name, slug FROM pages_product WHERE slug='rt400-series'")
old_hb = cursor.fetchone()

# 检查是否存在 rt400hb
cursor.execute("SELECT id, name, slug FROM pages_product WHERE slug='rt400hb'")
new_hb = cursor.fetchone()

output.append(f"rt400-series: {old_hb}")
output.append(f"rt400hb: {new_hb}")

# 如果 rt400-series 存在
if old_hb:
    if new_hb:
        # 两个都存在，删除 rt400-series
        output.append("Both exist. Deleting rt400-series...")
        cursor.execute("DELETE FROM pages_product WHERE slug='rt400-series'")
        conn.commit()
        output.append(f"Deleted rt400-series (id={old_hb[0]})")
    else:
        # 只有 rt400-series 存在，更新 slug
        output.append("Only rt400-series exists. Updating slug to rt400hb...")
        cursor.execute("UPDATE pages_product SET slug='rt400hb' WHERE slug='rt400-series'")
        conn.commit()
        output.append("Updated slug to rt400hb")
else:
    output.append("rt400-series not found (good!)")

# 确认结果
cursor.execute("SELECT id, name, slug FROM pages_product ORDER BY id")
products = cursor.fetchall()
output.append("\n=== All Products ===")
for p in products:
    output.append(f"id={p[0]} | name={p[1]} | slug={p[2]}")

conn.close()
output.append("\nDone!")

# 写入文件
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))