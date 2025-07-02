# ウイルス検知デモシステム

CSIRT（Computer Security Incident Response Team）対応のデモンストレーション用Streamlitアプリケーションです。ウイルス検知時の初動対応をAI（GPT-4o）がサポートするシミュレーションを行います。

## 機能

- 🦠 ウイルス検知シミュレーション
- 🔴 感染端末の自動ネットワーク遮断（表示上）
- 🤖 GPT-4oによる初動対応支援チャット
- 📝 イベントログの記録
- 📥 セッションログのMarkdownエクスポート

## 必要要件

- Python 3.8以上
- OpenAI APIキー（GPT-4o/GPT-4o-miniを使用）

## セットアップ

### 1. リポジトリのクローンまたはファイルのダウンロード

```bash
cd /path/to/your/directory
```

### 2. Python仮想環境の作成と有効化

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env.example`をコピーして`.env`を作成し、OpenAI APIキーを設定します：

```bash
cp .env.example .env
```

`.env`ファイルを編集：
```
OPENAI_API_KEY=your-actual-api-key-here
```

## 起動方法

```bash
streamlit run app.py
```

ブラウザが自動的に開き、`http://localhost:8501`でアプリケーションが表示されます。

## 使い方

1. **ウイルス発生シミュレーション**
   - 「🦠 ウイルス発生」ボタンをクリック
   - ポップアップで警告が表示されます

2. **AI対応チャット**
   - ポップアップを閉じると、AIからの初動質問が表示されます
   - チャット欄で状況を説明し、AIの指示に従ってください

3. **セッションリセット**
   - 「🔄 Reset」ボタンでセッションをリセットできます

4. **ログエクスポート**
   - イベントログ欄の「📥 Export MD」ボタンでセッションログをMarkdown形式でダウンロードできます

## 注意事項

- このアプリケーションはデモ用途のみです
- ネットワーク遮断は表示上のシミュレーションであり、実際のネットワーク制御は行いません
- OpenAI APIキーが設定されていない場合は、スタブモードで動作します

## トラブルシューティング

### APIキーエラーが発生する場合
- `.env`ファイルが正しく作成されているか確認してください
- APIキーが有効で、適切な権限があることを確認してください

### ポートが使用中の場合
```bash
streamlit run app.py --server.port 8502
```

## ライセンス

このプロジェクトはデモンストレーション目的で作成されています。