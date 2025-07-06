[# 7daysSPRINT]
 0. GithubRepository, [FastAPI] skeleton　		制作環境整備
 1. [SQLite], content_maps table 設定　　　 	動作テスト
 2. HTML fetch + Readability　　　　　　　 	通常レス JSON(mock)
 3. ツリー JSON 生成関数　　　　　　　　	解析動作テスト
 4. インタラクティブツリー UI　　　　　 	include/exclude クリック実装
 5. [さくらのVPS] 公開　　　　　　　　　 	外部からの利用確認
 6. [Firebase Auth] + 再解析　　　　　　 		認証 UI 完成
 7. 負荷テスト & バグ修正　　　　　　　 	[MVP] リリース
[# ROADMAP]
⬛️ フェーズ0 Foundation ― 不可逆な土台の整備
　技術スタック
　　Python 3.12 + FastAPI／Uvicorn
　　SQLite (content_mapper.db)
　　GitHub Actions：ruff・mypy・pytest
⬜️ 完了基準
　`uvicorn main:app` 起動／`/docs` 表示
⬛️ フェーズ1 Core ― API 心臓部
　エンドポイント `/api/analyze`
　　POST `{ url, manual_body?, manual_selector? }`
　処理フロー
　　1. `SELECT * FROM content_maps WHERE domain=?`
　　2. HTML取得 (5s, 1retry)
　　3. Readability → main_html
　　4. structure_tree_json 生成
　　5. CSSセレクタ：manual_selector か自動推定(未実装)
　　6. INSERT OR REPLACE content_maps
⬜️ 完了基準
　キャッシュヒットで即レス／手動入力で AI 不要
⬛️ フェーズ2 UI & Deploy
　インタラクティブツリー UI（仕様は後述）
　さくらのVPS に API + フロント一体デプロイ
⬜️ 完了基準
　公開 URL でツリー操作 → selector 保存成功
⬛️ フェーズ3 Secure & Reanalyze
　Firebase Auth（制作者アカウントのみ）
  フロントで ID トークン取得 → `Authorization: Bearer` ヘッダ
  FastAPI ミドルウェアで検証（非認証は 401）
　再解析ボタン `force=true`
  フロントに「再解析」ボタン
  API: クエリ `force=true` 受信でキャッシュ無視
⬜️ 完了基準
　認証必須・再解析でキャッシュ更新
⬛️ フェーズ4 Polish
　500 エラー GitHub Actions → Slack 通知
　MAX_CALLS_* 環境変数で日次上限制御
　Locust で 50 req/min 耐性確認
⬛️ 後回し
　本格監視 / Redis 多段キャッシュ / 課金プラン / AI モード (USE_AI=1)


[# UI_SPEC]
■ レイアウト
　┌ URL入力 ＋ Fetch ボタン
　├ 本文冒頭テキスト入力 (任意)
　├ CSS Selector フィールド（自動生成 & 手修正可）
　└ ツリー表示パネル（scroll）
■ ツリー JSON 形式
　`{ tag, class, id, selector, preview, state }`
　　state = "none" | "include" | "exclude"
■ ノード表示ラベル
　`tag.class#id  [先頭20字…]`
■ 状態トグル
　クリック毎に → none → include → exclude → none
　　include : `bg-include` (#d6ffd6)
　　exclude : `bg-exclude` (#ffd6d6)
■ 初期ハイライト
　manual_body が送信されていれば
　　サーバー側で一致ノードに `state:"include"` を付与
■ 操作フロー
　1. URL＋本文テキスト入力 → Fetch
　2. ツリー描画（include ノード緑）
　3. クリックで状態変更
　4. include ノードの selector を自動合成
　　　exclude は `:not()` で削除　　　　　　　　　例）`.content, .content2:not(.ad)`
　5. Save → POST （AI スキップ）
■ バリデーション
　‐ selector が 0 件なら警告
　‐ 256 文字超, 危険文字は拒否
■ DB 保存サンプル
　domain: `example.com`
　selector: `.content, .content2:not(.ad)`
　structure_tree_json: `[…state情報込み…]`
　is_manual: TRUE
■ 拡張フック
　`USE_AI=1` にすると manual_selector が空の時だけ AI プロバイダ呼出
