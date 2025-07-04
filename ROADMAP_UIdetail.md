ContentMapper｜ツリー UI 追加仕様（抜粋）

　インタラクティブツリーのノード状態
　　● デフォルト　　　　…背景なし（未選択）
　　● 本文 (include) …ワンクリックで グリーンバック bg-include
　　● 除外 (exclude) …本文ノードを再クリック〈または2クリック目〉で レッドバック bg-exclude
　　● さらにクリックするとデフォルトへ戻る（3 状態トグル）

　初期ハイライト
　　● API リクエストで manual_body が送られている場合
　　　○ 先頭 100 文字をサーバ側で検索 → 一致ノードを 本文 (include) 状態で JSON に state:"include" として返す
　　● フロントは受信ツリー JSON の state を反映し、該当ノードに bg-include を付与

　ノード表示ラベル
　　● 先頭 20 文字の本文プレビューを […] 付きで表示
　　　例）<p>… → p .content [今日は晴れだっ…]
　　● 長い文字列は 20 文字で省略し … 付与

　CSS クラス例
　　css 　　.bg-include { background:#d6ffd6; } /* グリーン */ 　　.bg-exclude { background:#ffd6d6; } /* レッド */ 　　

　クリック実装（Vanilla JS）
　　js 　　function toggleState(li){ 　　 const curr = li.dataset.state ?? "none"; 　　 const next = curr==="none" ? "include" : curr==="include" ? "exclude" : "none"; 　　 li.dataset.state = next; 　　 li.classList.toggle("bg-include", next==="include"); 　　 li.classList.toggle("bg-exclude", next==="exclude"); 　　 updateSelectorField(); // include状態ノードの共通 CSS を生成し入力欄へ 　　} 　　

　保存時の POST 例
　　json 　　{ 　　 "url":"https://example.com/post/123", 　　 "manual_selector":".content, .content2:not(.ad)", 　　 "manual_body":"今日は晴れだったので…" 　　} 　　
　　※ manual_selector はフロントで include ノードを列挙し自動生成（exclude ノードは :not() で削除）


最小実現コード例
<!-- index.html -->
<input id="url">
<button id="fetch">Fetch</button>
<textarea id="body"></textarea>
<input id="selector">
<button id="save">Save</button>

<ul id="tree"></ul>

<script>
function renderTree(node, parentUl){
  const li = document.createElement('li');
  li.textContent = node.label;
  li.dataset.selector = node.selector;
  li.onclick = () => {
    document.getElementById('selector').value = li.dataset.selector;
    highlightPreview(li.dataset.selector);
  };
  parentUl.appendChild(li);
  if(node.children){
    const ul = document.createElement('ul');
    li.appendChild(ul);
    node.children.forEach(c=>renderTree(c, ul));
  }
}
</script>
