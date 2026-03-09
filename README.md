# TigerNovel

一个可持续开发的 AI 小说自动化工程骨架：

- 使用 OpenAI 官方库，模型可配置
- 多 Agent（每个 Agent 独立配置文件）
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
set OPENAI_API_KEY=your_key_here
```

## 常用命令

```bash
# 新建小说（可选字段可以留空）
tigernovel create-book --slug my-book --title "我的小说" --synopsis "一个普通人逆袭"

# 生成章节（可带本章目标）
tigernovel write-chapter --slug my-book --chapter 1 --brief "主角初登场并埋下主线伏笔"
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

在 `agents/*.yaml` 中调整模型、温度、提示词。新增 Agent 可直接新增配置文件并接入管线。
