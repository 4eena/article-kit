# Repomix依存関係（v0.41 RC3）

既定値を `repomix@1.19.0` に固定。2026-11-15にnpmのパッケージ情報で公開済み・MITライセンスを確認。

- https://www.npmjs.com/package/repomix?activeTab=versions
- https://github.com/yamadashy/repomix/releases/tag/v1.19.0
- https://repomix.com/guide/installation

Node.js 22以上およびGitが必要（リモートリポジトリの場合）。

`ARTICLE_KIT_REPOMIX_VERSION` 環境変数で上書き可能。

配布ZIPはnpx経由で利用者の環境に取得する構成です。Repomix、node_modules、npmキャッシュはZIPに同梱しません。固定対象はRepomix本体のバージョンです。推移的依存はnpmが解決します。監査したlockfileのスナップショットと将来の解決結果は異なる場合があります。前回のローカル監査は保存済みのnpm解決記録に基づきます。推移的依存すべてのライセンス原文と将来の解決結果は未確認です。
