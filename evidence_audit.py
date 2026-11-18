"""Offline, dependency-free audit of repository evidence and draft citations."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse


def audit(evidence, draft):
    errors = []
    warnings = []
    files = evidence.get('files', [])
    valid = {f['url']: f for f in files if isinstance(f, dict) and isinstance(f.get('content'), str) and f.get('url')}
    if not valid:
        errors.append('No readable evidence files')
    if valid and not any(Path(f.get('path', '')).suffix.lower() in {'.py', '.js', '.ts', '.go', '.rs', '.java', '.tf', '.sh'} for f in valid.values()):
        warnings.append('No implementation code in evidence; claims about implementation cannot be verified')
    if evidence.get('truncated_tree'):
        warnings.append('GitHub tree was truncated; source coverage is incomplete')
    if any('error' in f for f in files):
        warnings.append('Some source files could not be fetched')
    repo = evidence.get('repository', '')
    if not repo.startswith('https://github.com/'):
        errors.append('Invalid repository URL')
    for url in re.findall(r'https://github\.com/[^\s)\]>]+', draft):
        url = url.rstrip('.,;')
        if url == repo:
            continue
        if url not in valid:
            warnings.append(f'Unverified GitHub citation: {url}')
    for marker in ('<!-- README とコードを確認して執筆 -->', '<!-- 実コードから確認できる構成だけを図示 -->', '<!-- 根拠となるファイルへのリンクを添える -->'):
        if marker in draft:
            warnings.append('Draft contains unfilled template sections')
            break
    return {'ok': not errors, 'errors': errors, 'warnings': sorted(set(warnings)), 'verified_files': len(valid), 'note': 'Citation URL validation only; semantic factual accuracy requires human review.'}


def main():
    p = argparse.ArgumentParser(description='Audit a Qiita draft against evidence.json')
    p.add_argument('evidence', type=Path)
    p.add_argument('draft', type=Path)
    p.add_argument('--report', type=Path)
    a = p.parse_args()
    result = audit(json.loads(a.evidence.read_text(encoding='utf-8')), a.draft.read_text(encoding='utf-8'))
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if a.report:
        a.report.write_text(output + '\n', encoding='utf-8')
    print(output)
    raise SystemExit(0 if result['ok'] else 1)

if __name__ == '__main__':
    main()
