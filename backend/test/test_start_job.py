import sys
import os
import time

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# 测试配置
test_config = {
    'starrocks': {
        'host': '127.0.0.1',
        'port': '9030',
        'username': 'root',
        'password': '123456',
        'tables': 'test2.*'
    },
    'oceanbase': {
        'host': '127.0.0.1',
        'port': '2881',
        'username': 'root@test',
        'password': '123456',
        'database': 'test2'
    },
    'flinkOMT': {
        'parallelism': '2',
        'checkpointInterval': '10000'
    }
}

# 测试 start_job 和 job_status
if __name__ == '__main__':
    with app.test_client() as client:
        print("=" * 60)
        print("正在测试 start_job 和 job_status API...")
        print("=" * 60)
        
        # 步骤1: 启动 Job
        print("\n[步骤1] 启动 Job...")
        print("-" * 60)
        response = client.post('/api/start-job', 
                              json=test_config,
                              content_type='application/json')
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.get_json()}")
        
        if response.status_code != 200:
            print(f"\n✗ 启动 Job 失败: {response.get_json()}")
            exit(1)
        
        result = response.get_json()
        job_id = result.get('jobId')
        if not job_id:
            print(f"\n✗ 未获取到 Job ID: {response.get_json()}")
            exit(1)
        
        print(f"\n✓ Job 已启动")
        print(f"Job ID: {job_id}")
        print(f"初始状态: {result.get('status')}")
        
        # 步骤2: 监控 Job 状态
        print("\n[步骤2] 监控 Job 状态...")
        print("-" * 60)
        
        max_iterations = 1800  # 最多监控1小时（假设每2秒检查一次）
        check_interval = 2  # 每2秒检查一次状态
        iteration = 0
        final_status = None
        
        while iteration < max_iterations:
            iteration += 1
            
            # 获取 Job 状态
            status_response = client.get(f'/api/job-status/{job_id}')
            
            if status_response.status_code != 200:
                print(f"\n✗ 获取 Job 状态失败: {status_response.get_json()}")
                break
            
            status_data = status_response.get_json()
            current_status = status_data.get('status', 'UNKNOWN')
            flink_job_id = status_data.get('flinkJobId')
            logs = status_data.get('logs', [])
            last_update = status_data.get('lastUpdate', '')
            
            # 打印当前状态
            print(f"\n[{iteration}] 检查状态 (第 {iteration} 次)")
            print(f"  状态: {current_status}")
            if flink_job_id:
                print(f"  Flink Job ID: {flink_job_id}")
            if last_update:
                print(f"  最后更新: {last_update}")
            
            # 打印最新日志
            if logs:
                print(f"  最新日志:")
                for log in logs[-3:]:  # 只显示最近3条日志
                    print(f"    - {log}")
            
            # 检查是否为最终状态
            if current_status in ['FINISHED', 'FAILED', 'CANCELED']:
                final_status = current_status
                print(f"\n{'=' * 60}")
                print(f"Job 已结束，最终状态: {final_status}")
                print(f"{'=' * 60}")
                
                # 打印所有日志
                if logs:
                    print(f"\n完整日志:")
                    print("-" * 60)
                    for i, log in enumerate(logs, 1):
                        print(f"{i}. {log}")
                
                break
            
            # 等待下次检查
            time.sleep(check_interval)
        
        # 最终结果
        print(f"\n{'=' * 60}")
        if final_status:
            if final_status == 'FINISHED':
                print("✓ 测试完成：Job 执行成功！")
            elif final_status == 'FAILED':
                print("✗ 测试完成：Job 执行失败！")
            elif final_status == 'CANCELED':
                print("⚠ 测试完成：Job 已取消！")
        else:
            print("⚠ 测试超时：达到最大监控次数，Job 仍在运行中")
        print(f"{'=' * 60}")

