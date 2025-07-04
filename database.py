import sqlite3
import json
from typing import Optional, Dict, Any
from datetime import datetime
import os

DATABASE_PATH = "content_mapper.db"

def init_database():
    """データベースを初期化し、テーブルを作成"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # content_mapsテーブルの作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_maps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            url TEXT NOT NULL,
            selector TEXT,
            manual_selector TEXT,
            manual_body TEXT,
            structure_tree_json TEXT,
            map_hash TEXT,
            is_manual BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # インデックスの作成
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_domain ON content_maps(domain)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON content_maps(url)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_map_hash ON content_maps(map_hash)")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def get_content_map(domain: str) -> Optional[Dict[str, Any]]:
    """ドメインでコンテンツマップを取得"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM content_maps 
        WHERE domain = ? 
        ORDER BY updated_at DESC 
        LIMIT 1
    """, (domain,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def save_content_map(
    domain: str,
    url: str,
    selector: Optional[str] = None,
    manual_selector: Optional[str] = None,
    manual_body: Optional[str] = None,
    structure_tree_json: Optional[str] = None,
    map_hash: Optional[str] = None,
    is_manual: bool = False
) -> bool:
    """コンテンツマップを保存または更新"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # 既存のレコードを確認
        cursor.execute("SELECT id FROM content_maps WHERE domain = ?", (domain,))
        existing = cursor.fetchone()
        
        if existing:
            # 更新
            cursor.execute("""
                UPDATE content_maps 
                SET url = ?, selector = ?, manual_selector = ?, manual_body = ?,
                    structure_tree_json = ?, map_hash = ?, is_manual = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE domain = ?
            """, (url, selector, manual_selector, manual_body, structure_tree_json, 
                  map_hash, is_manual, domain))
        else:
            # 新規作成
            cursor.execute("""
                INSERT INTO content_maps 
                (domain, url, selector, manual_selector, manual_body, structure_tree_json, 
                 map_hash, is_manual)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (domain, url, selector, manual_selector, manual_body, structure_tree_json, 
                  map_hash, is_manual))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_all_content_maps() -> list:
    """すべてのコンテンツマップを取得（デバッグ用）"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM content_maps ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

if __name__ == "__main__":
    # データベースの初期化
    init_database()
    print("Database setup complete!")
