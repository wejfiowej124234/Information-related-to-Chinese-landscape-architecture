from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "园林绿化公司资质文档"

# Only rename non-prefixed “top-level” docs to make Explorer sorting predictable.
RENAME_MAP = {
    "资质证书清单.md": "01-资质证书清单.md",
    "项目类型-资质与名录速查表.md": "02-项目类型-资质与名录速查表.md",
    "图表-资质与项目关系（Mermaid）.md": "03-图表-资质与项目关系（Mermaid）.md",
    "投标材料打包表（证照-附件-核验）.md": "04-投标材料打包表（证照-附件-核验）.md",
    "公司资质规划自述（对外版）.md": "05-公司资质规划自述（对外版）.md",
    "园林绿化公司注册及资质办理指南.md": "06-园林绿化公司注册及资质办理指南.md",
    "证照文档模板（统一结构）.md": "07-证照文档模板（统一结构）.md",
}


def _update_links(text: str, old: str, new: str) -> str:
    # Replace markdown link targets that start with old filename, optionally followed by #fragment.
    # Example: (资质证书清单.md) or (资质证书清单.md#L10)
    pattern = re.compile(r"\((" + re.escape(old) + r")(#[^)]+)?\)")

    def repl(m: re.Match[str]) -> str:
        frag = m.group(2) or ""
        return f"({new}{frag})"

    return pattern.sub(repl, text)


def main() -> int:
    if not DOCS.exists():
        raise SystemExit(f"Docs folder not found: {DOCS}")

    md_files = sorted(DOCS.rglob("*.md"))

    # 1) Update links in all markdown files (before rename, so we can still match old names).
    changed_files: list[Path] = []
    for p in md_files:
        original = p.read_text(encoding="utf-8")
        updated = original
        for old, new in RENAME_MAP.items():
            updated = _update_links(updated, old, new)
        if updated != original:
            p.write_text(updated, encoding="utf-8")
            changed_files.append(p)

    # 2) Rename files.
    for old, new in RENAME_MAP.items():
        src = DOCS / old
        dst = DOCS / new
        if not src.exists():
            continue
        if dst.exists():
            raise SystemExit(f"Destination already exists: {dst}")
        src.rename(dst)

    print("Updated links in:")
    for p in changed_files:
        print("-", p.relative_to(ROOT).as_posix())

    print("Renamed:")
    for old, new in RENAME_MAP.items():
        print(f"- {old} -> {new}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
