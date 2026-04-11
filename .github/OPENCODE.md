## OpenCode GitHub Actions 集成

此项目已配置 OpenCode 自动化工作流，用于自动分析 Issue 和 PR。

### 工作流说明

#### 1. **Issue 自动分析** (`opencode-issue.yml`)
- **触发**: 创建新 Issue 时自动触发
- **功能**: 自动梳理实现方法，提供：
  - 问题总结
  - 根因分析
  - 实现方案
  - 相关代码文件
  - 风险评估

#### 2. **PR 自动审查** (`opencode-review.yml`)
- **触发**: PR 打开、更新或重新打开时自动触发
- **功能**: 自动进行代码审查，检查：
  - 代码质量
  - 测试覆盖率
  - 文档更新
  - 性能问题
  - 安全问题

#### 3. **评论命令** (`opencode-comment.yml`)
- **触发**: 在 Issue/PR 评论中使用 `/oc` 或 `/opencode`
- **用法**:
  ```
  /opencode 帮我分析这个问题
  /oc review this code
  /opencode fix this issue
  ```

### 配置

当前配置使用 OpenCode Zen 的 `gpt-5-nano` 免费模型。

#### 选项

**方案 1：使用 OpenCode Zen（推荐）**
- 前往 [OpenCode Zen](https://opencode.ai/auth) 注册账户（免费）
- 无需信用卡，即可使用多个免费模型
- 可选模型：
  - `opencode/gpt-5-nano` — 完全免费，性能好
  - `opencode/minimax-m2.5-free` — 完全免费，适合编码
  - `opencode/big-pickle` — 完全免费，隐秘模型

**方案 2：使用自己的 API Key**
- 如果要使用其他提供商（OpenAI、Anthropic 等），在 GitHub Secrets 中配置：
  - `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`
- 更新 workflow 文件中的 `env` 部分

### 成本

- **Zen 免费模型** ($0/月)：完全免费，无需付款
- **付费 Zen 模型** (可选)：按使用量计费，起价 $0.02 - $30 每百万 token
- **其他提供商**：取决于具体提供商

### 模型推荐

| 模型 | 成本 | 特点 | 适用场景 |
|------|------|------|---------|
| `gpt-5-nano` | 免费 | 轻量级，快速 | 快速分析、评论 |
| `minimax-m2.5-free` | 免费 | 平衡性能 | 一般分析和审查 |
| `big-pickle` | 免费 | 实验性 | 测试和反馈 |
| `qwen3.6-plus-free` | 免费 | 高性能 | 复杂分析 |

### 故障排除

**错误：`ProviderModelNotFoundError`**
- 检查模型名称格式是否为 `opencode/<model-id>`
- 确保 Zen 账户已验证

**工作流不运行**
- 检查 GitHub Actions 是否已启用
- 确保工作流文件语法正确（`yaml` 格式）
- 查看 Actions 标签页的运行日志

**需要加速**
- 可以根据优先级调整或减少触发事件
- 例如，仅在 draft PR 发布时运行审查

### 进一步配置

#### 自定义 Prompt
编辑 `opencode-issue.yml` 或 `opencode-review.yml` 中的 `prompt` 字段以自定义分析内容。

#### 禁用特定工作流
注释掉或删除不需要的 workflow 文件。

#### 调整权限
根据需要修改 `permissions` 部分，最小化权限需求。

### 更多信息

- [OpenCode 文档](https://opencode.ai/docs/zh-cn)
- [OpenCode Zen](https://opencode.ai/docs/zh-cn/zen)
- [GitHub 集成指南](https://opencode.ai/docs/zh-cn/github)
