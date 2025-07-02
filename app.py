import streamlit as st
import os
import hashlib
import base64
from io import BytesIO
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

# 環境変数の読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="ウイルス検知デモ",
    page_icon="🦠",
    layout="wide"
)

# ===== ユーティリティ関数 =====
def get_client():
    """OpenAIクライアントを取得"""
    return OpenAI()


def hash_audio(audio_bytes):
    """音声データのハッシュ値を計算"""
    return hashlib.md5(audio_bytes).hexdigest()

def autoplay_audio(audio_bytes):
    """音声を自動再生（HTMLのaudioタグ使用）"""
    if not audio_bytes:
        return

    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

# ===== セッション状態の初期化 =====
def init_session_state():
    """セッション状態を初期化"""
    defaults = {
        "logged_in": False,
        "infected": False,
        "chat": [],
        "ai_responding": False,
        "last_audio_hash": "",
        "initial_message_sent": False,
        "audio_counter": 0
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ===== 音声関連関数 =====
def text_to_speech(text):
    """テキストを音声に変換"""
    client = get_client()
    if not client:
        return None

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="mp3"
        )
        return response.content
    except Exception as e:
        print(f"TTSエラー: {e}")
        return None

def speech_to_text(audio_bytes):
    """音声をテキストに変換"""
    client = get_client()
    if not client:
        return None

    try:
        audio_file = BytesIO(audio_bytes)
        audio_file.name = "audio.wav"

        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ja"
        )
        return response.text
    except Exception as e:
        print(f"STTエラー: {e}")
        return None


# ===== AI応答関数 =====
def get_ai_response(messages):
    """AIからの応答を取得（ストリーミング）"""
    client = get_client()
    if not client:
        yield "APIクライアントが利用できません。"
        return

    system_prompt = """あなたはCSIRT（Computer Security Incident Response Team）のAIアシスタントです。
ウイルス感染が検知された端末のユーザーに対して、冷静かつ的確な初動対応の指示を行ってください。
ウイルス対策ソフトでの検知されて、対象端末では自動的にネットワークを削除しています。
あなたが、対応するのは、その端末の所有者です。
以下の点に注意して対応してください：
1. ユーザーを安心させながら、状況を正確に把握する
2. 必要な情報を段階的に収集する
3. 適切な対処方法を分かりやすく説明する
4. 技術的な用語は避け、一般ユーザーにも理解できる言葉を使う"""

    # APIメッセージの準備
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages[-10:]:  # 最新10件のみ
        if msg["sender"] == "user":
            api_messages.append({"role": "user", "content": msg["text"]})
        elif msg["sender"] == "ai":
            api_messages.append({"role": "assistant", "content": msg["text"]})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
            stream=True,
            temperature=0.7,
            max_tokens=500
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"エラーが発生しました: {str(e)}"

# ===== ログイン機能 =====
def login_page():
    """ログインページを表示"""
    st.markdown(
        """
        <div style="text-align: center; padding: 50px;">
            <h1>🦠 ウイルス検知デモシステム</h1>
            <h3>ログインしてください</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ログインフォーム
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("ユーザー名", placeholder="ユーザー名を入力")
            password = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
            submitted = st.form_submit_button("ログイン", use_container_width=True)

            if submitted:
                if username == "aice" and password == "aice":
                    st.session_state.logged_in = True
                    st.success("ログイン成功！")
                    st.rerun()
                else:
                    st.error("ユーザー名またはパスワードが正しくありません")

# ===== メイン処理 =====
def main():
    init_session_state()

    # ログインチェック
    if not st.session_state.logged_in:
        login_page()
        return

    # ヘッダー
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.title("🦠 ウイルス検知デモシステム")

    with col2:
        if st.button("🦠 ウイルス発生", type="primary", disabled=st.session_state.infected):
            st.session_state.infected = True
            st.session_state.initial_message_sent = False
            st.rerun()

    with col3:
        col3_1, col3_2 = st.columns(2)
        with col3_1:
            if st.button("🔄 Reset"):
                # ログイン状態以外をリセット
                logged_in = st.session_state.logged_in
                for key in list(st.session_state.keys()):
                    if key != "logged_in":
                        del st.session_state[key]
                init_session_state()
                st.session_state.logged_in = logged_in
                st.rerun()

        with col3_2:
            if st.button("🚪 ログアウト"):
                st.session_state.logged_in = False
                st.rerun()

    # 状態表示
    if st.session_state.infected:
        st.error("🔴 **ウイルス感染対応中** - CSIRTと通話しています")
    else:
        st.success("✅ **正常稼働中** - システムは正常に動作しています")

    st.divider()

    # 初期メッセージの送信と音声再生
    if st.session_state.infected and not st.session_state.initial_message_sent:
        initial_messages = [
            {"sender": "system", "text": "【システム通知】セキュリティ上の脅威を検出したため、この端末をネットワークから自動的に切断しました。"},
            {"sender": "ai", "text": "こんにちは。CSIRTのAIアシスタントです。ウイルス感染の可能性が検出されました。落ち着いて対応しましょう。\n\n何か普段と違うことにお気づきでしたか？"}
        ]
        st.session_state.chat.extend(initial_messages)
        st.session_state.initial_message_sent = True

        # 初期メッセージの音声を生成して保存
        initial_audio = text_to_speech(initial_messages[1]["text"])
        if initial_audio:
            st.session_state["last_ai_audio"] = initial_audio

    # メインコンテンツ
    left_col, right_col = st.columns(2)

    # 左側：感染端末の状態
    with left_col:
        st.subheader("端末 A (感染端末)")
        if st.session_state.infected:
            st.error("🔴 Infected & Disconnected")
            st.info("ネットワークから切断されました")
        else:
            st.success("🟢 Healthy")
            st.info("正常に動作しています")

    # 右側：チャット表示
    with right_col:
        st.subheader("端末 B (CSIRT AI対応)")

        if st.session_state.infected:
            # チャットメッセージの表示
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.chat:
                    if message["sender"] == "ai":
                        st.chat_message("assistant").write(message["text"])
                    elif message["sender"] == "user":
                        st.chat_message("user").write(message["text"])
                    elif message["sender"] == "system":
                        st.info(message["text"])

            # AI音声の再生エリア
            if "last_ai_audio" in st.session_state:
                st.markdown("---")
                st.markdown("**🔊 AI応答音声**")
                # 音声プレーヤー表示
                st.audio(st.session_state["last_ai_audio"], format="audio/mp3")
                # 自動再生
                autoplay_audio(st.session_state["last_ai_audio"])
                # 再生後に削除（重複再生防止）
                del st.session_state["last_ai_audio"]
        else:
            st.info("ウイルスが検知されると、ここにAIチャットが表示されます。")


    # 入力エリア（感染時のみ）
    if st.session_state.infected:
        st.markdown("### 💬 入力方法")
        input_col1, input_col2 = st.columns(2)

        with input_col1:
            st.info("📝 **テキスト入力**: 下のチャット欄にメッセージを入力")

        with input_col2:
            st.info("🎙️ **音声入力**: 録音ボタンをクリックして話す")

        # 音声録音
        _, col_audio = st.columns([3, 1])
        with col_audio:
            audio_bytes = audio_recorder(
                text="録音開始",
                recording_color="#e74c3c",
                neutral_color="#27AE60",
                icon_name="fa-microphone",
                icon_size="3x",
                pause_threshold=2.0,
                sample_rate=44100,
                key="audio_recorder"
            )

            # 音声入力の処理
            if audio_bytes and not st.session_state.ai_responding:
                audio_hash = hash_audio(audio_bytes)
                if audio_hash != st.session_state.last_audio_hash:
                    st.session_state.last_audio_hash = audio_hash

                    with st.spinner("🎧 音声を認識中..."):
                        text = speech_to_text(audio_bytes)
                        if text:
                            st.success(f"認識結果: {text}")
                            st.session_state.chat.append({"sender": "user", "text": text})
                            st.session_state.ai_responding = True
                            st.rerun()
                        else:
                            st.error("音声の認識に失敗しました。もう一度お試しください。")

        # テキスト入力
        if prompt := st.chat_input("メッセージを入力...", disabled=st.session_state.ai_responding):
            st.session_state.chat.append({"sender": "user", "text": prompt})
            st.session_state.ai_responding = True
            st.rerun()

        # AI応答の処理
        if st.session_state.ai_responding and st.session_state.chat and st.session_state.chat[-1]["sender"] == "user":
            with right_col:
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    audio_segments = []
                    sentence_buffer = ""

                    # ストリーミング応答
                    for chunk in get_ai_response(st.session_state.chat):
                        full_response += chunk
                        sentence_buffer += chunk
                        response_placeholder.markdown(full_response + "▌")

                        # 文の終わりを検出して音声生成
                        for end_mark in ["。", "！", "？", "\n"]:
                            if end_mark in sentence_buffer:
                                idx = sentence_buffer.index(end_mark) + len(end_mark)
                                sentence = sentence_buffer[:idx].strip()
                                sentence_buffer = sentence_buffer[idx:]

                                if sentence:
                                    # 音声生成（後でまとめて再生）
                                    audio_segments.append(sentence)
                                break

                    # 残りのテキストを処理
                    if sentence_buffer.strip():
                        audio_segments.append(sentence_buffer.strip())

                    response_placeholder.markdown(full_response)
                    st.session_state.chat.append({"sender": "ai", "text": full_response})

                    st.session_state.ai_responding = False

                    # AIの応答音声を生成して保存
                    if full_response:
                        ai_audio = text_to_speech(full_response)
                        if ai_audio:
                            st.session_state["last_ai_audio"] = ai_audio

                    st.rerun()

if __name__ == "__main__":
    main()
