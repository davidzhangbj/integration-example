-- FlinkOMT 配置模板：StarRocks -> OceanBase
-- 这个文件是示例模板，实际运行时会根据用户配置动态生成

SET 'execution.checkpointing.interval' = '60000ms';
SET 'execution.checkpointing.mode' = 'EXACTLY_ONCE';
SET 'parallelism.default' = '1';

-- 创建 StarRocks Source Table
CREATE TABLE starrocks_source (
    id BIGINT,
    name STRING,
    value DOUBLE,
    update_time TIMESTAMP(3),
    PRIMARY KEY (id) NOT ENFORCED
) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = '${starrocks.host}',
    'port' = '${starrocks.port}',
    'username' = '${starrocks.username}',
    'password' = '${starrocks.password}',
    'database-name' = '${starrocks.database}',
    'table-name' = '${starrocks.table}',
    'server-id' = '5400-5404',
    'scan.startup.mode' = 'latest-offset'
);

-- 创建 OceanBase Sink Table
CREATE TABLE oceanbase_sink (
    id BIGINT,
    name STRING,
    value DOUBLE,
    update_time TIMESTAMP(3),
    PRIMARY KEY (id) NOT ENFORCED
) WITH (
    'connector' = 'oceanbase',
    'url' = 'jdbc:oceanbase://${oceanbase.host}:${oceanbase.port}/${oceanbase.database}',
    'table-name' = '${oceanbase.table}',
    'username' = '${oceanbase.username}',
    'password' = '${oceanbase.password}',
    'driver-class-name' = 'com.oceanbase.jdbc.Driver'
);

-- 执行数据同步
INSERT INTO oceanbase_sink
SELECT * FROM starrocks_source;


