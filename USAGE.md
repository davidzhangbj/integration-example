# 使用指南

## 快速开始

### 方式一：一键启动脚本（推荐）

```bash
./start.sh
```

脚本会自动：
1. 检查环境（Node.js、Python）
2. 安装前端和后端依赖
3. 启动所有服务

访问：http://localhost:3000

### 方式二：Docker Compose

```bash
docker-compose up -d
```

访问：http://localhost:3000

### 方式三：手动启动

#### 1. 启动后端服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
python backend/app.py
```

后端服务将运行在：http://localhost:5000

#### 2. 启动前端服务

```bash
# 安装依赖
npm install

# 启动前端
npm run dev
```

前端服务将运行在：http://localhost:3000

## 配置说明

### StarRocks 源数据库配置

- **主机**：StarRocks FE 节点地址
- **端口**：FE 查询端口（默认 9030）
- **用户名**：数据库用户名
- **密码**：数据库密码
- **数据库**：要同步的数据库名称
- **表名**：要同步的表名称

### OceanBase 目标数据库配置

- **主机**：OceanBase OBServer 节点地址
- **端口**：OceanBase 访问端口（默认 2883）
- **用户名**：格式为 `username@tenant`（例如：`root@test`）
- **密码**：数据库密码
- **数据库**：目标数据库名称
- **表名**：目标表名称

### FlinkOMT 高级配置

- **检查点间隔**：Checkpoint 间隔时间（毫秒），默认 60000ms
- **并行度**：任务并行度，默认 1

## 使用流程

### 第一步：填写配置

1. 打开 Web 界面（http://localhost:3000）
2. 填写 StarRocks 源数据库连接信息
3. 填写 OceanBase 目标数据库连接信息
4. （可选）调整 FlinkOMT 高级配置

### 第二步：启动任务

1. 点击"启动同步任务"按钮
2. 系统将自动：
   - 生成 FlinkOMT SQL 配置
   - 提交到 Flink 集群执行
   - 显示任务状态和日志

### 第三步：监控任务

在任务运行过程中：
- 查看实时日志输出
- 查看任务运行状态
- 需要时可以停止任务

### 第四步：查询数据库（新功能）

在配置页面下方，提供了数据库查询工具：

**快速查询**：
- **表结构**：点击"表结构"按钮，快速查看表的结构信息
- **表数据**：点击"表数据"按钮，快速查看表中的数据（最多100条）

**自定义 SQL 查询**：
- 在 SQL 输入框中输入任意 SQL 语句
- 点击"执行 SQL"按钮执行查询
- 查询结果会以表格形式展示

**支持的操作**：
- ✅ SELECT 查询
- ✅ DESC / DESCRIBE 查看表结构
- ✅ SHOW 命令
- ✅ 其他 SQL 语句（INSERT、UPDATE、DELETE 等，注意风险）

**注意事项**：
- 所有 SQL 都会在配置的数据库上执行
- 表数据查询默认限制为 100 条
- 建议只使用查询语句，避免修改数据

## 表结构要求

源表和目标表的结构需要兼容。建议字段类型一致，例如：

```sql
-- StarRocks 源表
CREATE TABLE source_table (
    id BIGINT,
    name VARCHAR(100),
    value DOUBLE,
    update_time TIMESTAMP
) PRIMARY KEY (id);

-- OceanBase 目标表
CREATE TABLE target_table (
    id BIGINT,
    name VARCHAR(100),
    value DOUBLE,
    update_time TIMESTAMP,
    PRIMARY KEY (id)
);
```

## 常见问题

### Q1: 任务提交失败

**可能原因**：
- Flink 集群未启动
- 未安装必要的 FlinkOMT Connector
- 网络无法访问 Flink REST API

**解决方法**：
1. 检查 Flink 集群状态：`curl http://localhost:8081/overview`
2. 确保安装了 `flink-connector-mysql-cdc` 和 `flink-connector-oceanbase`
3. 检查网络连接

### Q2: 连接数据库失败

**可能原因**：
- 数据库配置信息错误
- 网络无法访问数据库
- 数据库服务未启动
- 用户权限不足

**解决方法**：
1. 检查数据库配置是否正确
2. 使用数据库客户端测试连接
3. 检查防火墙设置
4. 确认用户有相应权限

### Q3: 数据没有同步

**可能原因**：
- 源表中没有数据
- 表结构不匹配
- FlinkOMT Connector 配置错误

**解决方法**：
1. 检查源表是否有数据
2. 验证表结构是否匹配
3. 查看 Flink 任务日志
4. 检查 FlinkOMT SQL 配置

### Q4: 任务一直运行但没有同步数据

**可能原因**：
- 源表没有新的变更数据
- CDC 配置错误

**解决方法**：
1. 在源表中插入或更新一些测试数据
2. 检查 FlinkOMT 的 `scan.startup.mode` 配置
3. 查看 Flink 任务日志中的错误信息

## 环境要求

### 必需组件

- Node.js 18+
- Python 3.11+
- Flink 1.17+
- StarRocks 数据库
- OceanBase 数据库

### FlinkOMT Connector

确保 Flink 集群已安装以下 Connector：

1. **flink-connector-mysql-cdc**
   ```bash
   # 下载并放置到 Flink lib 目录
   wget https://repo1.maven.org/maven2/com/ververica/flink-sql-connector-mysql-cdc/2.4.0/flink-sql-connector-mysql-cdc-2.4.0.jar
   cp flink-sql-connector-mysql-cdc-2.4.0.jar $FLINK_HOME/lib/
   ```

2. **flink-connector-oceanbase** 或 **JDBC Connector**
   ```bash
   # 使用 JDBC Connector 连接到 OceanBase
   wget https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.1.0-1.17/flink-connector-jdbc-3.1.0-1.17.jar
   cp flink-connector-jdbc-3.1.0-1.17.jar $FLINK_HOME/lib/
   
   # OceanBase JDBC Driver
   wget https://repo1.maven.org/maven2/com/oceanbase/oceanbase-client/2.4.3/oceanbase-client-2.4.3.jar
   cp oceanbase-client-2.4.3.jar $FLINK_HOME/lib/
   ```

## 高级配置

### 自定义 FlinkOMT SQL

如果需要修改 FlinkOMT SQL 模板，可以编辑 `config/flinkomt-template.sql` 文件。

### 修改后端逻辑

后端代码在 `backend/app.py`，可以根据实际需求修改：
- Flink 任务提交逻辑
- 任务状态监控方式
- 日志收集逻辑

### 环境变量配置

后端支持以下环境变量：

- `FLINK_HOME`：Flink 安装目录（默认：`/opt/flink`）
- `FLINK_REST_URL`：Flink REST API 地址（默认：`http://localhost:8081`）

设置方式：

```bash
export FLINK_HOME=/path/to/flink
export FLINK_REST_URL=http://flink-jobmanager:8081
python backend/app.py
```

## 技术支持

如有问题，请检查：
1. 后端服务日志
2. Flink 任务日志
3. 浏览器控制台错误信息

