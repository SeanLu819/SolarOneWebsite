import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询所有产品
cursor.execute("SELECT id, name, slug FROM pages_product ORDER BY id")
products = cursor.fetchall()

output = []
output.append("=== Current Products ===")
for p in products:
    output.append(f"id={p[0]} | name={p[1]} | slug={p[2]}")

# 检查rt400-series和rt400hb
cursor.execute("SELECT id, name, slug FROM pages_product WHERE slug='rt400-series'")
old_hb = cursor.fetchone()

cursor.execute("SELECT id, name, slug FROM pages_product WHERE slug='rt400hb'")
new_hb = cursor.fetchone()

output.append(f"\nrt400-series exists: {bool(old_hb)}")
output.append(f"rt400hb exists: {bool(new_hb)}")

# 如果rt400-series存在，更新它为rt400hb
if old_hb:
    if new_hb:
        output.append("\nBoth exist. Deleting rt400-series...")
        cursor.execute("DELETE FROM pages_product WHERE slug='rt400-series'")
        conn.commit()
        output.append(f"Deleted rt400-series (id={old_hb[0]})")
    else:
        output.append("\nUpdating rt400-series to rt400hb...")
        cursor.execute("UPDATE pages_product SET slug='rt400hb' WHERE slug='rt400-series'")
        conn.commit()
        output.append("Updated slug to rt400hb")
else:
    output.append("\nrt400-series not found in database (good!)")

# 再次查询确认
cursor.execute("SELECT id, name, slug FROM pages_product ORDER BY id")
products = cursor.fetchall()
output.append("\n=== After Update ===")
for p in products:
    output.append(f"id={p[0]} | name={p[1]} | slug={p[2]}")

conn.close()

# 写入文件
result_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_result.txt')
with open(result_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('\n'.join(output))