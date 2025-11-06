import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_oceanbase_connection

# 配置项 - 在这里输入你的 OceanBase 连接信息
config = {
    'host': 'localhost',
    'port': '2881',
    'username': 'root@test',  # 如果包含租户，格式为: 'user@tenant'
    'password': '123456',
    'database': 'test2'
}

# 测试连接
if __name__ == '__main__':
    try:
        print("正在连接 OceanBase...")
        print(f"主机: {config['host']}")
        print(f"端口: {config['port']}")
        print(f"用户名: {config['username']}")
        print(f"数据库: {config['database']}")
        print("-" * 50)
        
        connection = get_oceanbase_connection(config)
        
        print("✓ 连接成功！")
        print(f"连接对象: {connection}")
        
        # 测试执行一个简单查询
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"测试查询结果: {result}")
        
        connection.close()
        print("✓ 连接已关闭")
        
    except Exception as e:
        print(f"✗ 连接失败: {e}")

