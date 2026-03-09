# TigerNovel

一个可持续开发的 AI 小说自动化工程骨架：

- 使用 OpenAI 官方库，模型可配置
- 多 Agent（每个 Agent 独立配置文件）
- 支持 **agents 默认配置 + 单个 agent 覆盖**
- 一本小说一个目录，章节独立目录
- 草稿 / 评审 / 定稿全量留痕
- 支持章节连贯的上下文压缩与摘要
- 包含基础测试

## 快速开始

```bash
cd TigerNovel
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .[dev]
```

设置环境变量：

```bash
set TIGER_NOVEL_API_KEY=your_key_here
set TIGER_NOVEL_BASE_URL=https://your-base-url  # 可选，不设则用官方默认
```

## Agent 默认配置与覆盖

- 全局默认：`agents/defaults.yaml`
- 单个 agent：`agents/*.yaml`

优先级：**单个 agent 显式配置 > defaults.yaml**

例如你可以统一设置：

```yaml
# agents/defaults.yaml
model: gpt-5.3-codex
temperature: 0.7
max_output_tokens: 2000
```

然后只在某个 agent 里覆盖：

```yaml
# agents/writer.yaml
name: writer
temperature: 0.85
max_output_tokens: 2800
system_prompt_file: prompts/writer_system.md
```

## 常用命令

```bash
# 新建小说（可选字段可以留空）
tigernovel create-book --slug my-book --title "我的小说" --synopsis "一个普通人逆袭"

# 生成章节（可带章节标题）
tigernovel write-chapter --slug my-book --chapter 1 --chapter-title "雨夜来客"
```

## 目录约定

```txt
novels/
  <book_slug>/
    book.yaml
    memory/rolling_summary.md
    chapters/
      001/
        chapter.yaml
        drafts/
        reviews/
        final.md
        summary.md
```

## Agent 配置

在 `agents/*.yaml` 中调整参数和提示词文件路径，新增 Agent 可直接新增配置文件并接入管线。
