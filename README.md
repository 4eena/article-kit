# GitHub Article Kit v0.41 (Release Candidate)

公開GitHubリポジトリのコードをRepomixで収集し、ChatGPTなどに渡す記事執筆用ZIPを作成します。**記事本文の自動生成はしません。** AI APIキーや有料APIは不要です。

## Windowsでの使い方

1. Python 3.9以上とNode.js（npm/npxを含む）をインストール。
2. ZIPを展開し、`start_windows.bat` をダブルクリック。
3. ブラウザで `http://127.0.0.1:8765/` を開く（自動で開く場合もあります）。
4. 公開GitHubリポジトリのURLを貼る。
5. 「技術解説型」（初期値）または「開発ストーリー型」を選択し、Qiita/Zenn/一般ブログを指定。
6. 「記事キットを作成」を押し、ZIPを保存。
7. ZIPの `START_HERE.md` と `repository_context.md` をAIに渡して記事本文を作成する。

## 注意事項

- ローカル専用。インターネットに公開したり、ポート転送したりしないでください。
- GitHub URL取得は通信を伴い、初回はnpxがRepomixを取得するため時間がかかることがあります。
- Repomixは既定で `repomix@1.19.0` を指定します。初回実行時はnpmからの取得が必要です。 CLIで `--repomix` にインストール済み実行ファイルを指定した場合は、その実行ファイルを使用します。
- プライベートリポジトリの利用、秘密情報の完全検出、リポジトリ全体の網羅性、記事の正確性は保証しません。
- `manifest.json` の `repository_identity_verified` はリモート取得経路を通ったことを示す実装上の値であり、Gitコミットの暗号学的検証ではありません。
- Windows実機でpsf/requestsのオンライン取得と両スタイルのZIP生成を確認済みです。Repomix 1.19.0の起動と、固定版指定のCLI取得・ZIP整合性検査に成功しました。

## 開発者向け

`python -m unittest discover -p "test_*.py" -q`

CLIで既存のRepomix資料を使う例:

`python repomix_bridge.py https://github.com/owner/repo --context repomix-output.md --style technical --target qiita --out article_kit.zip`

`technical` は要点重視、`story` は背景・設計判断も重視します。どちらも根拠のない制作経緯を創作しないよう指示します。

## 公開前セルフチェック

Windows PowerShellで `py -3 preflight.py` を実行できます。依存ソフトの検出と既存の自動テストをまとめて実行します（ネットワーク試験ではありません）。

## 生成ZIPの整合性チェック

`py -3 verify_kit.py article_kit_technical.zip`

ZIP内の3ファイル、資料サイズ、SHA256、スタイル、投稿先、取得元の記録を確認します。GitHubの最新コードとの一致や実行安全性は検証しません。


## v0.41 依存関係
Repomixを1.19.0に固定しました。Node.js 22以上とGitが必要です。Windows実機でオンライン取得を確認済みです。

## 最終確認
`py -3 preflight.py` はPython・Node.js 22以上・npx・Git・回帰テストをオフラインで検査します。Windowsでのオンライン取得確認は `FINAL_TEST_GUIDE.md` を参照してください。

## v0.41 追加機能：記事品質検査（オフラインCLI）

既存v0.33のZIP生成・Web UIはそのまま維持し、**別コマンド**で記事の品質検査を追加しました。
記事本文はユーザーがAI等で作成したMarkdownを指定します。外部AI API・ネットワーク通信は不要です。

### Windowsでの実行例

まず記事本文を `article.md` として保存します。生成した記事キットZIP内の `repository_context.md` を取り出してから、展開先で次を実行します。

```powershell
py -3 article_validator.py --article article.md --context repository_context.md --repo owner/repo --out validation_report
```

あるいは手元のソースコード一式を照合元にできます。

```powershell
py -3 article_validator.py --article article.md --source-dir C:\path\to\repo --repo owner/repo --out validation_report
```

`validation_report/report.md` と `validation_report/report.json` が作られます。エラーがある場合は終了コード1、入力エラーは2です。警告だけなら0です。

検査対象：Markdownのコードフェンス・見出し、典型的な秘密情報、インラインファイル名、GitHubソースリンク、Python関数/クラス定義（AST）、明示的な `file.py:function()` 参照。`file.py:function()` は追加した厳密検査用記法であり、通常のQiita記事で必須ではありません。

**制限**：静的検査のみ。リンク先のネットワーク到達性、説明の意味的な正しさ、テスト成功、秘密情報の完全検出を保証しません。Repomixに収集されていないファイルは存在しないと断定できないため、多くの参照不一致は警告です。記事・コードは実行しません。Web UIへの検査フォーム統合は未実装です。

テスト：`py -3 -m unittest discover -p "test_*.py" -q`。Windows実機でオンライン取得を確認済みです。Repomix 1.19.0を指定したCLI取得・ZIP整合性検査に成功しました。

## v0.41 Release Candidate

- Offline article-only validation is supported.
- Source-aware validation remains available.
- The original Windows candidate passed its automated verification.
- Online and browser ZIP generation were verified on Windows using psf/requests; Repomix 1.19.0 CLI verification passed on Windows.

Article-only validation:

    py -3 article_validator.py --article article.md --article-only --out validation_report

## ライセンス

Article Kit本体はMIT Licenseで提供します。著作権表示と許諾文をコピーまたは実質的な部分に保持する条件で、利用・改変・再配布できます。全文と著作権表示は [LICENSE](LICENSE) を参照してください。

生成資料に収録される外部リポジトリのコードや文書には、それぞれの権利条件が適用されます。
