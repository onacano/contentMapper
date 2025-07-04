ContentMapper｜構造マップAPI（インタラクティブ UI 版）
　AIレス・OSS主体（Readability + 手動 UI）で本文抽出
　　サイトごとに構造保存（content_maps）
　　● 手動セレクタ入力・ツリークリックで本文／除外指定
　　● 本文冒頭テキストで自動ハイライト
　　● 将来 AI を env で ON に出来る拡張性を保持

認証　Google Firebase Authentication
形態　Webサービス＋APIサービスのみ
環境変数（READMEで詳細記載）
　DATABASE_URL, MAX_CALLS_PER_MIN, MAX_CALLS_PER_DAY, USE_AI (0/1) ほか

⬛️ 根本システム
　1. 入力：URL + (optional) manual_body
　　1-1 content_maps にキャッシュ確認
　2. HTML取得：requests.get + retry
　3. 本文抽出 & ツリー生成（Readability）
　4. DB保存：domain, selector, structure_tree_json, map_hash, updated_at
　！再解析フック／手動 UI で include・exclude 指定