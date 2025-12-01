import sqlite3
from datetime import datetime

# 连接你的现有数据库（替换为你的数据库文件路径！）
conn = sqlite3.connect('server_monitor.db')
cursor = conn.cursor()

# 1. 创建历史数据表
cursor.execute('''
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    username TEXT NOT NULL,
    cpu TEXT NOT NULL,
    mem TEXT NOT NULL,
    disk TEXT DEFAULT '0.0%',
    record_time DATETIME NOT NULL
)
''')

# 2. 创建系统设置表
cursor.execute('''
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    refresh_interval INTEGER DEFAULT 5,
    cpu_threshold INTEGER DEFAULT 80,
    mem_threshold INTEGER DEFAULT 80,
    theme TEXT DEFAULT 'dark',
    data_retention INTEGER DEFAULT 7,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# 初始化设置表默认数据
cursor.execute('SELECT * FROM settings LIMIT 1')
if not cursor.fetchone():
    cursor.execute('INSERT INTO settings DEFAULT VALUES')

conn.commit()
conn.close()
print("✅ 数据库表创建成功！已新增 history（历史数据）和 settings（系统设置）表")