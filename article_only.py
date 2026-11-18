import argparse
import json
from pathlib import Path

from article_validator import validate, report_markdown


def run(article):
    # No repository context: inspect Markdown-related findings only.
    result = validate(article, {})

    # Source-dependent checks cannot be evaluated in article-only mode.
    findings = [
        f for f in result["findings"]
        if not f["rule"].startswith(("REF", "PY"))
    ]

    summary = {
        level: sum(f["severity"] == level for f in findings)
        for level in ("error", "warning", "info")
    }

    result["findings"] = findings
    result["summary"] = summary
    result["ok"] = summary["error"] == 0
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Article Kit Markdown-only inspection"
    )
    parser.add_argument("--article", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("article_only_report"))
    args = parser.parse_args()

    article = args.article.read_text(encoding="utf-8-sig")
    result = run(article)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    (args.out / "report.md").write_text(
        report_markdown(result), encoding="utf-8"
    )

    print("Article-only QA:", result["summary"])
    print("Report:", args.out)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
