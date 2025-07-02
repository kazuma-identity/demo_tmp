"""
Streamlit音声機能検証アプリ
app.pyの音声機能を単体でテストします
"""

import streamlit as st
import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="音声機能テスト", page_icon="🔊")
st.title("🔊 Streamlit 音声機能テスト")

# セッション状態の初期化
if "audio_counter" not in st.session_state:
    st.session_state.audio_counter = 0

# API接続確認
def get_client():
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key.startswith("sk-"):
        return OpenAI(api_key=api_key)
    return None

# autoplay関数（app.pyと同じ）
def autoplay(mp3: bytes, uid=""):
    if not mp3:
        st.error("音声データが空です")
        return
    
    b64 = base64.b64encode(mp3).decode()
    st.markdown(f"""
    <audio id="a{uid}" preload="auto">
      <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
    </audio>
    <script>
      (function() {{
        const el = document.getElementById("a{uid}");
        if (!el) {{
            console.error('Audio element not found: a{uid}');
            return;
        }}
        
        // グローバルな音声キューを初期化
        if (!window.audioQueue) {{
            window.audioQueue = [];
            window.isPlaying = false;
            console.log('Audio queue initialized');
        }}
        
        // 新しい音声をキューに追加
        window.audioQueue.push(el);
        console.log('Audio added to queue. Queue length:', window.audioQueue.length);
        
        // 再生関数
        function playNext() {{
            if (window.isPlaying || window.audioQueue.length === 0) {{
                console.log('Already playing or queue empty');
                return;
            }}
            
            window.isPlaying = true;
            const audio = window.audioQueue.shift();
            audio.playbackRate = 1.5;  // 1.5倍速
            
            console.log('Attempting to play audio...');
            audio.play().then(() => {{
                console.log('✅ Audio playback started: {uid}');
                document.getElementById('status').textContent = '✅ 再生中: {uid}';
            }}).catch(e => {{
                console.error('❌ Audio playback error:', e);
                document.getElementById('status').textContent = '❌ 再生エラー: ' + e.name;
                window.isPlaying = false;
                // エラー時は次の音声を試す
                setTimeout(playNext, 100);
            }});
            
            audio.onended = () => {{
                console.log('✅ Audio playback ended: {uid}');
                document.getElementById('status').textContent = '✅ 再生完了: {uid}';
                window.isPlaying = false;
                playNext();
            }};
        }}
        
        // 再生中でなければ再生開始
        if (!window.isPlaying) {{
            console.log('Starting playback...');
            playNext();
        }}
      }})();
    </script>
    """, unsafe_allow_html=True)

# ステータス表示用
st.markdown('<div id="status" style="color: green; font-weight: bold;">待機中...</div>', unsafe_allow_html=True)

# メインコンテンツ
tab1, tab2, tab3 = st.tabs(["基本テスト", "自動再生テスト", "連続再生テスト"])

with tab1:
    st.header("基本的な音声再生テスト")
    
    client = get_client()
    if client:
        st.success("✅ OpenAI API 接続OK")
        
        # テキスト入力
        text = st.text_input("読み上げテキスト", value="こんにちは、音声テストです。")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔊 st.audio()で再生"):
                with st.spinner("音声生成中..."):
                    try:
                        response = client.audio.speech.create(
                            model="tts-1",
                            voice="nova",
                            input=text,
                            response_format="mp3"
                        )
                        audio_bytes = response.content
                        st.success(f"生成成功: {len(audio_bytes)} bytes")
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.error(f"エラー: {e}")
        
        with col2:
            if st.button("🔊 autoplayで再生"):
                with st.spinner("音声生成中..."):
                    try:
                        response = client.audio.speech.create(
                            model="tts-1",
                            voice="nova",
                            input=text,
                            response_format="mp3"
                        )
                        audio_bytes = response.content
                        st.success(f"生成成功: {len(audio_bytes)} bytes")
                        st.session_state.audio_counter += 1
                        autoplay(audio_bytes, f"test{st.session_state.audio_counter}")
                    except Exception as e:
                        st.error(f"エラー: {e}")
    else:
        st.error("❌ API接続エラー: .envファイルを確認してください")

with tab2:
    st.header("自動再生テスト")
    st.info("ページ読み込み時に自動的に音声を再生します")
    
    if st.button("🔄 ページをリロード"):
        st.rerun()
    
    # 自動再生（初回のみ）
    if "auto_played" not in st.session_state:
        st.session_state.auto_played = True
        client = get_client()
        if client:
            try:
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input="自動再生テストです。",
                    response_format="mp3"
                )
                autoplay(response.content, "auto")
                st.success("自動再生を開始しました")
            except Exception as e:
                st.error(f"自動再生エラー: {e}")

with tab3:
    st.header("連続再生テスト")
    
    sentences = [
        "これは1番目の文章です。",
        "これは2番目の文章です。",
        "これは3番目の文章です。"
    ]
    
    if st.button("🔊 連続再生開始"):
        client = get_client()
        if client:
            progress = st.progress(0)
            status = st.empty()
            
            for i, sentence in enumerate(sentences):
                status.text(f"生成中 {i+1}/{len(sentences)}: {sentence}")
                try:
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice="nova",
                        input=sentence,
                        response_format="mp3"
                    )
                    st.session_state.audio_counter += 1
                    autoplay(response.content, f"seq{st.session_state.audio_counter}")
                    progress.progress((i + 1) / len(sentences))
                except Exception as e:
                    st.error(f"エラー ({i+1}): {e}")
            
            status.text("✅ すべての音声を生成しました")

# デバッグ情報
with st.expander("🔧 デバッグ情報"):
    st.write("**セッション状態:**")
    st.json({
        "audio_counter": st.session_state.audio_counter,
        "auto_played": st.session_state.get("auto_played", False)
    })
    
    st.write("**コンソールログの確認方法:**")
    st.info("ブラウザのデベロッパーツール（F12）を開いてConsoleタブを確認してください")
    
    st.write("**よくある問題:**")
    st.warning("""
    - 自動再生がブロックされる場合：ユーザーがページと対話（クリック等）した後でないと自動再生できません
    - 音声が聞こえない場合：ブラウザの音量設定、システムの音量設定を確認してください
    - エラーが出る場合：コンソールログを確認してください
    """)

# JavaScriptコンソール表示
st.markdown("""
<script>
console.log('=== Streamlit Audio Test Page Loaded ===');
console.log('Audio Queue:', window.audioQueue);
console.log('Is Playing:', window.isPlaying);
</script>
""", unsafe_allow_html=True)