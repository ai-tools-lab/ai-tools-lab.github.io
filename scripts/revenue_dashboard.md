# Revenue Dashboard Design

## Overview
収益化トラッキングの仕組みと KPI 定義。将来の自動レポート生成に向けた設計書。

## KPI Definitions

| KPI | Source | Target (Month 3) | Target (Month 6) |
|-----|--------|-------------------|-------------------|
| **Pageviews (PV)** | Google Analytics | 5,000/mo | 20,000/mo |
| **Unique Visitors** | Google Analytics | 2,000/mo | 8,000/mo |
| **AdSense Revenue** | Google AdSense | $5/mo | $30/mo |
| **AdSense CTR** | Google AdSense | 1-2% | 2-3% |
| **Affiliate Revenue** | Amazon/各ASP | $10/mo | $50/mo |
| **Affiliate Click Rate** | UTM tracking | 3-5% | 5-8% |
| **Newsletter Subscribers** | Buttondown | 50 | 200 |
| **Email Open Rate** | Buttondown | 40%+ | 35%+ |
| **Bounce Rate** | Google Analytics | <70% | <60% |
| **Avg Session Duration** | Google Analytics | >1:30 | >2:00 |

## Data Sources

### Google Analytics 4
- GA4 Data API (v1) で PV・ユーザー数・流入元を取得
- `google-analytics-data` Python パッケージ使用
- Service Account 認証

### Google AdSense
- AdSense Management API で収益・CTR・RPM を取得
- OAuth2 認証

### Buttondown
- Buttondown API (`https://api.buttondown.com/v1/`)
- API Key 認証
- 購読者数・開封率を取得

### Affiliate
- 手動 CSV 入力 or 各 ASP の API
- UTM パラメータでトラッキング

## Auto-Report Script Design (Future)

```python
#!/usr/bin/env python3
"""revenue_report.py - Weekly revenue report generator"""

# Phase 1: Manual CSV
# - scripts/data/revenue_YYYY-MM.csv に手動記録
# - 月次サマリーを生成

# Phase 2: API Integration
# - GA4 API → PV, users, bounce rate
# - AdSense API → revenue, CTR
# - Buttondown API → subscribers, open rate

# Phase 3: Automated Dashboard
# - GitHub Actions で週次実行
# - Markdown レポートを自動生成
# - content/reports/ に公開（任意）

def generate_weekly_report():
    """Weekly report: Mon-Sun metrics"""
    pass

def generate_monthly_report():
    """Monthly summary with trends"""
    pass

if __name__ == "__main__":
    generate_weekly_report()
```

## Revenue CSV Format (Phase 1)

```csv
date,source,type,amount_usd,notes
2026-02-17,adsense,ad_revenue,0.00,Initial setup
2026-02-17,amazon,affiliate,0.00,Initial setup
```

Store in: `scripts/data/revenue_YYYY-MM.csv`

## Action Items
1. ✅ Google Analytics タグ設置済み（GA ID 設定待ち）
2. ✅ AdSense 広告枠テンプレート設置済み（AdSense ID 設定待ち）
3. ✅ Buttondown フォーム設置済み（Username 設定待ち）
4. ⬜ GA4 プロパティ作成 → ID を hugo.toml に設定
5. ⬜ AdSense アカウント申請 → ID を hugo.toml に設定
6. ⬜ Buttondown アカウント作成 → Username を hugo.toml に設定
7. ⬜ `scripts/data/` ディレクトリ作成、CSV トラッキング開始
8. ⬜ revenue_report.py 実装（Phase 2）
