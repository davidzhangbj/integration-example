# FlinkOMT Demo - StarRocks to OceanBase

这是一个 Web 界面的 FlinkOMT 演示项目，可以帮助用户快速了解和使用 FlinkOMT 进行 StarRocks 到 OceanBase 的数据同步。

## 功能特性

- 🎨 现代化的 Web 界面，操作简单直观
- 🔄 实时任务监控和日志查看
- 📝 图形化配置数据库连接信息
- 🚀 一键启动/停止同步任务
- 📊 实时显示任务运行状态
- 🔍 **SQL 查询工具**：支持查询源数据库和目标数据库的表结构和表数据
- ⚡ **快速查询**：一键查看表结构和表数据
- 📋 **自定义 SQL**：支持执行任意 SQL 查询语句

## 技术栈

- **前端**: React + Vite + Tailwind CSS
- **后端**: Flask + Python
- **数据同步**: FlinkOMT (Apache Flink)

## 快速开始

### 方式一：使用 Docker Compose（推荐）

1. **克隆或下载项目**
```bash
cd integration-example
```

2. **启动所有服务**
```bash
docker-compose up -d
```

3. **访问 Web 界面**
打开浏览器访问：http://localhost:3000

### 方式二：本地开发

#### 前置要求

- Node.js 18+ 
- Python 3.11+
- Flink 1.17+（已安装并配置好）

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
cd backend
python app.py
```

5. **访问应用**
- 前端：http://localhost:3000
- 后端 API：http://localhost:5000

## 使用说明

### 1. 配置数据库连接

在 Web 界面中填写：

**StarRocks 源数据库**：
- 主机地址
- 端口（默认 9030）
- 用户名
- 密码
- 数据库名
- 表名

**OceanBase 目标数据库**：
- 主机地址
- 端口（默认 2883）
- 用户名（格式：username@tenant）
- 密码
- 数据库名
- 表名

**FlinkOMT 高级配置**：
- 检查点间隔（毫秒）
- 并行度

### 2. 启动同步任务

点击"启动同步任务"按钮，系统将：
1. 根据配置生成 FlinkOMT SQL
2. 提交到 Flink 集群执行
3. 实时显示任务状态和日志

### 3. 监控任务

在任务运行过程中，可以：
- 查看实时日志输出
- 查看任务运行状态
- 停止正在运行的任务

## 项目结构

```
integration-example/
├── src/                    # 前端源代码
│   ├── App.jsx            # 主应用组件
│   ├── main.jsx           # 入口文件
│   └── index.css          # 样式文件
├── backend/               # 后端源代码
│   └── app.py             # Flask 应用
├── config/                # 配置文件
│   └── flinkomt-template.sql  # FlinkOMT SQL 模板
├── docker-compose.yml     # Docker Compose 配置
├── Dockerfile.frontend    # 前端 Docker 镜像
├── Dockerfile.backend     # 后端 Docker 镜像
├── package.json           # 前端依赖
├── requirements.txt       # 后端依赖
└── README.md             # 项目说明
```

## 注意事项

1. **Flink 环境**：确保 Flink 集群已正确启动，并且可以访问 Flink REST API（默认端口 8081）

2. **数据库连接**：确保网络可以访问 StarRocks 和 OceanBase 数据库

3. **FlinkOMT Connector**：确保 Flink 集群已安装必要的 Connector：
   - `flink-connector-mysql-cdc`
   - `flink-connector-oceanbase`（或兼容的 JDBC connector）

4. **表结构**：源表和目标表的结构需要兼容，建议字段类型一致

## 开发和扩展

### 修改前端样式

前端使用 Tailwind CSS，可以直接在 `src/App.jsx` 中修改样式类名。

### 修改后端逻辑

后端代码在 `backend/app.py`，可以根据实际需求修改：
- Flink 任务提交逻辑
- 任务状态监控
- 日志收集方式

### 自定义 FlinkOMT SQL

模板文件在 `config/flinkomt-template.sql`，可以根据实际需求调整 SQL 语句。

## 常见问题

**Q: 任务提交失败？**
A: 检查 Flink 集群是否正常运行，以及是否安装了必要的 Connector。

**Q: 连接数据库失败？**
A: 检查数据库配置信息是否正确，网络是否可达。

**Q: 数据没有同步？**
A: 检查源表中是否有数据，表结构是否匹配。

## 许可证

本项目仅供演示和学习使用。

