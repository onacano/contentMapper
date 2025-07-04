import requests
import json
from urllib.parse import urlparse, urljoin
from readability import Document
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import hashlib
import time

class HTMLAnalyzer:
    def __init__(self, timeout: int = 5, max_retries: int = 1):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_html(self, url: str) -> str:
        """HTMLを取得（リトライ機能付き）"""
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == self.max_retries:
                    raise Exception(f"Failed to fetch HTML after {self.max_retries + 1} attempts: {str(e)}")
                time.sleep(1)  # 1秒待機してリトライ
        
        raise Exception("Unexpected error in fetch_html")

    def extract_main_content(self, html: str) -> str:
        """Readabilityで本文を抽出"""
        try:
            doc = Document(html)
            return doc.content()
        except Exception as e:
            raise Exception(f"Failed to extract main content: {str(e)}")

    def build_structure_tree(self, html: str, manual_body: Optional[str] = None) -> List[Dict[str, Any]]:
        """HTML構造ツリーを生成"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            def create_node(element, level: int = 0) -> Dict[str, Any]:
                if element.name is None:  # テキストノードをスキップ
                    return None
                
                # 基本情報の取得
                tag = element.name
                classes = element.get('class', [])
                element_id = element.get('id', '')
                
                # CSSセレクタの生成
                selector = tag
                if classes:
                    selector += '.' + '.'.join(classes)
                if element_id:
                    selector += '#' + element_id
                
                # プレビューテキストの取得
                text_content = element.get_text(strip=True)
                preview = text_content[:50] + '...' if len(text_content) > 50 else text_content
                
                # manual_bodyとの一致確認
                state = 'none'
                if manual_body and manual_body.strip():
                    # 先頭100文字で一致確認
                    manual_preview = manual_body[:100]
                    if manual_preview in text_content:
                        state = 'include'
                
                node = {
                    'tag': tag,
                    'class': ' '.join(classes) if classes else '',
                    'id': element_id,
                    'selector': selector,
                    'preview': preview,
                    'state': state,
                    'children': []
                }
                
                # 子要素の処理（直接の子要素のみ、テキストノード除外）
                for child in element.children:
                    if hasattr(child, 'name') and child.name:  # 要素ノードのみ
                        child_node = create_node(child, level + 1)
                        if child_node:
                            node['children'].append(child_node)
                
                return node
            
            # bodyタグから開始
            body = soup.find('body')
            if not body:
                # bodyがない場合はhtmlタグから
                body = soup.find('html')
            
            if body:
                tree = create_node(body)
                return [tree] if tree else []
            else:
                return []
                
        except Exception as e:
            raise Exception(f"Failed to build structure tree: {str(e)}")

    def generate_map_hash(self, url: str, structure_tree: List[Dict[str, Any]]) -> str:
        """構造のハッシュを生成"""
        content = f"{url}_{json.dumps(structure_tree, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def analyze_url(self, url: str, manual_body: Optional[str] = None) -> Dict[str, Any]:
        """URLを解析してすべての情報を返す"""
        try:
            # HTML取得
            html = self.fetch_html(url)
            
            # 本文抽出
            main_content = self.extract_main_content(html)
            
            # 構造ツリー生成
            structure_tree = self.build_structure_tree(html, manual_body)
            
            # ハッシュ生成
            map_hash = self.generate_map_hash(url, structure_tree)
            
            # ドメイン取得
            domain = urlparse(url).netloc
            
            return {
                'url': url,
                'domain': domain,
                'main_content': main_content,
                'structure_tree': structure_tree,
                'map_hash': map_hash,
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'url': url,
                'status': 'error',
                'error': str(e)
            }

if __name__ == "__main__":
    # テスト用
    analyzer = HTMLAnalyzer()
    result = analyzer.analyze_url("https://example.com")
    print(json.dumps(result, indent=2, ensure_ascii=False))
