from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "园林绿化公司资质文档"

# Group docs into typed folders under DOCS.
MOVE_MAP: dict[str, Path] = {
    # Entry / index / meta
    "00-新手入口（按证照分类）.md": Path("00-入口与索引/00-新手入口（按证照分类）.md"),
    "00-文件目录（按使用顺序排序）.md": Path("00-入口与索引/00-文件目录（按使用顺序排序）.md"),
    "01-资质证书清单.md": Path("00-入口与索引/01-资质证书清单.md"),
    "02-项目类型-资质与名录速查表.md": Path("00-入口与索引/02-项目类型-资质与名录速查表.md"),
    "03-图表-资质与项目关系（Mermaid）.md": Path("00-入口与索引/03-图表-资质与项目关系（Mermaid）.md"),
    "04-投标材料打包表（证照-附件-核验）.md": Path("00-入口与索引/04-投标材料打包表（证照-附件-核验）.md"),
    "05-公司资质规划自述（对外版）.md": Path("00-入口与索引/05-公司资质规划自述（对外版）.md"),
    "06-园林绿化公司注册及资质办理指南.md": Path("00-入口与索引/06-园林绿化公司注册及资质办理指南.md"),
    "07-证照文档模板（统一结构）.md": Path("00-入口与索引/07-证照文档模板（统一结构）.md"),

    # Certificate single-docs
    "1-营业执照信息.md": Path("10-证照（单证）/1-营业执照信息.md"),
    "3-安全生产许可证.md": Path("10-证照（单证）/3-安全生产许可证.md"),
    "4-三体系管理体系认证证书.md": Path("10-证照（单证）/4-三体系管理体系认证证书.md"),
    "5-建筑工程施工服务企业资质证书（能力等级评价）.md": Path("10-证照（单证）/5-建筑工程施工服务企业资质证书（能力等级评价）.md"),
    "6-开户许可证（基本存款账户）.md": Path("10-证照（单证）/6-开户许可证（基本存款账户）.md"),
    "7-企业信用与资信AAA（冠捷时速）.md": Path("10-证照（单证）/7-企业信用与资信AAA（冠捷时速）.md"),
    "8-垃圾消纳企业服务资质证书（一级）.md": Path("10-证照（单证）/8-垃圾消纳企业服务资质证书（一级）.md"),

    # Construction qualification topic
    "2-建筑业企业资质证书.md": Path("20-施工资质专题/2-建筑业企业资质证书.md"),
    "2-1-施工资质证书信息（两本资质证书）.md": Path("20-施工资质专题/2-1-施工资质证书信息（两本资质证书）.md"),
    "2-2-施工资质办理流程（怎么拿证）.md": Path("20-施工资质专题/2-2-施工资质办理流程（怎么拿证）.md"),
    "2-3-北京口径-资质标准硬指标全量对照.md": Path("20-施工资质专题/2-3-北京口径-资质标准硬指标全量对照.md"),
    "2-4-北京口径-社保口径（百问百答摘要）.md": Path("20-施工资质专题/2-4-北京口径-社保口径（百问百答摘要）.md"),
}

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def _is_url(target: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target))


def _future_path_for_md(md_path: Path) -> Path:
    # Resolve the future location under DOCS.
    rel = md_path.relative_to(DOCS)
    # If file is part of the move plan, always use the planned destination.
    # This works both before and after moving.
    basename = md_path.name
    return MOVE_MAP.get(basename, rel)


def _compute_relative_link(src_future: Path, dst_future: Path) -> str:
    # Both are relative to DOCS.
    src_dir = (DOCS / src_future).parent
    dst = DOCS / dst_future
    rel = os.path.relpath(dst, start=src_dir)
    return Path(rel).as_posix()


def _rewrite_links(text: str, src_future: Path) -> str:
    def repl(m: re.Match[str]) -> str:
        label = m.group(1)
        target = m.group(2).strip()

        if not target or target.startswith("#") or _is_url(target):
            return m.group(0)

        # Split fragment
        if "#" in target:
            target_file, frag = target.split("#", 1)
            frag = "#" + frag
        else:
            target_file, frag = target, ""

        # Only rewrite markdown-to-markdown links
        if not target_file.endswith(".md"):
            return m.group(0)

        base = Path(target_file).name
        if base not in MOVE_MAP:
            return m.group(0)

        dst_future = MOVE_MAP[base]
        new_target = _compute_relative_link(src_future, dst_future)
        return f"[{label}]({new_target}{frag})"

    return LINK_RE.sub(repl, text)


def main() -> int:
    if not DOCS.exists():
        raise SystemExit(f"Docs folder not found: {DOCS}")

    # Collect md files (current state before moving)
    md_files = sorted(DOCS.rglob("*.md"))

    # 1) Update links based on future locations
    changed: list[Path] = []
    for p in md_files:
        src_future = _future_path_for_md(p)
        original = p.read_text(encoding="utf-8")
        updated = _rewrite_links(original, src_future)
        if updated != original:
            p.write_text(updated, encoding="utf-8")
            changed.append(p)

    # 2) Ensure destination dirs exist
    for dst_rel in MOVE_MAP.values():
        (DOCS / dst_rel).parent.mkdir(parents=True, exist_ok=True)

    # 3) Move files
    moved: list[tuple[Path, Path]] = []
    for name, dst_rel in MOVE_MAP.items():
        src = DOCS / name
        dst = DOCS / dst_rel
        if not src.exists():
            # may already be moved
            continue
        if dst.exists():
            raise SystemExit(f"Destination already exists: {dst}")
        src.rename(dst)
        moved.append((src, dst))

    print("Updated links in:")
    for p in changed:
        print("-", p.relative_to(ROOT).as_posix())

    print("Moved files:")
    for src, dst in moved:
        print("-", src.relative_to(ROOT).as_posix(), "->", dst.relative_to(ROOT).as_posix())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
