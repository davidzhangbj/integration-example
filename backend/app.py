from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import subprocess
import threading
import time
import uuid
from datetime import datetime
import pymysql
import pymysql.cursors
import re
import requests

app = Flask(__name__)
CORS(app)

# 存储任务状态
jobs = {}

# Flink 相关配置
FLINK_HOME = os.getenv('FLINK_HOME', '/root/flink/flink-1.19.1')
FLINK_REST_URL = os.getenv('FLINK_REST_URL', 'http://localhost:8081')

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
    yaml_content = f"""################################################################################

# Description: Sync StarRocks all tables to OceanBase

################################################################################

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
        jobs[job_id] = {
            'id': job_id,
            'status': 'SUBMITTED',
            'config': config,
            'config_file': config_file,
            'process': process,
            'flink_job_id': flink_job_id,
            'logs': logs,
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }
        
        return jsonify({'jobId': job_id, 'status': 'submitted'})
    
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
        if job.get('flink_job_id'):
            response = requests.get(f'{FLINK_REST_URL}/jobs/{job["flink_job_id"]}')
            if response.status_code == 200:
                job_data = response.json()
                state = job_data.get('state', 'UNKNOWN')
                job['status'] = state
                if state == 'RUNNING':
                    job['logs'].append('任务正在运行中...')
                elif state == 'FINISHED':
                    job['logs'].append('任务已完成！')
                elif state == 'FAILED':
                    job['logs'].append('任务执行失败')
        else:
            # 没有 flink_job_id，返回无任务在执行
            job['status'] = 'NO_JOB'
            job['logs'].append('无任务在执行')
            
        job['last_update'] = datetime.now().isoformat()
    except Exception as e:
        job['logs'].append(f'监控错误: {str(e)}')
    
    # 返回任务状态信息
    return jsonify({
        'jobId': job['id'],
        'status': job['status'],
        'flinkJobId': job.get('flink_job_id'),
        'logs': job.get('logs', []),
        'startTime': job.get('start_time'),
        'lastUpdate': job.get('last_update')
    })

@app.route('/api/stop-job/<job_id>', methods=['POST'])
def stop_job(job_id):
    """停止任务"""
    if job_id not in jobs:
        return jsonify({'error': '任务不存在'}), 404
    
    job = jobs[job_id]
    
    try:
        # 停止 Flink 任务
        if job.get('flink_job_id'):
            requests.post(f'{FLINK_REST_URL}/jobs/{job["flink_job_id"]}/yarn-cancel')
        
        # 终止进程
        if job.get('process'):
            job['process'].terminate()
        
        job['status'] = 'CANCELED'
        job['logs'].append('任务已停止')
        
        # 清理配置文件
        if os.path.exists(job.get('config_file')):
            os.remove(job['config_file'])
        
        return jsonify({'status': 'stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
                cursor.execute(sql)
                
                # 判断是否是查询语句
                sql_upper = sql.strip().upper()
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

