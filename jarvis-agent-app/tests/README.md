# J.A.R.V.I.S. Agent 测试套件

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ -v --cov=core --cov=modules --cov=schemas --cov-report=html

# 只运行特定测试文件
pytest tests/test_server.py -v

# 只运行特定测试类
pytest tests/test_server.py::TestChatEndpoint -v

# 跳过慢速测试
pytest tests/ -v -m "not slow"

# 运行集成测试
pytest tests/ -v -m "integration"
```

## 测试结构

- `test_server.py` - API 端点测试
- `test_core.py` - 核心引擎和中间件测试
- `test_modules.py` - 业务模块测试
- `test_schemas.py` - Schema 验证测试
- `conftest.py` - 共享 fixtures 和配置

## 测试覆盖率目标

- 总体覆盖率: 80%+
- 核心模块覆盖率: 90%+
- Schema 验证覆盖率: 100%
