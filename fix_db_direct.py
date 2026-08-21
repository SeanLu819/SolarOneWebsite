import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询所有产品
print("=== Current Products ===")
cursor.execute("SELECT id, name, slug FROM pages_product ORDER BY id")
products = cursor.fetchall()
for p in products:
    print(f"id={p[0]} | name={p[1]} | slug={p[2]}")

# 检查rt400-series和rt400hb
print("\n=== Checking specific products ===")
cursor.execute("SELECT id, name, slug FROM pages_product WHERE slug='rt400-series'")
old_hb = cursor.fetchone()
print(f"rt400-series: {old_hb}")

cursor.execute("SELECT id, name, slug FROM pages_product WHERE slug='rt400hb'")
new_hb = cursor.fetchone()
print(f"rt400hb: {new_hb}")

# 如果rt400-series存在，更新它为rt400hb
if old_hb:
    if new_hb:
        # 如果两个都存在，删除旧的rt400-series，保留rt400hb
        print("\nBoth exist. Deleting rt400-series...")
        cursor.execute("DELETE FROM pages_product WHERE slug='rt400-series'")
        conn.commit()
        print(f"Deleted rt400-series (id={old_hb[0]})")
    else:
        # 只更新slug
        print("\nUpdating rt400-series to rt400hb...")
        cursor.execute("UPDATE pages_product SET slug='rt400hb' WHERE slug='rt400-series'")
        conn.commit()
        print("Updated slug to rt400hb")
else:
    print("\nrt400-series not found in database")

# 再次查询确认
print("\n=== After Update ===")
cursor.execute("SELECT id, name, slug FROM pages_product ORDER BY id")
products = cursor.fetchall()
for p in products:
    print(f"id={p[0]} | name={p[1]} | slug={p[2]}")

conn.close()