---
inclusion: auto
description: Systematic debugging methodology and common patterns for issue resolution.
---

# Debugging Methodology

## 系统化调试流程

### 1. 重现问题
- 找到最小复现步骤
- 记录环境上下文
- 隔离变量

### 2. 定位根因
- 二分查找
- 日志追踪
- 断点调试

### 3. 修复验证
- 单元测试
- 集成测试
- 回归测试

## 常用技巧

### 日志调试
```python
# 结构化日志
logger.info("User action", extra={
    "user_id": user_id,
    "action": "purchase",
    "amount": amount
})
```

### 断点调试
- IDE 断点
- 条件断点
- 日志断点

### 远程调试
- debugpy (Python)
- Delve (Go)
- lldb (C++)

## 常见问题模式

| 症状 | 可能原因 |
|------|----------|
| 内存持续增长 | 内存泄漏 |
| 响应越来越慢 | 性能退化 |
| 偶发失败 | 竞态条件 |
| 间歇性错误 | 超时/重试 |

## 工具推荐

- Python: pdb, ipdb, debugpy
- JavaScript: Chrome DevTools
- Go: Delve, pprof
- 系统: strace, lsof, netstat
