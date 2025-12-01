import paramiko
import logging

logging.basicConfig(level=logging.DEBUG)

def test_connection():
    try:
        print("🔍 开始测试SSH连接...")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print("📡 连接到 192.168.80.131...")
        
        # 使用您实际的root密码
        password = "123456"  # 替换为您实际的root密码
        
        ssh.connect(
            '192.168.80.131', 
            22, 
            'root', 
            password,  # 使用实际密码
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        print("✅ SSH连接成功！")
        
        # 测试命令执行
        stdin, stdout, stderr = ssh.exec_command('uname -a', timeout=5)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        print(f"📋 系统信息: {output}")
        if error:
            print(f"⚠️ 错误信息: {error}")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ SSH连接失败: {e}")
        return False

if __name__ == '__main__':
    test_connection()
