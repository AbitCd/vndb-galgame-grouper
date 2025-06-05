# VNDB Galgame Grouper

[![License](https://img.shields.io/github/license/AbitCd/vndb-galgame-grouper)](LICENSE.txt)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)
[![Downloads](https://img.shields.io/github/downloads/AbitCd/vndb-galgame-grouper/total)](https://github.com/AbitCd/vndb-galgame-grouper/releases)

VNDBデータベースに基づいてビジュアルノベル（ギャルゲー）フォルダを一括管理するツールです。ゲームを開発者、声優などの情報でグループ化し、フォルダ名をメインタイトルに自動的にリネームします。VNDB APIを利用して開発され、複数の使用方法と柔軟な設定オプションを提供します。

[English](README_en.md) | [简体中文](README.md) | 日本語

---
## ✨ 主な機能

- 🎮 VNDBデータベース内のゲームを自動認識
  - あいまい照合によるマッチング（平均3秒/項目）
  - 正規表現による多様な命名規則の認識
  - 照合精度の調整が可能

- 📂 グループ化機能
  - VN（ビジュアルノベル）と非VNコンテンツの自動分類
  - 開発会社、スタッフなどでグループ化

- 🔄 フォルダ名の変更
  - 標準化された命名規則に対応
  - オリジナル名または一般名の選択
  - 重要な識別情報の維持

- 💡 複数の使用方法
  - 直感的なGUIインターフェース
  - コマンドライン操作
  - 設定ファイルによる制御
## 💻 システム要件

- Python 3.8以上
- 対応OS：
  - Windows 10/11
  - Linux (Ubuntu 18.04+, CentOS 7+)
  - macOS 10.15+
- メモリ：最小2GB RAM（4GB以上推奨）
- ディスク容量：最小1GB（キャッシュとインデックス用）
## ⚡ パフォーマンスの最適化

- 初回実行時にあいまい照合用のインデックスをダウンロードして構築（数分かかる場合があります）
- 処理速度向上のためキャッシュの有効化を推奨：
  ```bash
  python main.py --folder /path/to/games --api-cache --group-cache
  ```
- 大量のファイル処理時の推奨事項：
  - キャッシュファイルにSSDを使用
  - あいまい照合のしきい値を適切に調整
  - バッチ処理の使用を検討
## 🚀 クイックスタート

1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

2. ツールの実行
```bash
# GUIモード
python main.py

# CLIモード
python main.py --cli
```

3. 基本的な使用例
```bash
# 特定のフォルダを処理
python main.py --folder /path/to/games

# あいまい照合を有効化
python main.py --folder /path/to/games --enable-fuzzy-match

# 全機能を使用する例
python main.py --folder /path/to/games --do-vn-group --tag-field developers --normalize
```
## 📖 詳細なドキュメント

詳細な使用方法については[usage.md](usage.md)を参照してください。

## ❓ よくある質問

1. **あいまい照合の精度が低い場合**
   - fuzzy_match_thresholdの値を調整（デフォルト0.4）
   - regex_filterを使用してフォルダ名を前処理
   - debug_modeで照合過程を確認

2. **処理速度の改善方法**
   - キャッシュ機能が有効か確認
   - ネットワーク状態を確認
   - バッチ処理モードの利用を検討

3. **特殊文字の対応**
   - 日本語・中国語の文字は標準対応
   - normalize_nameで文字を標準化
   - 必要に応じて正規表現フィルタを調整

4. **フォルダの権限問題**
   - 読み書き権限の確認
   - 管理者として実行
   - ファイルシステムの権限設定を確認

その他の質問についてはIssueを作成してください。
## 📝 ライセンス

このプロジェクトはGPLv3ライセンスの下で提供されています。詳細は[LICENSE](LICENSE.txt)ファイルを参照してください。

## ⭐ スター履歴

[![Star History Chart](https://api.star-history.com/svg?repos=AbitCd/vndb-galgame-grouper&type=Date)](https://star-history.com/#AbitCd/vndb-galgame-grouper&Date)

## 📧 お問い合わせ

問題の報告や機能の提案は以下の方法でお願いします：

- GitHubでIssueを作成

## ⭐ 備考
AIで生成したドキュメントです。日本語版のドキュメントを読む人がいるでしょうか？