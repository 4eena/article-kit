"""Offline verification of Article Kit ZIP artifacts (no GitHub access)."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

REQUIRED = {"START_HERE.md", "repository_context.md", "manifest.json"}

def verify(path):
    path = Path(path)
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or set(names) != REQUIRED:
            raise ValueError("ZIP内のファイル構成が不正です")
        if z.testzip() is not None:
            raise ValueError("ZIPが破損しています")
        context = z.read("repository_context.md")
        if len(context) > 2_000_000:
            raise ValueError("資料が2MBを超えています")
        manifest = json.loads(z.read("manifest.json"))
        if manifest.get("context_bytes") != len(context):
            raise ValueError("資料サイズがmanifestと一致しません")
        if manifest.get("context_sha256") != hashlib.sha256(context).hexdigest():
            raise ValueError("資料のSHA256がmanifestと一致しません")
        if manifest.get("style") not in ("technical", "story"):
            raise ValueError("記事スタイルが不正です")
        if manifest.get("target") not in ("qiita", "zenn", "generic"):
            raise ValueError("投稿先が不正です")
        if manifest.get("source") not in ("provided_context", "repomix_remote", "repomix_cli"):
            raise ValueError("取得元が不正です")
        if not z.read("START_HERE.md").strip() or not context.strip():
            raise ValueError("資料または執筆指示が空です")
        return manifest

def main():
    p = argparse.ArgumentParser(description="Article Kit ZIP整合性チェック")
    p.add_argument("zip_file", type=Path)
    args = p.parse_args()
    try:
        m = verify(args.zip_file)
    except (ValueError, OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as exc:
        print("NG:", exc)
        return 1
    print("OK:", m["repository"], m["source"], m["style"], m["context_bytes"], "bytes")
    print("注意: これはZIP内部の整合性確認であり、GitHub上の最新状態やコードの安全性の証明ではありません。")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
