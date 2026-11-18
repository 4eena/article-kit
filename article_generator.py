"""Evidence-only Markdown generator; no AI and no invented behavior."""
import argparse
import ast
import json
from pathlib import Path



def describe_verified_patterns(tree):
    """Report syntax only, without assuming runtime behavior."""
    nodes = list(ast.walk(tree))
    patterns = []
    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'urlopen' for n in nodes):
        patterns.append(('HTTP通信', '`urlopen(...)` の呼び出しがあります。通信成功は未検証です。'))
    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'write_text' for n in nodes):
        patterns.append(('ファイル書き込み', '`write_text(...)` の呼び出しがあります。保存成功は未検証です。'))
    if any(isinstance(n, ast.Compare) and any(isinstance(op, ast.GtE) for op in n.ops) and any(isinstance(v, ast.Constant) and type(v.value) is int and v.value == 2 for v in n.comparators) for n in nodes):
        patterns.append(('閾値比較', '`>= 2` の条件判定があります。設計意図は断定しません。'))
    return patterns

def generate(data):
    repo = data['repository']
    files = [f for f in data['files'] if isinstance(f.get('content'), str) and f.get('url')]
    if not files:
        raise ValueError('No readable evidence files')
    name = repo.rstrip('/').split('/')[-1]
    lines = [f'# {name} のソースコードを読み解く', '', '> GitHubから取得したファイルに基づく自動生成記事です。動作確認は未実施です。', '', '## 対象', '', f'- リポジトリ: {repo}', f'- ブランチ: `{data.get("branch", "unknown")}`', '', '## 確認できたファイル', '']
    for f in files:
        lines.append(f'- [`{f["path"]}`]({f["url"]})')
    code_files = [f for f in files if Path(f['path']).suffix.lower() in {'.py', '.js', '.ts', '.go', '.rs', '.java', '.tf', '.sh'}]
    if not code_files:
        lines.extend(['', '> **資料不足:** 取得できた資料に実装コードがありません。READMEなどの説明だけでは設計・機能・動作を検証できないため、技術解説は保留します。', ''])
    lines.extend(['', '## コードから確認できる構造', ''])
    for f in files:
        if not f['path'].endswith('.py'):
            continue
        try:
            tree = ast.parse(f['content'])
        except SyntaxError:
            lines.append(f'- [`{f["path"]}`]({f["url"]}): Python構文解析不可（ファイルが途中までの可能性）')
            continue
        functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if not functions:
            continue
        lines.extend([f'### `{f["path"]}`', '', f'根拠: {f["url"]}', '', 'ソース内で定義されている関数:', ''])
        for n in functions:
            lines.append(f'- `{n.name}()`（{n.lineno}行目）')
        lines.append('')
        patterns = describe_verified_patterns(tree)
        if patterns:
            lines.extend(['コード上で確認できる処理:', ''])
            for label, detail in patterns:
                lines.append(f'- **{label}**: {detail} [根拠]({f["url"]})')
            lines.append('')
    lines.extend(['## 動作確認', '', 'この生成処理ではプログラムを実行していません。実運用・通知の成功は未検証です。', '', '## 注意点', '', '本記事は取得できたファイルだけを対象にしています。関数名から動作を推測した説明は含めていません。', ''])
    if data.get('truncated_tree') or any('error' in f for f in data['files']):
        lines.extend(['一部ファイルの取得に失敗、またはファイル一覧が省略された可能性があります。', ''])
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('evidence', type=Path)
    p.add_argument('--out', type=Path, default=Path('qiita_article.md'))
    a = p.parse_args()
    a.out.write_text(generate(json.loads(a.evidence.read_text(encoding='utf-8'))), encoding='utf-8')
    print(a.out)


if __name__ == '__main__':
    main()
