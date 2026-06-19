# 贡献指南

感谢你对 J.A.R.V.I.S. Agent 项目的兴趣! 🎉

## 行为准则

本项目遵循 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则。请尊重所有参与者。

## 如何贡献

### 🐛 报告 Bug

1. 在 [Issues](https://github.com/Aqr325/Jarvis/issues) 中搜索是否已有相同问题
2. 如果没有，[创建新 Issue](https://github.com/Aqr325/Jarvis/issues/new?template=bug_report.md)
3. 提供详细的复现步骤、环境信息和截图

### 💡 功能建议

1. 在 [Discussions](https://github.com/Aqr325/Jarvis/discussions) 中先讨论你的想法
2. 确认后创建 Feature Request Issue
3. 描述功能用途和实现思路

### 🔧 提交代码

1. **Fork** 本仓库
2. 创建你的特性分支: `git checkout -b feature/amazing-feature`
3. 编写代码并添加测试
4. 确保所有测试通过: `pytest tests/ -v`
5. 提交你的变更: `git commit -m "feat: add amazing feature"`
6. 推送到分支: `git push origin feature/amazing-feature`
7. 创建 Pull Request

### 📝 代码规范

- **Python**: 遵循 PEP 8
- **提交信息**: 使用 [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` 新功能
  - `fix:` Bug 修复
  - `docs:` 文档更新
  - `test:` 测试相关
  - `refactor:` 代码重构
- **测试**: 新功能必须包含测试

### 📁 项目结构

```
jarvis-agent-app/
├── core/          # 核心引擎 (engine, rate_limiter, websocket, timeout)
├── modules/       # 功能模块 (NLP, 公共API, 自定义LLM)
├── agents/        # 多Agent协作系统
├── plugins/       # 插件系统
├── auth/          # 认证授权
├── schemas/       # Pydantic Schema
├── tests/         # 测试套件
└── public/        # 前端资源
```

### 🧪 运行测试

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=core --cov=modules --cov=schemas
```

### ❓ 有问题?

- 在 [Discussions](https://github.com/Aqr325/Jarvis/discussions) 中提问
- 或在 Issues 中标记为 `question`

---

感谢你的贡献! 🚀
