from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sqlite3
import os
import csv
from io import StringIO
from threading import Timer
import logging
import paramiko
import re
from datetime import datetime, timedelta
import time

# ===================== 基础配置 =====================
app = Flask(__name__)
CORS(app)

# 数据库路径（容器内路径，对应宿主机 ./backend/data/monitor.db）
DB_PATH = '/app/data/monitor.db'
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # 确保目录存在

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===================== 数据库初始化（新增 history 和 settings 表） =====================
def init_db():
    """初始化数据库表（包含原有 hosts 表 + 新增 history/settings 表）"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # 原有 hosts 表（保持不变）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hosts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    port INTEGER DEFAULT 22,
                    cpu TEXT DEFAULT "0.0%",
                    mem TEXT DEFAULT "0.0%",
                    disk TEXT DEFAULT "0.0%",
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 新增：历史数据表（存储监控数据历史）
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
            # 新增：系统设置表（存储刷新频率、告警阈值等）
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
            # 初始化设置表默认数据（如果无数据）
            cursor.execute('SELECT * FROM settings LIMIT 1')
            if not cursor.fetchone():
                cursor.execute('INSERT INTO settings DEFAULT VALUES')
            conn.commit()
        logger.info(f"✅ 数据库初始化成功，表：hosts + history + settings（路径：{DB_PATH}）")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败：{str(e)}")

# 辅助函数：获取数据库连接（统一路径）
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ===================== 监控数据采集工具（保持原有逻辑） =====================
class MonitorCollector:
    """SSH连接采集服务器监控数据"""
    @staticmethod
    def get_cpu_usage(ssh):
        """采集CPU使用率（Linux）"""
        try:
            # 兼容不同Linux版本的top命令输出
            stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep -E '^%Cpu|^CPU' | awk '{print 100 - $8}'")
            cpu_usage = stdout.read().decode().strip()
            if cpu_usage and cpu_usage.replace('.', '').isdigit():
                return f"{float(cpu_usage):.1f}%"
            return "0.0%"
        except Exception as e:
            logger.error(f"❌ 采集CPU使用率失败：{str(e)}")
            return "0.0%"

    @staticmethod
    def get_mem_usage(ssh):
        """采集内存使用率（Linux）"""
        try:
            stdin, stdout, stderr = ssh.exec_command("free | grep Mem | awk '{print $2, $3}'")
            mem_data = stdout.read().decode().strip().split()
            if len(mem_data) == 2:
                mem_total = int(mem_data[0])
                mem_used = int(mem_data[1])
                mem_usage = f"{(mem_used / mem_total) * 100:.1f}%"
                return mem_usage
            return "0.0%"
        except Exception as e:
            logger.error(f"❌ 采集内存使用率失败：{str(e)}")
            return "0.0%"

    @staticmethod
    def get_disk_usage(ssh):
        """采集磁盘使用率（Linux，默认/分区）"""
        try:
            stdin, stdout, stderr = ssh.exec_command("df -h / | grep / | awk '{print $5}'")
            disk_usage = stdout.read().decode().strip()
            return disk_usage if disk_usage else "0.0%"
        except Exception as e:
            logger.error(f"❌ 采集磁盘使用率失败：{str(e)}")
            return "0.0%"

    @staticmethod
    def connect_ssh(ip, username, password, port=22):
        """建立SSH连接"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                hostname=ip,
                port=port,
                username=username,
                password=password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            logger.info(f"✅ SSH连接成功：{ip}:{port}")
            return ssh
        except Exception as e:
            logger.error(f"❌ SSH连接失败 {ip}:{port}：{str(e)}")
            ssh.close()
            return None

# ===================== 新增：定时采集数据任务（存入 history 表） =====================
def collect_server_data():
    """定时采集所有主机数据，存入 history 表 + 清理过期数据"""
    collector = MonitorCollector()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. 获取所有已添加主机
        cursor.execute('SELECT ip, username, password, port FROM hosts')
        hosts = cursor.fetchall()
        if not hosts:
            logger.info("⚠️ 暂无已添加的主机，跳过数据采集")
            conn.close()
            # 读取刷新频率，启动下一次采集
            restart_collect_task()
            return

        # 2. 遍历主机采集数据并存入 history 表
        for host in hosts:
            ip = host['ip']
            username = host['username']
            password = host['password']
            port = host['port']

            # 建立SSH连接采集数据
            ssh = collector.connect_ssh(ip, username, password, port)
            if ssh:
                cpu = collector.get_cpu_usage(ssh)
                mem = collector.get_mem_usage(ssh)
                disk = collector.get_disk_usage(ssh)
                ssh.close()
            else:
                # 连接失败，存入离线数据
                cpu = "0.0%"
                mem = "0.0%"
                disk = "0.0%"

            # 存入 history 表
            cursor.execute('''
                INSERT INTO history (ip, username, cpu, mem, disk, record_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', [ip, username, cpu, mem, disk, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            logger.info(f"📝 已记录主机 {ip} 历史数据：CPU={cpu}, MEM={mem}")

        # 3. 清理过期数据（按系统设置的保留天数）
        cursor.execute('SELECT data_retention FROM settings LIMIT 1')
        retention_days = cursor.fetchone()['data_retention']
        expire_time = (datetime.now() - timedelta(days=retention_days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('DELETE FROM history WHERE record_time < ?', [expire_time])
        logger.info(f"🗑️ 清理 {retention_days} 天前的历史数据（过期时间：{expire_time}）")

        conn.commit()
    except Exception as e:
        logger.error(f"❌ 定时数据采集失败：{str(e)}")
    finally:
        conn.close()
        # 启动下一次采集任务
        restart_collect_task()

def restart_collect_task():
    """读取系统设置的刷新频率，启动下一次采集"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT refresh_interval FROM settings LIMIT 1')
    interval = cursor.fetchone()['refresh_interval']
    conn.close()
    # 定时执行（interval 秒后）
    Timer(interval, collect_server_data).start()
    logger.info(f"⏰ 下一次数据采集将在 {interval} 秒后执行")

# ===================== 原有核心接口（保持不变） =====================
@app.route('/api/hosts', methods=['GET'])
def get_hosts():
    """获取主机列表（自动采集最新数据）"""
    try:
        logger.info("📥 收到 /api/hosts 查询请求")
        collector = MonitorCollector()
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT id, ip, username, password, port FROM hosts ORDER BY created_at DESC')
            hosts = cursor.fetchall()
            
            # 批量采集数据并更新（移除 updated_at 更新）
            for host in hosts:
                ssh = collector.connect_ssh(
                    ip=host['ip'],
                    username=host['username'],
                    password=host['password'],
                    port=host['port']
                )
                if ssh:
                    cpu = collector.get_cpu_usage(ssh)
                    mem = collector.get_mem_usage(ssh)
                    disk = collector.get_disk_usage(ssh)
                    ssh.close()
                    
                    # 更新数据库（只更新监控数据，不涉及 updated_at）
                    cursor.execute('''
                        UPDATE hosts SET cpu=?, mem=?, disk=? WHERE id=?
                    ''', (cpu, mem, disk, host['id']))
                    conn.commit()
        
        # 重新查询更新后的数据
        cursor.execute('''
            SELECT ip, username, port, cpu, mem, disk FROM hosts
            ORDER BY created_at DESC
        ''')
        result = []
        for row in cursor.fetchall():
            result.append({
                'ip': row['ip'],
                'username': row['username'],
                'port': row['port'],
                'cpu': row['cpu'],
                'mem': row['mem'],
                'disk': row['disk']
            })
        
        logger.info(f"📤 查询完成，共 {len(result)} 台主机（已更新监控数据）")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"❌ /api/hosts 报错：{str(e)}")
        return jsonify({'error': '查询失败', 'detail': str(e)}), 500

@app.route('/api/add_host', methods=['POST'])
def add_host():
    """添加主机接口"""
    try:
        data = request.form
        ip = data.get('ip')
        username = data.get('username')
        password = data.get('password')
        port = data.get('port', 22)

        if not (ip and username and password):
            logger.warning("⚠️ 缺少必填参数")
            return jsonify({'status': 'fail', 'message': 'IP、用户名、密码不能为空'}), 400

        # 验证SSH连接（确保能采集数据）
        collector = MonitorCollector()
        ssh = collector.connect_ssh(ip, username, password, port)
        if not ssh:
            return jsonify({'status': 'fail', 'message': 'SSH连接失败，请检查账号密码和端口'}), 400
        ssh.close()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # 检查IP 是否已存在
            cursor.execute('SELECT ip FROM hosts WHERE ip = ?', (ip,))
            if cursor.fetchone():
                return jsonify({'status': 'fail', 'message': '该主机已添加'}), 400
            # 插入数据（无 updated_at 字段）
            cursor.execute('''
                INSERT INTO hosts (ip, username, password, port)
                VALUES (?, ?, ?, ?)
            ''', (ip, username, password, port))
            conn.commit()

        logger.info(f"✅ 主机 {ip} 添加成功")
        return jsonify({'status': 'success', 'message': '添加主机成功'}), 201
    except Exception as e:
        logger.error(f"❌ 添加主机失败：{str(e)}")
        return jsonify({'status': 'fail', 'message': str(e)}), 500

@app.route('/api/delete_host/<ip>', methods=['DELETE'])
def delete_host(ip):
    """删除主机接口"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM hosts WHERE ip = ?', (ip,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"✅ 主机 {ip} 删除成功")
                return jsonify({'status': 'success', 'message': '删除主机成功'}), 200
            else:
                return jsonify({'status': 'fail', 'message': '主机不存在'}), 404
    except Exception as e:
        logger.error(f"❌ 删除主机失败：{str(e)}")
        return jsonify({'status': 'fail', 'message': str(e)}), 500

# ===================== 新增：历史记录接口 =====================
@app.route('/api/history', methods=['GET'])
def get_history():
    """历史记录查询 + CSV导出"""
    try:
        logger.info("📥 收到 /api/history 查询请求")
        # 获取前端查询参数
        host_ip = request.args.get('host_ip', 'all')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        export = request.args.get('export')

        # 校验时间参数
        if not (start_time and end_time):
            logger.warning("⚠️ 缺少时间范围参数")
            return jsonify({'error': '请选择查询时间范围'}), 400

        # 连接数据库查询
        conn = get_db_connection()
        cursor = conn.cursor()

        # 构造查询SQL
        sql = '''
        SELECT h.record_time, h.ip, h.username, h.cpu, h.mem, h.disk,
               CASE WHEN CAST(REPLACE(h.cpu, '%', '') AS FLOAT) > 0 THEN '在线' ELSE '离线' END AS status
        FROM history h
        WHERE h.record_time BETWEEN ? AND ?
        '''
        params = [start_time, end_time]

        # 按IP筛选
        if host_ip != 'all':
            sql += ' AND h.ip = ?'
            params.append(host_ip)

        # 按时间降序排序
        sql += ' ORDER BY h.record_time DESC'

        cursor.execute(sql, params)
        history_data = cursor.fetchall()
        conn.close()

        # 导出CSV
        if export == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            # 写入表头
            writer.writerow(['记录时间', '主机IP', '用户名', 'CPU使用率', '内存使用率', '磁盘使用率', '状态'])
            # 写入数据
            for row in history_data:
                writer.writerow([
                    row['record_time'], row['ip'], row['username'],
                    row['cpu'], row['mem'], row['disk'], row['status']
                ])
            # 构建下载响应
            response = make_response(output.getvalue())
            filename = f'history_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            response.headers['Content-Type'] = 'text/csv'
            logger.info(f"📤 导出历史数据CSV：{len(history_data)} 条记录")
            return response

        # 返回JSON数据
        result = []
        for row in history_data:
            result.append({
                'record_time': row['record_time'],
                'ip': row['ip'],
                'username': row['username'],
                'cpu': row['cpu'],
                'mem': row['mem'],
                'disk': row['disk'],
                'status': row['status']
            })
        logger.info(f"📤 返回历史数据：{len(result)} 条记录")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"❌ /api/history 报错：{str(e)}")
        return jsonify({'error': '查询历史数据失败', 'detail': str(e)}), 500

# ===================== 新增：系统设置接口 =====================
@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """系统设置：读取（GET）+ 保存（POST）"""
    try:
        if request.method == 'GET':
            # 读取设置
            logger.info("📥 收到 /api/settings 读取请求")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings LIMIT 1')
            settings = cursor.fetchone()
            conn.close()
            result = {
                'refresh_interval': settings['refresh_interval'],
                'cpu_threshold': settings['cpu_threshold'],
                'mem_threshold': settings['mem_threshold'],
                'theme': settings['theme'],
                'data_retention': settings['data_retention']
            }
            logger.info(f"📤 返回系统设置：{result}")
            return jsonify(result), 200

        elif request.method == 'POST':
            # 保存设置
            logger.info("📥 收到 /api/settings 保存请求")
            settings_data = request.get_json()
            conn = get_db_connection()
            cursor = conn.cursor()
            # 更新设置表
            cursor.execute('''
                UPDATE settings SET
                    refresh_interval = ?,
                    cpu_threshold = ?,
                    mem_threshold = ?,
                    theme = ?,
                    data_retention = ?,
                    update_time = ?
                WHERE id = 1
            ''', [
                settings_data.get('refresh_interval', 5),
                settings_data.get('cpu_threshold', 80),
                settings_data.get('mem_threshold', 80),
                settings_data.get('theme', 'dark'),
                settings_data.get('data_retention', 7),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
            conn.commit()
            conn.close()
            logger.info(f"✅ 保存系统设置成功：{settings_data}")
            return jsonify({'status': 'success', 'message': '设置保存成功！'}), 200
    except Exception as e:
        logger.error(f"❌ /api/settings 报错：{str(e)}")
        return jsonify({'error': '处理设置失败', 'detail': str(e)}), 500

# ===================== 启动服务 =====================
if __name__ == '__main__':
    init_db()  # 初始化数据库（包含新增表）
    collect_server_data()  # 启动定时采集任务（首次执行）
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
