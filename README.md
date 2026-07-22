# Web Game Samples Playground

Google の [`web-game-samples`](https://github.com/google/web-game-samples) に含まれるブラウザ向けデモを、本番ビルドしてそのまま遊べるようにしたランチャーです。

## 遊ぶ

- [Web Game Samples Playground](https://nozomiidev.github.io/gptestch01/)
- [Phaser 3 / Basketball Shoot Out](https://nozomiidev.github.io/gptestch01/demos/phaser/)
- [PixiJS 8 / Playables SDK Demo](https://nozomiidev.github.io/gptestch01/demos/pixijs/)
- [Plain HTML / JS / CSS](https://nozomiidev.github.io/gptestch01/demos/plain/)

## 収録デモ

| デモ | 公開方法 |
| --- | --- |
| Phaser 3 / Basketball Shoot Out | `npm ci && npm run build` で Vite の `dist/` を生成 |
| PixiJS 8 / Playables SDK Demo | `npm ci && npm run build` で TypeScript + Vite の `dist/` を生成 |
| Plain HTML / JS / CSS | ビルド不要。静的ファイルをそのまま配置 |

Godot と Unity のディレクトリは、エディター向け ZIP / Unity Package であり完成済み Web ビルドではないため、このブラウザ公開には含めていません。

## スタンドアロン対応

元のサンプルは YouTube Playables SDK を利用します。公開サイトでは、実際の Playables 環境なら公式 SDK をそのまま使い、通常のブラウザでは保存・一時停止・広告 API などを安全なローカル実装へ切り替えます。

PixiJS 版の外部 Web フォント読み込みも非致命的にしているため、フォント配信が広告ブロッカーやネットワーク設定で遮断されてもゲーム本体は起動します。

## 自動ビルドと公開

`.github/workflows/build-and-publish.yml` が次を自動実行します。

1. このリポジトリと upstream の `google/web-game-samples` を取得
2. Phaser と PixiJS を Node.js 24 でプロダクションビルド
3. Plain HTML 版、SDK フォールバック、ランチャー画面をまとめる
4. ファイル構成を検証してダウンロード可能な Actions artifact を生成
5. GitHub 公式の `upload-pages-artifact` と `deploy-pages` で GitHub Pages に公開

upstream は再現性のため、既定ではコミット `4310035578c205ff503872face8ec91246314af3` に固定しています。Actions の手動実行時には別の ref を指定できます。

## ライセンス

ランチャー部分はこのリポジトリのコードです。各デモと素材のライセンスは upstream の [`LICENSE`](https://github.com/google/web-game-samples/blob/main/LICENSE) および各サンプル内の表記に従います。
