from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "园林绿化公司资质文档"

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _normalize_target(src: Path, target: str) -> Path | None:
    target = target.strip()
    if not target.lower().endswith(".md"):
        return None
    if "://" in target or target.startswith("mailto:"):
        return None

    target = target.split("#", 1)[0]
    if not target:
        return None

    # Ignore absolute/UNC paths.
    if re.match(r"^[A-Za-z]:\\", target) or target.startswith("\\"):
        return None

    return (src.parent / target).resolve()


def main() -> int:
    if not ROOT.exists():
        print(f"Not found: {ROOT}")
        return 2

    md_files = sorted(ROOT.rglob("*.md"))
    root_resolved = ROOT.resolve()

    missing: list[tuple[str, int, str]] = []

    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for m in LINK_RE.finditer(text):
            raw_target = m.group(1)
            target_path = _normalize_target(md, raw_target)
            if target_path is None:
                continue

            try:
                target_path.relative_to(root_resolved)
            except Exception:
                # Only validate links within this doc folder.
                continue

            if not target_path.exists():
                line = text.count("\n", 0, m.start()) + 1
                missing.append((str(md.relative_to(root_resolved)), line, raw_target))

    print(f"Scanned {len(md_files)} markdown files under: {ROOT}")
    if not missing:
        print("OK: No missing internal .md links found.")
        return 0

    print("Missing internal .md links:")
    for path, line, raw in missing:
        print(f"- {path}:{line} -> {raw}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
