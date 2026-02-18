# 記事自動スケジューラー設計書

## 概要

週5本（平日毎日）の新記事を自動生成・公開するシステム。
GitHub Actionsで実行し、OpenAI APIで記事を生成、Hugo + GitHub Pagesでデプロイする。

## アーキテクチャ

```
GitHub Actions (cron: 平日 09:00 UTC)
  ↓
scripts/generate_article.py (記事生成スクリプト)
  ├── 1. 既存タイトル一覧を取得
  ├── 2. トピック候補を生成（重複チェック付き）
  ├── 3. OpenAI APIで記事本文を生成
  ├── 4. frontmatter付きMarkdownファイルを保存
  └── 5. OG画像を生成（オプション）
  ↓
git commit & push
  ↓
GitHub Pages 自動デプロイ（既存workflow or Hugo build）
```

## トピック重複回避の仕組み

### 方法: タイトル類似度チェック

1. `content/posts/` 内の全既存タイトルを収集
2. 新トピック候補を OpenAI API で5〜10個生成
3. 各候補について既存タイトルとの類似度を計算:
   - **方法A（軽量）**: Jaccard類似度（単語の集合ベース）— 閾値 0.5 以上は却下
   - **方法B（高精度）**: OpenAI Embeddings → cosine similarity — 閾値 0.85 以上は却下
4. 類似度が低い候補から1つ選択

### トピックカテゴリの分散

```python
CATEGORIES = [
    "AI Agents",        # 月曜
    "AI Coding Tools",  # 火曜
    "AI Automation",    # 水曜
    "Business Productivity",  # 木曜
    "Tool Reviews & Comparisons",  # 金曜
]
```

曜日ごとにカテゴリを固定し、偏りを防ぐ。

## 記事生成スクリプト仕様

### `scripts/generate_article.py`

```python
# 主要フロー
def main():
    existing_titles = get_existing_titles("content/posts/")
    category = get_today_category()  # 曜日ベース
    
    # OpenAI APIでトピック候補を生成
    candidates = generate_topic_candidates(category, existing_titles)
    
    # 類似度チェックで重複排除
    topic = select_unique_topic(candidates, existing_titles)
    
    # 記事本文を生成
    article = generate_article(topic, category)
    
    # Markdownファイルとして保存
    save_article(article)
```

### OpenAI API利用

- **モデル**: `gpt-4o` (コスト効率と品質のバランス)
- **トピック生成**: 1リクエスト（~500 tokens）
- **記事生成**: 1リクエスト（~2000 tokens）
- **推定コスト**: 1記事あたり約 $0.01〜0.03
- **月間コスト**: 約 $0.20〜0.60（週5本 × 4週）

## GitHub Actions Workflow

ファイル: `.github/workflows/auto-publish.yml`

### トリガー
- cron: `0 9 * * 1-5` (UTC月〜金 09:00 = MST 02:00)
- 手動実行 (`workflow_dispatch`) も可能

### ステップ
1. リポジトリをcheckout
2. Python環境セットアップ
3. `pip install openai`
4. `python3 scripts/generate_article.py` 実行
5. 変更があれば commit & push
6. Hugo buildとデプロイは既存のデプロイworkflowに委譲

### Secrets
- `OPENAI_API_KEY`: OpenAI APIキー

## 運用ガイド

### 初期設定

1. GitHub Secretsに `OPENAI_API_KEY` を設定
2. リポジトリの Actions 権限で write を許可
3. `scripts/generate_article.py` のプロンプトをレビュー

### モニタリング

- GitHub Actions のログで生成状況を確認
- 週次で生成記事の品質をレビュー
- 必要に応じてプロンプトを調整

### 緊急停止

- GitHub Actions の workflow を disable にする
- または `.github/workflows/auto-publish.yml` を削除して push

## 今後の拡張

- [ ] SNS自動投稿（`social_post.py` と連携）
- [ ] SEOスコアチェック（公開前の品質ゲート）
- [ ] アフィリエイトリンクの自動挿入
- [ ] Google Analytics連携によるトピック最適化
- [ ] A/Bテスト（タイトルバリエーション）
