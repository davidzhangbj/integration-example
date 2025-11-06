# FlinkOMT Demo - StarRocks to OceanBase

这是一个 Web 界面的 FlinkOMT 演示项目，可以帮助用户快速了解和使用 FlinkOMT 进行 StarRocks 到 OceanBase 的数据同步。

## 功能特性

- 🎨 现代化的 Web 界面，操作简单直观
- 🔄 实时任务监控和日志查看
- 📝 图形化配置数据库连接信息
- 🚀 一键启动/停止同步任务
- 📊 实时显示任务运行状态
- 🔍 **SQL 查询工具**：支持查询源数据库和目标数据库的表结构和表数据
- ⚡ **快速查询**：一键查看表结构和表数据（最多100条）
- 📋 **自定义 SQL**：支持执行任意 SQL 查询语句（SELECT、DESC、SHOW 等）
- ✅ **连接测试**：支持测试 StarRocks、OceanBase 和 Flink 集群连接状态
- 🏥 **健康检查**：自动检测数据库和 Flink 集群的健康状态

## 技术栈

- **前端**: React 18 + Vite + Tailwind CSS + React Router
- **后端**: Flask + Python 3.11+
- **数据同步**: FlinkOMT (Apache Flink 1.19.1)
- **数据库**: StarRocks (源) + OceanBase (目标)

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

### 方式二：使用 Docker Compose

```bash
docker-compose up -d
```

访问：http://localhost:3000

### 方式三：手动启动

#### 前置要求

- Node.js 18+ 
- Python 3.11+
- Flink 1.19.1+（已安装并配置好）
- StarRocks 数据库
- OceanBase 数据库

#### 启动步骤

1. **安装前端依赖**
```bash
npm install
```

2. **启动前端开发服务器**
```bash
npm run dev
```

3. **安装后端依赖**
```bash
pip install -r requirements.txt
```

4. **启动后端服务**
```bash
python backend/app.py
```

5. **访问应用**
- 前端：http://localhost:3000
- 后端 API：http://localhost:5000

## 使用说明

### 1. 配置数据库连接

在 Web 界面中填写：

**StarRocks 源数据库**：
- 主机地址：StarRocks FE 节点地址
- 端口：FE 查询端口（默认 9030）
- 用户名：数据库用户名
- 密码：数据库密码
- 表名：要同步的表名称（支持模式匹配，如 `test[1-2].orders[0-9]`）

**OceanBase 目标数据库**：
- 主机地址：OceanBase OBServer 节点地址
- 端口：OceanBase 访问端口（默认 2881）
- 用户名：格式为 `username@tenant`（例如：`root@test`）
- 密码：数据库密码

**FlinkOMT 高级配置**：
- 检查点间隔：Checkpoint 间隔时间（毫秒），默认 60000ms
- 并行度：任务并行度，默认 1

### 2. 测试连接

在启动任务前，可以点击"测试连接"按钮：
- 测试 StarRocks 连接
- 测试 OceanBase 连接
- 测试 Flink 集群状态

### 3. 启动同步任务

点击"启动同步任务"按钮，系统将：
1. 根据配置生成 FlinkOMT YAML 配置文件
2. 提交到 Flink 集群执行
3. 实时显示任务状态和日志

### 4. 监控任务

在任务运行过程中，可以：
- 查看实时日志输出
- 查看任务运行状态（RUNNING、FINISHED、FAILED 等）
- 查看 Flink Job ID
- 停止正在运行的任务

### 5. 查询数据库

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

## 项目结构

```
integration-example/
├── src/                    # 前端源代码
│   ├── pages/             # 页面组件
│   │   └── FlinkOMTPage.jsx  # FlinkOMT 主页面
│   ├── components/        # 公共组件
│   │   └── Layout.jsx     # 布局组件
│   ├── App.jsx            # 主应用组件
│   ├── main.jsx           # 入口文件
│   └── index.css          # 样式文件
├── backend/               # 后端源代码
│   ├── app.py             # Flask 应用主文件
│   └── test/              # 测试文件
│       ├── test_starrocks_connection.py
│       ├── test_oceanbase_connection.py
│       ├── test_execute_sql.py
│       └── test_start_job.py
├── config/                # 配置文件
│   └── flinkomt-template.sql  # FlinkOMT SQL 模板（已弃用，现使用 YAML）
├── docker-compose.yml     # Docker Compose 配置
├── Dockerfile.frontend    # 前端 Docker 镜像
├── Dockerfile.backend     # 后端 Docker 镜像
├── start.sh               # 一键启动脚本
├── package.json           # 前端依赖
├── requirements.txt       # 后端依赖
├── README.md             # 项目说明
└── USAGE.md              # 详细使用指南
```

## 环境要求

### 必需组件

- Node.js 18+
- Python 3.11+
- Flink 1.19.1+
- StarRocks 数据库
- OceanBase 数据库

### FlinkOMT 依赖

确保 Flink 集群已安装以下依赖：

1. **flink-omt-flink_1.18-1.1.jar**
   - FlinkOMT 主程序包，需要放置在 `$FLINK_HOME/lib/` 目录下

2. **flink-connector-mysql-cdc**（可选，用于 CDC）
   ```bash
   wget https://repo1.maven.org/maven2/com/ververica/flink-sql-connector-mysql-cdc/2.4.0/flink-sql-connector-mysql-cdc-2.4.0.jar
   cp flink-sql-connector-mysql-cdc-2.4.0.jar $FLINK_HOME/lib/
   ```

3. **OceanBase JDBC Driver**（可选）
   ```bash
   wget https://repo1.maven.org/maven2/com/oceanbase/oceanbase-client/2.4.3/oceanbase-client-2.4.3.jar
   cp oceanbase-client-2.4.3.jar $FLINK_HOME/lib/
   ```

## 环境变量配置

后端支持以下环境变量：

- `FLINK_HOME`：Flink 安装目录（默认：`/root/flink/flink-1.19.1`）
- `FLINK_REST_URL`：Flink REST API 地址（默认：`http://localhost:8081`）

设置方式：

```bash
export FLINK_HOME=/path/to/flink
export FLINK_REST_URL=http://flink-jobmanager:8081
python backend/app.py
```

## 注意事项

1. **Flink 环境**：确保 Flink 集群已正确启动，并且可以访问 Flink REST API（默认端口 8081）

2. **数据库连接**：确保网络可以访问 StarRocks 和 OceanBase 数据库

3. **FlinkOMT JAR**：确保 Flink 集群已安装 `flink-omt-flink_1.18-1.1.jar`

4. **表结构**：源表和目标表的结构需要兼容，建议字段类型一致

5. **表名配置**：StarRocks 表名支持模式匹配，如 `test[1-2].orders[0-9]` 表示匹配多个表

## 开发和扩展

### 修改前端样式

前端使用 Tailwind CSS，可以直接在 `src/pages/FlinkOMTPage.jsx` 中修改样式类名。

### 修改后端逻辑

后端代码在 `backend/app.py`，可以根据实际需求修改：
- Flink 任务提交逻辑
- 任务状态监控
- 日志收集方式
- SQL 查询功能

### 自定义 FlinkOMT 配置

FlinkOMT 配置通过 YAML 格式生成，配置生成逻辑在 `backend/app.py` 的 `generate_flinkomt_config()` 函数中。

## 常见问题

### Q1: 任务提交失败

**可能原因**：
- Flink 集群未启动
- 未安装 `flink-omt-flink_1.18-1.1.jar`
- 网络无法访问 Flink REST API
- Flink 命令路径不正确

**解决方法**：
1. 检查 Flink 集群状态：`curl http://localhost:8081/overview`
2. 确保 `flink-omt-flink_1.18-1.1.jar` 已放置在 `$FLINK_HOME/lib/` 目录下
3. 检查环境变量 `FLINK_HOME` 和 `FLINK_REST_URL` 是否正确
4. 检查网络连接

### Q2: 连接数据库失败

**可能原因**：
- 数据库配置信息错误
- 网络无法访问数据库
- 数据库服务未启动
- 用户权限不足

**解决方法**：
1. 使用 Web 界面的"测试连接"功能检查连接
2. 检查数据库配置是否正确（特别是 OceanBase 的用户名格式：`username@tenant`）
3. 使用数据库客户端测试连接
4. 检查防火墙设置
5. 确认用户有相应权限

### Q3: 数据没有同步

**可能原因**：
- 源表中没有数据
- 表结构不匹配
- FlinkOMT 配置错误
- 任务未正常运行

**解决方法**：
1. 检查源表是否有数据（使用 SQL 查询工具）
2. 验证表结构是否匹配
3. 查看 Flink 任务日志
4. 检查 FlinkOMT YAML 配置是否正确生成

### Q4: 任务一直运行但没有同步数据

**可能原因**：
- 源表没有新的变更数据
- FlinkOMT 配置错误
- 表名模式匹配不正确

**解决方法**：
1. 在源表中插入或更新一些测试数据
2. 检查表名配置是否正确（支持模式匹配）
3. 查看 Flink 任务日志中的错误信息
4. 检查 FlinkOMT YAML 配置文件

### Q5: SQL 查询失败

**可能原因**：
- SQL 语法错误
- 数据库连接已断开
- 权限不足

**解决方法**：
1. 检查 SQL 语法是否正确
2. 重新测试数据库连接
3. 确认用户有查询权限
4. 查看后端日志获取详细错误信息

## API 接口

后端提供以下 REST API 接口：

- `GET /api/health` - 基础健康检查
- `POST /api/health/starrocks` - 测试 StarRocks 连接
- `POST /api/health/oceanbase` - 测试 OceanBase 连接
- `GET /api/health/flink` - 检查 Flink 集群状态
- `POST /api/start-job` - 启动同步任务
- `GET /api/job-status/<job_id>` - 获取任务状态
- `POST /api/stop-job/<job_id>` - 停止任务
- `POST /api/execute-sql` - 执行 SQL 查询

详细使用说明请参考 `USAGE.md` 文件。

## 许可证

本项目仅供演示和学习使用。

