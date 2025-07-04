from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from urllib.parse import urlparse
import json

from database import init_database, get_content_map, save_content_map
from analyzer import HTMLAnalyzer

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="ContentMapper API",
    description="Web page structure analysis and content mapping API",
    version="1.0.0"
)

# データベース初期化
init_database()

# HTMLアナライザーの初期化
analyzer = HTMLAnalyzer()

# 静的ファイルの配信（フロントエンド用）
app.mount("/static", StaticFiles(directory="."), name="static")

# Pydanticモデル
class AnalyzeRequest(BaseModel):
    url: str
    manual_body: Optional[str] = None
    manual_selector: Optional[str] = None
    force: Optional[bool] = False

class AnalyzeResponse(BaseModel):
    status: str
    domain: str
    structure_tree: list
    manual_selector: Optional[str] = None
    cached: bool = False
    message: Optional[str] = None

# ルートエンドポイント - フロントエンドを配信
@app.get("/")
async def read_root():
    return FileResponse("index.html")

# メインAPIエンドポイント
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_content(request: AnalyzeRequest):
    """
    ウェブページを解析し、構造ツリーを返す
    
    - **url**: 解析対象のURL
    - **manual_body**: 本文の手動指定（初期ハイライト用）
    - **manual_selector**: 手動CSSセレクタ（保存用）
    - **force**: キャッシュを無視して再解析する
    """
    try:
        # URLのバリデーション
        parsed_url = urlparse(request.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        domain = parsed_url.netloc
        
        # 強制再解析でない場合、キャッシュを確認
        cached_result = None
        if not request.force:
            cached_result = get_content_map(domain)
        
        # キャッシュがある場合
        if cached_result and not request.force:
            try:
                structure_tree = json.loads(cached_result['structure_tree_json'])
                
                # manual_bodyがある場合は初期ハイライトを適用
                if request.manual_body:
                    structure_tree = apply_initial_highlight(structure_tree, request.manual_body)
                
                return AnalyzeResponse(
                    status="success",
                    domain=domain,
                    structure_tree=structure_tree,
                    manual_selector=cached_result.get('manual_selector'),
                    cached=True,
                    message="Cached result"
                )
            except json.JSONDecodeError:
                # キャッシュが壊れている場合は新規解析
                pass
        
        # 新規解析
        result = analyzer.analyze_url(request.url, request.manual_body)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        
        # データベースに保存
        structure_tree_json = json.dumps(result['structure_tree'], ensure_ascii=False)
        save_success = save_content_map(
            domain=domain,
            url=request.url,
            structure_tree_json=structure_tree_json,
            map_hash=result['map_hash'],
            manual_selector=request.manual_selector,
            manual_body=request.manual_body,
            is_manual=bool(request.manual_selector)
        )
        
        if not save_success:
            print("Warning: Failed to save to database")
        
        return AnalyzeResponse(
            status="success",
            domain=domain,
            structure_tree=result['structure_tree'],
            manual_selector=request.manual_selector,
            cached=False,
            message="Analysis complete"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def apply_initial_highlight(structure_tree: list, manual_body: str) -> list:
    """manual_bodyに基づいて初期ハイライトを適用"""
    def highlight_nodes(nodes):
        for node in nodes:
            if node.get('preview') and manual_body[:100] in node['preview']:
                node['state'] = 'include'
            if node.get('children'):
                highlight_nodes(node['children'])
    
    highlight_nodes(structure_tree)
    return structure_tree

# 保存エンドポイント
@app.post("/api/save")
async def save_configuration(request: AnalyzeRequest):
    """
    設定を保存
    """
    try:
        if not request.url or not request.manual_selector:
            raise HTTPException(status_code=400, detail="URL and manual_selector are required")
        
        domain = urlparse(request.url).netloc
        
        success = save_content_map(
            domain=domain,
            url=request.url,
            manual_selector=request.manual_selector,
            manual_body=request.manual_body,
            is_manual=True
        )
        
        if success:
            return {"status": "success", "message": "Configuration saved"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# デバッグ用エンドポイント
@app.get("/api/debug/content_maps")
async def debug_content_maps():
    """すべてのコンテンツマップを返す（デバッグ用）"""
    from database import get_all_content_maps
    return get_all_content_maps()

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "ContentMapper API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
