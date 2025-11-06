import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# 测试配置
starrocks_config = {
    'host': '127.0.0.1',
    'port': '9030',
    'username': 'root',
    'password': '123456',
    'database': 'sys'  # StarRocks 默认数据库
}

oceanbase_config = {
    'host': '127.0.0.1',
    'port': '2881',
    'username': 'root@test',
    'password': '123456',
    'database': 'test'  # OceanBase 默认数据库
}

# 测试 execute_sql API
if __name__ == '__main__':
    with app.test_client() as client:
        print("=" * 60)
        print("正在测试 execute_sql API...")
        print("=" * 60)
        
        # 测试 StarRocks 的 SHOW DATABASES
        print("\n[测试1] 测试 StarRocks 的 SHOW DATABASES")
        print("-" * 60)
        print(f"配置: {starrocks_config}")
        print(f"SQL: SHOW DATABASES")
        
        response = client.post('/api/execute-sql',
                              json={
                                  'dbType': 'starrocks',
                                  'sql': 'SHOW DATABASES',
                                  'config': starrocks_config
                              },
                              content_type='application/json')
        
        print(f"\n状态码: {response.status_code}")
        result = response.get_json()
        print(f"响应内容: {result}")
        
        if response.status_code == 200 and result.get('success'):
            print("\n✓ StarRocks SHOW DATABASES 测试成功！")
            print(f"  列名: {result.get('columns', [])}")
            print(f"  行数: {result.get('rowCount', 0)}")
            if result.get('rows'):
                print(f"  前3个数据库:")
                for i, row in enumerate(result.get('rows', [])[:3], 1):
                    print(f"    {i}. {row}")
        else:
            print(f"\n✗ StarRocks SHOW DATABASES 测试失败")
            print(f"  错误: {result.get('error', '未知错误')}")
            exit(1)
        
        # 测试 OceanBase 的 SHOW DATABASES
        print("\n" + "=" * 60)
        print("[测试2] 测试 OceanBase 的 SHOW DATABASES")
        print("-" * 60)
        print(f"配置: {oceanbase_config}")
        print(f"SQL: SHOW DATABASES")
        
        response = client.post('/api/execute-sql',
                              json={
                                  'dbType': 'oceanbase',
                                  'sql': 'SHOW DATABASES',
                                  'config': oceanbase_config
                              },
                              content_type='application/json')
        
        print(f"\n状态码: {response.status_code}")
        result = response.get_json()
        print(f"响应内容: {result}")
        
        if response.status_code == 200 and result.get('success'):
            print("\n✓ OceanBase SHOW DATABASES 测试成功！")
            print(f"  列名: {result.get('columns', [])}")
            print(f"  行数: {result.get('rowCount', 0)}")
            if result.get('rows'):
                print(f"  前3个数据库:")
                for i, row in enumerate(result.get('rows', [])[:3], 1):
                    print(f"    {i}. {row}")
        else:
            print(f"\n✗ OceanBase SHOW DATABASES 测试失败")
            print(f"  错误: {result.get('error', '未知错误')}")
            exit(1)
        
        # 测试总结
        print("\n" + "=" * 60)
        print("✓ 所有测试完成！")
        print("=" * 60)

