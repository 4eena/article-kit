# Windows 11 実機検証

1. ZIPをエクスプローラーの「すべて展開」で新規フォルダーに展開してください。日本語名のバッチファイル2本が正しく表示されることを確認します。
2. 展開フォルダーでPowerShellを開き、次を実行してください。ZIPを展開フォルダーの親に置いた例です。場所が違う場合はZIPへのパスを変更してください。

   ```powershell
   $env:PYTHONIOENCODING = 'utf-8'
   py -3.10 -X utf8=0 .\verify_windows.py ..\ArticleKit_v041_RC3_Public_Release_Final.zip
   ```

   Python 3.10.11、Node.js 26.13.1、locale cp932、Repomix 1.19.0 の表示を確認します。ZIPと展開内容、同梱の回帰テスト、実際のGitHub取得、CLIとWeb両スタイルの生成ZIPを一括検証します。別の公開リポジトリで試すには `--repo https://github.com/owner/repo` を追加します。
3. 古いArticle Kitのコンソールを閉じ、`start_windows.bat` をダブルクリックします。ブラウザーが開いてv0.41が表示されることを確認します。`https://github.com/psf/requests` を入力し、ファイル選択を空欄にして、技術解説型と開発ストーリー型でZIPを保存します。
4. 保存した各ZIPを `py -3.10 verify_kit.py "ZIPのパス"` で検証します。出力で `repomix_remote` と各スタイルを確認します。失敗時はコマンド出力と画面エラーを記録してください。

一括検証の `--offline` はnpm・GitHub通信を省略します。オフライン合格とは別に、上記のオンライン実行とブラウザー操作の結果が必要です。
