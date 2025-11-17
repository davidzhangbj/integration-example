from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import time
import uuid
from datetime import datetime, timezone, timedelta
import pymysql
import pymysql.cursors
import re
import requests

# 东八区时区（上海时区）
TZ_SHANGHAI = timezone(timedelta(hours=8))

def get_shanghai_time():
    """获取东八区（上海）当前时间"""
    return datetime.now(TZ_SHANGHAI)

app = Flask(__name__)
CORS(app)

# 存储任务状态
jobs = {}

# Flink 相关配置
FLINK_HOME = os.getenv('FLINK_HOME', '/root/flink/flink-1.19.1')
FLINK_REST_URL = os.getenv('FLINK_REST_URL', 'http://jobmanager:8081')

def extract_flink_job_id(output):
    """从 Flink 命令输出中提取 Job ID"""
    if not output:
        return None
    
    # Flink 输出中常见的 Job ID 模式
    # 例如: "Job has been submitted with JobID a1b2c3d4e5f6g7h8"
    patterns = [
        r'Job\s+has\s+been\s+submitted\s+with\s+JobID\s+([a-f0-9]{32})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def generate_flinkomt_config(config):
    """生成 FlinkOMT 配置文件"""
    starrocks = config['starrocks']
    oceanbase = config['oceanbase']
    flinkomt = config['flinkOMT']
    
    
    # 构建 StarRocks JDBC URL
    starrocks_jdbc_url = f"jdbc:mysql://{starrocks.get('host', '127.0.0.1')}:{starrocks.get('port', '9030')}/sys"
    
    # 构建 StarRocks Scan URL (FE 端口，通常是 8030)
    scan_port = starrocks.get('scanPort', '8030')
    scan_url = f"{starrocks.get('host', '127.0.0.1')}:{scan_port}"
    tables = starrocks.get('tables', '')
    
    
    # 构建 OceanBase JDBC URL
    oceanbase_url = f"jdbc:mysql://{oceanbase.get('host', '127.0.0.1')}:{oceanbase.get('port', '2881')}/test"
    
    # FlinkOMT YAML 配置
    yaml_content = f"""
source:
  type: starrocks
  jdbc-url: {starrocks_jdbc_url}
  username: {starrocks.get('username', 'root')}
  password: {starrocks.get('password', '')}
  scan-url: {scan_url}
  scan.max-retries: {starrocks.get('scanMaxRetries', '1')}
  tables: {tables}

oceanbase:
  url: {oceanbase_url}
  username: {oceanbase.get('username', 'root@test')}
  password: {oceanbase.get('password', '')}
  schema-name: test

pipeline:
  name: Sync StarRocks Database to OceanBase
  parallelism: {flinkomt.get('parallelism', '2')}
"""
    return yaml_content

@app.route('/api/start-job', methods=['POST'])
def start_job():
    """启动 FlinkOMT 任务"""
    try:
        config = request.json
        job_id = str(uuid.uuid4())
        print('job_id: ', job_id)
        
        # 生成 FlinkOMT YAML 配置文件
        yaml_content = generate_flinkomt_config(config)
        config_file = f'/tmp/flinkomt_{job_id}.yaml'
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        # 提交 Flink 任务
        flinkomt = config['flinkOMT']
        
        # 转换 checkpointInterval 从毫秒到秒
        checkpoint_interval_ms = int(flinkomt.get('checkpointInterval', '10000'))
        checkpoint_interval_sec = checkpoint_interval_ms // 1000
        parallelism = flinkomt.get('parallelism', '1')
        
        # 构建 FlinkOMT 启动命令
        flink_cmd = [
            f'{FLINK_HOME}/bin/flink',
            'run',
            '-m', 'jobmanager:8081',
            '-d',  # 后台运行
            '-D', f'execution.checkpointing.interval={checkpoint_interval_sec}s',
            '-D', f'parallelism.default={parallelism}',
            '-c', 'com.oceanbase.omt.cli.CommandLineCliFront',
            f'{FLINK_HOME}/lib/flink-omt-flink_1.18-1.1.jar',
            '-config', config_file,
            '--skip-confirm'
        ]
        
        # 提交 Flink 任务
        process = subprocess.Popen(
            flink_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待进程完成并获取输出 (Flink 命令会立即返回 Job ID)
        try:
            stdout, stderr = process.communicate(timeout=30)
            output = stdout + stderr if stderr else stdout
            
            # 从输出中提取 Flink Job ID
            flink_job_id = extract_flink_job_id(output)
            
            if flink_job_id:
                logs = [f'任务已提交，Job ID: {flink_job_id}']
            else:
                logs = ['任务已提交，等待启动...', f'输出: {output[:200]}']
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            output = stdout + stderr if stderr else stdout
            flink_job_id = extract_flink_job_id(output)
            logs = ['任务提交超时，尝试提取 Job ID...']
            if flink_job_id:
                logs.append(f'已提取 Job ID: {flink_job_id}')
        except Exception as e:
            flink_job_id = None
            logs = [f'任务提交时出错: {str(e)}']
        
        # 初始化任务状态
        jobs[flink_job_id] = {
            'job_id': flink_job_id,
            'status': 'SUBMITTED',
            'config': config,
            'config_file': config_file,
            'process': process,
            'logs': logs,
            'last_log_count': len(logs),  # 记录上次返回的日志数量
            'last_status': 'SUBMITTED',  # 记录上次的状态，用于避免重复添加状态日志
            'start_time': get_shanghai_time().isoformat(),
            'last_update': get_shanghai_time().isoformat()
        }
        
        return jsonify({
            'jobId': flink_job_id, 
            'status': 'submitted',
            'logs': logs,
            'lastUpdate': get_shanghai_time().isoformat()  # 返回东八区时间戳
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/job-status/<job_id>', methods=['GET'])
def job_status(job_id):
    """获取任务状态"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': '任务不存在'}), 404
    
    try:
        # 尝试从 Flink REST API 获取任务状态
        if job.get('job_id'):
            response = requests.get(f'{FLINK_REST_URL}/jobs/{job["job_id"]}')
            if response.status_code == 200:
                job_data = response.json()
                state = job_data.get('state', 'UNKNOWN')
                previous_status = job.get('last_status', '')
                
                # 更新状态
                job['status'] = state
                
                # 对于 RUNNING 状态，每次轮询都添加日志，让用户知道任务在运行
                if state == 'RUNNING':
                    job['logs'].append('任务正在运行中...')
                    job['last_status'] = state
                # 对于其他状态，只在状态变化时添加日志
                elif state != previous_status:
                    job['last_status'] = state
                    if state == 'FINISHED':
                        job['logs'].append('任务已完成！')
                    elif state == 'FAILED':
                        job['logs'].append('任务执行失败')
                    elif state == 'CANCELED':
                        job['logs'].append('任务已取消')
        else:
            # 没有 flink_job_id，返回无任务在执行
            previous_status = job.get('last_status', '')
            if previous_status != 'NO_JOB':
                job['status'] = 'NO_JOB'
                job['last_status'] = 'NO_JOB'
                job['logs'].append('无任务在执行')
            
        job['last_update'] = get_shanghai_time().isoformat()
    except Exception as e:
        error_msg = f'监控错误: {str(e)}'
        # 避免重复添加相同的错误日志
        if not job.get('logs') or job['logs'][-1] != error_msg:
            job['logs'].append(error_msg)
    
    # 只返回新增的日志（从上次返回的位置开始）
    last_log_count = job.get('last_log_count', 0)
    all_logs = job.get('logs', [])
    new_logs = all_logs[last_log_count:]
    
    # 更新上次返回的日志数量
    job['last_log_count'] = len(all_logs)
    
    # 返回任务状态信息
    return jsonify({
        'jobId': job['job_id'],
        'status': job['status'],
        'logs': new_logs,  # 只返回新增的日志
        'startTime': job.get('start_time'),
        'lastUpdate': job.get('last_update')
    })

@app.route('/api/stop-job/<job_id>', methods=['POST'])
def stop_job(job_id):
    """停止任务"""
    if job_id not in jobs:
        return jsonify({'error': '任务不存在'}), 404
    
    job = jobs[job_id]
    flink_job_id = job.get('job_id')
    
    if not flink_job_id:
        job['status'] = 'CANCELED'
        job['logs'].append('任务已停止（无 Flink Job ID）')
        return jsonify({'status': 'stopped'})
    
    try:
        # 发送取消请求 - 使用 GET 方法访问 yarn-cancel 端点
        cancel_url = f'{FLINK_REST_URL}/jobs/{flink_job_id}/yarn-cancel'
        response = requests.get(cancel_url, timeout=30)
        
        if response.status_code not in [200, 202]:
            # 如果 GET yarn-cancel 失败，尝试标准的 PATCH cancel 端点
            cancel_url = f'{FLINK_REST_URL}/jobs/{flink_job_id}/cancel'
            response = requests.patch(cancel_url, headers={'Content-Type': 'application/json'}, timeout=30)
            
            if response.status_code not in [200, 202]:
                error_msg = f'取消 Flink 任务失败: HTTP {response.status_code}'
                try:
                    error_detail = response.json().get('errors', [])
                    if error_detail:
                        error_msg += f' - {error_detail[0] if isinstance(error_detail, list) else error_detail}'
                except:
                    error_msg += f' - {response.text[:200]}'
                job['logs'].append(error_msg)
                return jsonify({'error': error_msg}), 500
        
        job['logs'].append('已发送取消请求到 Flink 集群')
        
        # 等待任务真正取消，最多等待 30 秒
        max_wait_time = 30
        check_interval = 1
        waited_time = 0
        last_state = None
        
        while waited_time < max_wait_time:
            try:
                status_response = requests.get(f'{FLINK_REST_URL}/jobs/{flink_job_id}', timeout=5)
                if status_response.status_code == 200:
                    job_data = status_response.json()
                    state = job_data.get('state', 'UNKNOWN')
                    
                    # 只在状态变化时记录日志，避免重复
                    if state != last_state:
                        last_state = state
                        if state in ['CANCELED', 'FAILED', 'FINISHED']:
                            job['status'] = state
                            job['logs'].append(f'任务已成功取消，最终状态: {state}')
                            break
                        elif state == 'CANCELLING':
                            job['logs'].append('任务正在取消中...')
                    elif state in ['CANCELED', 'FAILED', 'FINISHED']:
                        break
                elif status_response.status_code == 404:
                    # 任务不存在，可能已经取消
                    job['logs'].append('任务已不存在，可能已成功取消')
                    break
            except requests.exceptions.RequestException:
                # 请求失败，可能任务已经不存在
                if waited_time > 5:  # 至少等待 5 秒后再判断
                    job['logs'].append('无法连接到 Flink REST API，可能任务已取消')
                    break
            
            time.sleep(check_interval)
            waited_time += check_interval
        
        if waited_time >= max_wait_time and job.get('status') not in ['CANCELED', 'FAILED', 'FINISHED']:
            job['logs'].append('等待任务取消超时，但取消请求已发送')
        
        # 终止进程（如果存在）
        if job.get('process'):
            try:
                job['process'].terminate()
                try:
                    job['process'].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    job['process'].kill()
            except Exception as e:
                job['logs'].append(f'终止进程时出错: {str(e)}')
        
        # 更新状态为已取消
        if job.get('status') not in ['CANCELED', 'FAILED', 'FINISHED']:
            job['status'] = 'CANCELED'
        
        # 清理配置文件
        config_file = job.get('config_file', '')
        if config_file and os.path.exists(config_file):
            try:
                os.remove(config_file)
            except Exception as e:
                job['logs'].append(f'清理配置文件时出错: {str(e)}')
        
        return jsonify({'status': 'stopped'})
        
    except requests.exceptions.RequestException as e:
        error_msg = f'请求 Flink REST API 失败: {str(e)}'
        job['logs'].append(error_msg)
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        error_msg = f'停止任务时出错: {str(e)}'
        job['logs'].append(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """基础健康检查"""
    return jsonify({'status': 'ok'})

@app.route('/api/health/starrocks', methods=['POST'])
def health_starrocks():
    """检查 StarRocks 连接"""
    try:
        data = request.json or {}
        starrocks_config = data.get('starrocks') or data
        
        if not starrocks_config:
            return jsonify({
                'status': 'error',
                'connected': False,
                'error': '未提供 StarRocks 配置'
            }), 400
        
        # 尝试连接并执行简单查询
        conn = get_starrocks_connection(starrocks_config)
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'connected': True,
            'message': 'StarRocks 连接成功'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'connected': False,
            'error': str(e)
        }), 503

@app.route('/api/health/oceanbase', methods=['POST'])
def health_oceanbase():
    """检查 OceanBase 连接"""
    try:
        data = request.json or {}
        oceanbase_config = data.get('oceanbase') or data
        
        if not oceanbase_config:
            return jsonify({
                'status': 'error',
                'connected': False,
                'error': '未提供 OceanBase 配置'
            }), 400
        
        # 尝试连接并执行简单查询
        conn = get_oceanbase_connection(oceanbase_config)
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'connected': True,
            'message': 'OceanBase 连接成功'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'connected': False,
            'error': str(e)
        }), 503

@app.route('/api/health/flink', methods=['GET'])
def health_flink():
    """检查 Flink 集群状态"""
    try:
        # 检查 Flink REST API 是否可访问
        timeout = 5  # 5秒超时
        response = requests.get(f'{FLINK_REST_URL}/overview', timeout=timeout)
        
        if response.status_code == 200:
            return jsonify({
                'status': 'ok',
                'connected': True,
                'message': 'Flink 集群运行正常'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'connected': False,
                'error': f'Flink REST API 返回错误状态码: {response.status_code}'
            }), 503
            
    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'error',
            'connected': False,
            'error': f'连接 Flink REST API 超时: {FLINK_REST_URL}'
        }), 503
    except requests.exceptions.ConnectionError:
        return jsonify({
            'status': 'error',
            'connected': False,
            'error': f'无法连接到 Flink REST API: {FLINK_REST_URL}'
        }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'connected': False,
            'error': str(e)
        }), 503

def get_starrocks_connection(config):
    """获取 StarRocks 数据库连接"""
    try:
        # database 字段可选，如果不存在则使用空字符串（连接但不选择数据库）
        database = config.get('database', '')
        connection = pymysql.connect(
            host=config['host'],
            port=int(config['port']),
            user=config['username'],
            password=config['password'],
            database=database if database else None,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        return connection
    except Exception as e:
        raise Exception(f"连接 StarRocks 失败: {str(e)}")

def get_oceanbase_connection(config):
    """获取 OceanBase 数据库连接"""
    try:
        # database 字段可选，如果不存在则使用空字符串（连接但不选择数据库）
        database = config.get('database', '')
        connection = pymysql.connect(
            host=config['host'],
            port=int(config['port']),
            user=config['username'],
            password=config['password'],
            database=database if database else None,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        return connection
    except Exception as e:
        raise Exception(f"连接 OceanBase 失败: {str(e)}")

@app.route('/api/execute-sql', methods=['POST'])
def execute_sql():
    """执行 SQL 查询"""
    try:
        data = request.json
        db_type = data.get('dbType')  # 'starrocks' or 'oceanbase'
        sql = data.get('sql')
        db_config = data.get('config')
        
        if not sql or not sql.strip():
            return jsonify({'error': 'SQL 语句不能为空'}), 400
        
        if not db_config:
            return jsonify({'error': '数据库配置不能为空'}), 400
        
        # 获取数据库连接
        if db_type == 'starrocks':
            connection = get_starrocks_connection(db_config)
        elif db_type == 'oceanbase':
            connection = get_oceanbase_connection(db_config)
        else:
            return jsonify({'error': '不支持的数据库类型'}), 400
        
        try:
            with connection.cursor() as cursor:
                # 支持多语句执行（用分号分隔）
                statements = [s.strip() for s in sql.split(';') if s.strip()]
                
                if not statements:
                    return jsonify({'error': 'SQL 语句不能为空'}), 400
                
                # 执行前面的语句（如 USE database）
                for stmt in statements[:-1]:
                    cursor.execute(stmt)
                
                # 执行最后一条语句（实际的 SQL）
                final_sql = statements[-1]
                cursor.execute(final_sql)
                
                # 判断最后一条语句是否是查询语句
                sql_upper = final_sql.strip().upper()
                if sql_upper.startswith('SELECT') or sql_upper.startswith('DESC') or sql_upper.startswith('DESCRIBE') or sql_upper.startswith('SHOW'):
                    # 查询语句，返回结果
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    
                    return jsonify({
                        'success': True,
                        'columns': columns,
                        'rows': results,
                        'rowCount': len(results)
                    })
                else:
                    # 非查询语句，返回影响的行数
                    connection.commit()
                    affected_rows = cursor.rowcount
                    return jsonify({
                        'success': True,
                        'message': f'执行成功，影响 {affected_rows} 行',
                        'affectedRows': affected_rows
                    })
        finally:
            connection.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

