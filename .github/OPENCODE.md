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

当前配置使用 OpenCode Zen 的 `minimax-m2.5-free` 免费模型。

#### 必需配置

**GitHub Secrets 配置** （必需）
在仓库设置中添加以下 Secret：

1. 进入仓库 Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加以下变量：

| Secret 名称 | 说明 | 获取方式 |
|-----------|------|--------|
| `OPENCODE_ZEN_API_KEY` | OpenCode Zen API Key | https://opencode.ai/auth 注册后复制 |

**获取 API Key 步骤：**
1. 前往 [OpenCode Zen](https://opencode.ai/auth) 注册账户（免费）
2. 登录后在设置中复制 API Key
3. 无需信用卡或付款
4. 在 GitHub 中配置为 `OPENCODE_ZEN_API_KEY` Secret

#### 可选：更换模型

如果要使用其他模型，修改 workflow 文件中的 `model` 字段：

- `opencode/minimax-m2.5-free` — **当前** ⭐ 完全免费，适合编码
- `opencode/gpt-5-nano` — 完全免费，轻量级
- `opencode/big-pickle` — 完全免费，隐秘模型
- `opencode/qwen3.6-plus-free` — 完全免费，高性能

#### 可选：使用自己的 API Key

如果要使用其他提供商（OpenAI、Anthropic 等）：
1. 在 GitHub Secrets 中添加 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`
2. 更新 workflow 文件中的 `env` 部分
3. 修改 `model` 字段为对应提供商的模型

### 成本

- **Zen 免费模型** ($0/月)：完全免费，只需注册 OpenCode Zen 账户
- **付费 Zen 模型** (可选)：按使用量计费，起价 $0.02 - $30 每百万 token
- **其他提供商**：取决于具体提供商

### 模型推荐

| 模型 | 成本 | 特点 | 当前使用 |
|------|------|------|---------|
| `minimax-m2.5-free` | 免费 | 平衡性能，最适合编码 | ⭐ **是** |
| `gpt-5-nano` | 免费 | 轻量级，快速 | 否 |
| `big-pickle` | 免费 | 实验性 | 否 |
| `qwen3.6-plus-free` | 免费 | 高性能 | 否 |

### 配置 GitHub 分支保护规则

此项目已启用 OpenCode 自动审查。为了不被人工 review 要求阻挡，需要调整分支保护规则。

**目标：** 允许在 OpenCode 批准后合并，不强制要求具有 write 权限的人工 review。

**步骤：**

1. 进入仓库 **Settings** → **Branches**
2. 找到 `dev` 分支的保护规则，点击编辑（或创建新规则）
3. 配置如下：

| 设置项 | 推荐配置 | 说明 |
|-------|--------|------|
| **Require a pull request before merging** | ✅ 开启 | 仍然要求 PR，确保有审查记录 |
| **Require approvals** | ❌ **关闭** | **关键** - 取消需要人工批准的要求 |
| **Require status checks to pass before merging** | ✅ 开启 | CI 检查必须通过（lint, test, build） |
| **Require branches to be up to date before merging** | ✅ 推荐 | 合并前同步最新代码 |
| **Include administrators** | ✅ 可选 | 规则对 admin 也适用 |

4. 点击 "Save changes"

### 合并流程

```
1. 创建 PR
   ↓
2. 自动检查运行
   - Lint, Test, Build 检查
   - OpenCode 自动审查 (5-10 分钟)
   ↓
3. 所有检查通过
   ↓
4. 手动点击 "Merge pull request" 合并
   ↓
5. 代码合并到 dev 分支
```

### OpenCode 的作用

- ✅ 自动审查每个 PR 的代码质量、测试、安全性等
- ✅ 在评论中给出明确的建议（可合并/需改进）
- ✅ 记录审查意见，便于追溯
- ⚠️ **不强制阻止合并** - 最终合并决定由你手动执行

### 何时手动合并

当满足以下条件时，可以手动合并：
1. ✅ 所有 CI 检查通过（lint, test, build）
2. ✅ OpenCode 的评论中提到 `✅ APPROVED FOR MERGE` 或代码质量可接受
3. ✅ (可选) 有至少 1 个其他人的赞同评论

---

**原问题：** "Review required - At least 1 approving review is required"

**解决方案：** 在分支保护规则中关闭 "Require approvals"，这样 OpenCode 的审查记录就足够了，不必等待真人批准。

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
