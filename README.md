# Web Game Samples Playground

Google の [`web-game-samples`](https://github.com/google/web-game-samples) に含まれる、ブラウザ向けデモを本番ビルドして遊べるようにするランチャーです。

## 遊ぶ

- GitHub Pages: https://nozomiidev.github.io/gptestch01/
- Pages 有効化前のプレビュー: https://raw.githack.com/nozomiidev/gptestch01/gh-pages/index.html
- Phaser: `demos/phaser/`
- PixiJS: `demos/pixijs/`
- Plain HTML / JS / CSS: `demos/plain/`

## 収録デモ

| デモ | 公開方法 |
| --- | --- |
| Phaser 3 / Basketball Shoot Out | `npm ci && npm run build` で Vite の `dist/` を生成 |
| PixiJS 8 / Playables SDK Demo | `npm ci && npm run build` で TypeScript + Vite の `dist/` を生成 |
| Plain HTML / JS / CSS | ビルド不要。静的ファイルをそのまま配置 |

Godot と Unity のディレクトリは、エディター向け ZIP / Unity Package であり完成済み Web ビルドではないため、このブラウザ公開には含めていません。

## スタンドアロン対応

元のサンプルは YouTube Playables SDK を利用します。公開サイトでは実際の Playables 環境なら公式 SDK をそのまま使い、通常のブラウザでは保存・一時停止・広告 API などを安全なローカル実装へ切り替えます。これにより PixiJS サンプルも SDK 外で起動できます。

## 自動ビルド

`.github/workflows/build-and-publish.yml` が次を行います。

1. このリポジトリと upstream の `google/web-game-samples` を取得
2. Phaser と PixiJS を Node.js でプロダクションビルド
3. Plain HTML 版、SDK フォールバック、ランチャー画面をまとめる
4. 完成サイトを Actions artifact と `gh-pages` ブランチへ公開

upstream は再現性のため、既定ではコミット `4310035578c205ff503872face8ec91246314af3` に固定しています。Actions の手動実行時には別の ref を指定できます。

## GitHub Pages の初回設定

Pages がまだ有効でない場合だけ、リポジトリの **Settings → Pages → Deploy from a branch** で `gh-pages` と `/(root)` を選択します。ビルド済みファイル自体は上記プレビュー URL からも確認できます。

## ライセンス

ランチャー部分はこのリポジトリのコードです。各デモと素材のライセンスは upstream の [`LICENSE`](https://github.com/google/web-game-samples/blob/main/LICENSE) および各サンプル内の表記に従います。
