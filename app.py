from flask import Flask, request, jsonify
from flask_cors import CORS
import paramiko
import subprocess
from datetime import datetime
import threading
import json
import os

app = Flask(__name__)
CORS(app)

# 数据存储文件
DATA_FILE = "monitor_data.json"

# 全局数据结构
HOSTS = {}
METRICS = {}
LOCK = threading.Lock()

def load_data():
    """从文件加载数据"""
    global HOSTS, METRICS
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                HOSTS = data.get('hosts', {})
                METRICS = data.get('metrics', {})
                print(f"✅ 加载数据: {len(HOSTS)} 台主机")
    except Exception as e:
        print(f"❌ 加载数据失败: {e}")

def save_data():
    """保存数据到文件"""
    try:
        with LOCK:
            data = {
                'hosts': HOSTS,
                'metrics': METRICS,
                'last_update': datetime.now().isoformat()
            }
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ 保存数据失败: {e}")

def ping_host(ip):
    """Ping检测主机是否在线"""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3
        )
        return result.returncode == 0
    except:
        return False

def collect_metrics_simple(ip, username, password):
    """简化的数据采集"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, 22, username, password, timeout=10)
        
        # 采集CPU使用率
        cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
        stdin, stdout, stderr = ssh.exec_command(cpu_cmd)
        cpu_usage = stdout.read().decode().strip()
        cpu = float(cpu_usage) if cpu_usage else 0.0
        
        # 采集内存使用率
        mem_cmd = "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100}'"
        stdin, stdout, stderr = ssh.exec_command(mem_cmd)
        mem_usage = stdout.read().decode().strip()
        mem = float(mem_usage) if mem_usage else 0.0
        
        ssh.close()
        
        return {
            'cpu': cpu,
            'memory': mem,
            'disk': 0,  # 简化版本
            'error': None
        }
    except Exception as e:
        return {
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'error': f"SSH连接失败: {str(e)}"
        }

# API路由
@app.route('/')
def index():
    return jsonify({
        'status': 'running',
        'service': 'Server Monitor API',
        'version': '1.0',
        'hosts_count': len(HOSTS)
    })

@app.route('/api/hosts', methods=['GET'])
def get_hosts():
    """获取主机列表"""
    hosts_list = []
    with LOCK:
        for ip, info in HOSTS.items():
            host_info = {
                'ip': ip,
                'username': info['username'],
                'alerts': METRICS.get(ip, {}).get('alerts', []),
                'last_update': METRICS.get(ip, {}).get('last_update')
            }
            hosts_list.append(host_info)
    return jsonify(hosts_list)

@app.route('/api/hosts', methods=['POST'])
def add_host():
    """添加主机"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的JSON数据'}), 400
        
        ip = data.get('ip', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not ip or not username or not password:
            return jsonify({'error': '请填写完整的主机信息'}), 400
        
        # 简单的IP验证
        import re
        ip_regex = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if not ip_regex.match(ip):
            return jsonify({'error': '请输入有效的IP地址'}), 400
        
        # 测试连接
        print(f"🔍 测试连接到主机 {ip}...")
        if not ping_host(ip):
            return jsonify({'error': '无法ping通主机，请检查IP地址和网络连接'}), 400
        
        with LOCK:
            HOSTS[ip] = {
                'username': username,
                'password': password
            }
            
            # 立即采集一次数据
            print(f"📊 采集主机 {ip} 的初始数据...")
            result = collect_metrics_simple(ip, username, password)
            
            if result['error']:
                METRICS[ip] = {
                    'cpu': [0], 
                    'memory': [0], 
                    'disk': [0],
                    'alerts': [result['error']], 
                    'last_update': datetime.now().isoformat()
                }
            else:
                METRICS[ip] = {
                    'cpu': [result['cpu']], 
                    'memory': [result['memory']], 
                    'disk': [result['disk']],
                    'alerts': [],
                    'last_update': datetime.now().isoformat()
                }
            
            save_data()
        
        print(f"✅ 主机 {ip} 添加成功")
        return jsonify({'message': f'主机 {ip} 添加成功'})
    
    except Exception as e:
        print(f"❌ 添加主机失败: {str(e)}")
        return jsonify({'error': f'添加主机失败: {str(e)}'}), 500

@app.route('/api/hosts/<ip>', methods=['DELETE'])
def delete_host(ip):
    """删除主机"""
    with LOCK:
        if ip in HOSTS:
            del HOSTS[ip]
            if ip in METRICS:
                del METRICS[ip]
            save_data()
            return jsonify({'message': f'主机 {ip} 删除成功'})
        else:
            return jsonify({'error': '主机不存在'}), 404

@app.route('/api/metrics')
def get_metrics():
    """获取所有监控数据"""
    with LOCK:
        return jsonify(METRICS)

@app.route('/api/refresh', methods=['POST'])
def refresh_metrics():
    """手动刷新监控数据"""
    try:
        updated_count = 0
        with LOCK:
            for ip, info in HOSTS.items():
                print(f"🔄 刷新主机 {ip} 的数据...")
                result = collect_metrics_simple(ip, info['username'], info['password'])
                
                if ip not in METRICS:
                    METRICS[ip] = {'cpu': [], 'memory': [], 'disk': [], 'alerts': []}
                
                if result['error']:
                    METRICS[ip]['alerts'] = [result['error']]
                else:
                    # 添加新数据点
                    METRICS[ip]['cpu'].append(result['cpu'])
                    METRICS[ip]['memory'].append(result['memory'])
                    METRICS[ip]['disk'].append(result['disk'])
                    
                    # 限制数据点数量
                    for key in ['cpu', 'memory', 'disk']:
                        METRICS[ip][key] = METRICS[ip][key][-20:]
                    
                    METRICS[ip]['alerts'] = []
                    updated_count += 1
                
                METRICS[ip]['last_update'] = datetime.now().isoformat()
            
            save_data()
        
        return jsonify({'message': f'数据刷新成功，更新了 {updated_count} 台主机'})
    except Exception as e:
        return jsonify({'error': f'刷新失败: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'hosts_count': len(HOSTS)
    })

if __name__ == '__main__':
    # 加载已有数据
    load_data()
    
    print("🚀 服务器监控系统启动成功!")
    print("📡 API地址: http://0.0.0.0:5000")
    print("🌐 前端地址: http://localhost:8080")
    print("💾 数据文件:", DATA_FILE)
    
    # 稳定版本：移除定时任务，避免资源问题
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)