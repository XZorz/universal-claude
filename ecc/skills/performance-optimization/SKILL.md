# Performance Optimization Skill

## 目标
识别并解决性能瓶颈

## 优化流程

### 1. 性能分析
```python
# Python profiling
import cProfile
cProfile.run('main()')

# Go profiling  
go tool pprof http://localhost:6060/debug/pprof/
```

### 2. 热点识别
- CPU 密集：算法优化
- IO 密集：缓存/异步
- 内存密集：数据结构优化

### 3. 针对性优化

## 数据库优化

### 索引优化
```sql
-- 查看查询计划
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'xxx';

-- 添加索引
CREATE INDEX idx_users_email ON users(email);
```

### 查询优化
- SELECT 只取需要的字段
- 避免 SELECT *
- 批量操作代替循环

## 缓存策略

### 多级缓存
```
请求 → L1(本地) → L2(Redis) → DB
```

### 缓存失效
- TTL 自动过期
- 主动刷新
- 延迟双删

## 代码优化

### 算法优化
- O(n²) → O(n log n)
- 字典查找代替列表遍历
- 位运算代替算术

### 并发优化
- 多线程/协程
- 异步 IO
- 批量处理

## 验证方法

| 指标 | 目标 | 测量方法 |
|------|------|----------|
| 响应时间 | P99 < 200ms | APM |
| 吞吐量 | QPS > 1000 | 压测 |
| 资源使用 | CPU < 80% | 监控 |

## 适用场景
- 性能退化
- 新功能上线
- 大促前
- 架构升级
