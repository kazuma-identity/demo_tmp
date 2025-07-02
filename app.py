# app.py  ── ウイルス検知デモ（Streamlit + OpenAI）Streaming 対応版
import streamlit as st
import os, hashlib, base64
from io import BytesIO
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

# ── 0. 環境準備 ─────────────────────────────────────────────
load_dotenv()
st.set_page_config("ウイルス検知デモ", "🦠", layout="wide")

# ── 1. ユーティリティ ─────────────────────────────────────
def get_client() -> OpenAI:               # key は env(OPENAI_API_KEY) を自動読込
    return OpenAI()

def md5(b: bytes) -> str:                 # 音声の重複送信防止用
    return hashlib.md5(b).hexdigest()

def autoplay_audio(mp3: bytes):
    if not mp3: return
    b64 = base64.b64encode(mp3).decode()
    st.markdown(f"""
        <audio autoplay>
          <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>""", unsafe_allow_html=True)

def text_to_speech(text: str) -> bytes | None:
    try:
        return get_client().audio.speech.create(
            model="tts-1", voice="nova",
            input=text, response_format="mp3").content
    except Exception as e:
        st.warning(f"TTS エラー: {e}")
        return None

def speech_to_text(wav: bytes) -> str | None:
    try:
        buf = BytesIO(wav); buf.name = "audio.wav"
        return get_client().audio.transcriptions.create(
            model="whisper-1", file=buf, language="ja").text
    except Exception as e:
        st.warning(f"STT エラー: {e}")
        return None

def get_ai_stream(history):
    system_prompt = (
        "あなたはCSIRT（Computer Security Incident Response Team）のAIアシスタントです。"
        "ウイルス感染が検知された端末のユーザーへ冷静かつ的確な初動対応を案内してください。"
    )
    msgs = [{"role": "system", "content": system_prompt}]
    for m in history[-10:]:
        role = "user" if m["sender"] == "user" else "assistant"
        msgs.append({"role": role, "content": m["text"]})
    client = get_client()
    for chunk in client.chat.completions.create(
            model="gpt-4o", messages=msgs, stream=True):
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# ── 2. セッション初期化 ────────────────────────────────────
defaults = dict(
    logged_in=False, infected=False, chat=[],
    ai_responding=False, last_audio_hash="", initial_message_sent=False,
    last_ai_audio=None)
for k, v in defaults.items(): st.session_state.setdefault(k, v)

# ── 3. ログイン画面 ───────────────────────────────────────
def login_page():
    st.markdown("<h1 style='text-align:center'>🦠 ウイルス検知デモシステム</h1>", unsafe_allow_html=True)
    with st.form("login", border=False):
        u = st.text_input("ユーザー名"); p = st.text_input("パスワード", type="password")
        if st.form_submit_button("ログイン"):
            if (u, p) == ("aice", "aice"):
                st.session_state.logged_in = True; st.rerun()
            else: st.error("認証失敗")

if not st.session_state.logged_in:
    login_page(); st.stop()

# ── 4. ヘッダー ───────────────────────────────────────────
left, mid, right = st.columns([2,1,1])
with left:  st.title("🦠 ウイルス検知デモシステム")
with mid:
    if st.button("🦠 ウイルス発生", disabled=st.session_state.infected):
        st.session_state.infected = True
        st.session_state.initial_message_sent = False
        st.rerun()
with right:
    col_r1, col_r2 = st.columns(2)
    if col_r1.button("🔄 Reset"):
        logged = st.session_state.logged_in
        st.session_state.clear(); st.session_state.logged_in = logged
        st.rerun()
    if col_r2.button("🚪 ログアウト"):
        st.session_state.logged_in = False; st.rerun()

# ── 5. 状態バー ───────────────────────────────────────────
if st.session_state.infected:
    st.error("🔴 感染対応モード（ネット遮断中）")
else:
    st.success("✅ 正常稼働")

st.divider()

# ── 6. 初期メッセージ & 音声 ──────────────────────────────
if st.session_state.infected and not st.session_state.initial_message_sent:
    sys_msg = "【システム通知】セキュリティ脅威を検出したため端末をネットワークから遮断しました。"
    ai_msg  = "こんにちは。CSIRT AIです。状況を確認します。何か異常に気付きましたか？"
    st.session_state.chat += [
        {"sender": "system", "text": sys_msg},
        {"sender": "ai",     "text": ai_msg}]
    st.session_state.initial_message_sent = True
    if audio := text_to_speech(ai_msg):
        st.session_state.last_ai_audio = audio

# ── 7. 端末カード & チャット表示 ──────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.subheader("端末A")
    if st.session_state.infected:
        st.error("🔴 Disconnected")
    else:
        st.success("🟢 Healthy")

with col_r:
    st.subheader("端末B (CSIRT AI)")
    for m in st.session_state.chat:
        if m["sender"] == "ai":
            st.chat_message("assistant").write(m["text"])
        elif m["sender"] == "user":
            st.chat_message("user").write(m["text"])
        else:
            st.info(m["text"])
    # 直近 AI 音声を自動再生
    if st.session_state.last_ai_audio:
        autoplay_audio(st.session_state.last_ai_audio)
        st.session_state.last_ai_audio = None

# ── 8. 入力インターフェース ─────────────────────────────
if st.session_state.infected:
    prompt = st.chat_input("メッセージを入力…", disabled=st.session_state.ai_responding)

    # 音声録音
    audio_blob = audio_recorder(
        text="録音開始", recording_color="#e74c3c", neutral_color="#27AE60",
        pause_threshold=2.0, sample_rate=16000, key="mic")

    # 音声 to テキスト
    if audio_blob and md5(audio_blob) != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = md5(audio_blob)
        if text := speech_to_text(audio_blob):
            st.session_state.chat.append({"sender": "user", "text": text})
            st.session_state.ai_responding = True
            st.rerun()

    # テキスト送信
    if prompt:
        st.session_state.chat.append({"sender": "user", "text": prompt})
        st.session_state.ai_responding = True
        st.rerun()

# ── 9. AI 応答ストリーミング描画 ─────────────────────────
if st.session_state.ai_responding and st.session_state.chat[-1]["sender"] == "user":
    with col_r:
        assistant_msg = st.chat_message("assistant")

        # ストリーム → 画面 & TTS
        def stream():
            buf = ""
            for tok in get_ai_stream(st.session_state.chat):
                buf += tok
                yield tok
            if audio := text_to_speech(buf):
                st.session_state.last_ai_audio = audio
                autoplay_audio(audio)
            # チャット履歴へ追加
            st.session_state.chat.append({"sender": "ai", "text": buf})
            st.session_state.ai_responding = False

        assistant_msg.write_stream(stream())

# ── 10. 実行 ──────────────────────────────────────────────
if __name__ == "__main__":
    pass  # Streamlit は import 時に実行される
