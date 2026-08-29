## MySQL 慢查询分析与优化步骤

### 定位慢查询
- 开启慢查询日志：`slow_query_log = ON`，`long_query_time = 1`
- `SHOW PROCESSLIST` 看当前正在执行的长 SQL
- 用 `EXPLAIN` 分析执行计划

### EXPLAIN 关键字段
- `type`：访问类型，从好到差 system > const > eq_ref > ref > range > index > **ALL（全表扫描）**
- `key`：实际使用的索引
- `rows`：预估扫描行数，越小越好
- `Extra`：出现 `Using filesort` / `Using temporary` 说明需要优化

### 常见优化手段
1. 加索引：高频 where/order by/group by 字段
2. 覆盖索引：查询列都在索引中，避免回表
3. 避免在索引列上用函数或计算：`WHERE YEAR(create_time)=2024` 会让索引失效，改成范围条件
4. 避免 `%前缀` 模糊查询：`LIKE '%abc'` 走不了索引
5. 分页深翻页优化：`LIMIT 100000,10` 改为基于上一页 id 的游标查询
6. 大表拆分：分库分表 / 冷热分离

> 面试延伸：`select *` 为什么慢？宽列数据无法覆盖索引，必然回表 + 网络传输大。
