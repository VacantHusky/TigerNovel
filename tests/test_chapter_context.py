from __future__ import annotations

from pathlib import Path

from app.domain.models import BookMeta
from app.services.chapter_context import ChapterContextService
from app.storage.fs_repo import FileRepository


def _seed_chapter(repo: FileRepository, slug: str, no: int, title: str, summary: str) -> None:
    cdir = repo.create_chapter(slug, no, title=title)
    (cdir / "summary.md").write_text(summary, encoding="utf-8")


def test_dynamic_rolling_summary_and_order(tmp_path: Path) -> None:
    repo = FileRepository(tmp_path)
    repo.create_book(BookMeta(slug="demo", title="Demo"))

    # 造 12 章历史摘要，供第13章上下文使用
    for i in range(1, 13):
        _seed_chapter(repo, "demo", i, f"标题{i}", f"摘要内容{i}" * 30)
        # 同时给上一章定稿文件（仅最后一章需要被读取）
        (repo.chapter_dir("demo", i) / "final.md").write_text(f"定稿{i}", encoding="utf-8")

    svc = ChapterContextService(repo)
    ctx = svc.build_context("demo", 13, chapter_title="新章")

    # 顺序：滚动摘要在前，上一章定稿在后
    assert "全书滚动摘要:" in ctx
    assert "上一章定稿:" in ctx
    assert ctx.index("全书滚动摘要:") < ctx.index("上一章定稿:")

    # 含章节序号与标题
    assert "当前章节: 第013章 新章" in ctx

    # 分层标记存在
    assert "[L1" in ctx
    assert "[L2" in ctx or "[L3" in ctx
