# Code Refactoring Skill

## 目标
改善代码质量而不改变外部行为

## 重构时机

### 需要重构的信号
- 重复代码超过 3 处
- 函数超过 50 行
- 类超过 500 行
- 圈复杂度 > 10
- 难以添加新功能

### 重构前准备
1. 有测试覆盖
2. 理解现有逻辑
3. 备份当前版本

## 核心技巧

### 提取函数
```python
# Before
def process():
    do_step_one()
    do_step_two()
    do_step_three()

# After
def process():
    step_one()
    step_two()
    step_three()
```

### 提取类
```python
# Before: 巨型类
class UserManager:
    def authenticate(self): ...
    def send_email(self): ...
    def generate_report(self): ...

# After: 职责分离
class AuthService: ...
class EmailService: ...
class ReportGenerator: ...
```

### 简化条件
```python
# Before
if is_valid and (user_type == 'admin' or user_type == 'super'):
    pass

# After
if is_valid and is_privileged:
    pass
```

## 重构安全检查

- [ ] 所有测试通过
- [ ] 代码格式化
- [ ] 静态检查通过
- [ ] 手动验证功能

## 适用场景
- 代码 review 后
- 添加功能前
- Bug 修复时
- 技术债务清理
