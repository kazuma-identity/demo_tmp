#!/usr/bin/env python3
"""
音声機能検証スクリプト
OpenAI APIのTTS（テキスト読み上げ）機能をテストします。
"""

import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import pygame
import time

# .envファイルを読み込み
load_dotenv()

def test_api_connection():
    """API接続テスト"""
    print("=== API接続テスト ===")
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if not api_key:
        print("❌ エラー: OPENAI_API_KEYが設定されていません")
        return None
    
    if not api_key.startswith("sk-"):
        print("❌ エラー: API キーの形式が正しくありません")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        print("✅ API接続成功")
        return client
    except Exception as e:
        print(f"❌ API接続エラー: {e}")
        return None

def test_tts(client, text="これは音声テストです。正常に聞こえていますか？"):
    """TTS（音声合成）テスト"""
    print("\n=== TTS（音声合成）テスト ===")
    print(f"テキスト: {text}")
    
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="mp3"
        )
        
        audio_data = response.content
        print(f"✅ 音声生成成功: {len(audio_data)} bytes")
        
        # 音声ファイルを保存
        audio_file = "test_audio.mp3"
        with open(audio_file, "wb") as f:
            f.write(audio_data)
        print(f"✅ 音声ファイル保存: {audio_file}")
        
        return audio_file
    
    except Exception as e:
        print(f"❌ TTS エラー: {type(e).__name__}: {str(e)}")
        return None

def play_audio_pygame(audio_file):
    """Pygameで音声を再生"""
    print("\n=== Pygame音声再生テスト ===")
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        print("🔊 音声再生中...")
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        print("✅ 音声再生完了")
        pygame.mixer.quit()
        return True
        
    except Exception as e:
        print(f"❌ 再生エラー: {e}")
        return False

def play_audio_system(audio_file):
    """システムコマンドで音声を再生"""
    print("\n=== システムコマンド音声再生テスト ===")
    try:
        if sys.platform == "win32":
            os.system(f'start "" "{audio_file}"')
        elif sys.platform == "darwin":  # macOS
            os.system(f'afplay "{audio_file}"')
        else:  # Linux
            os.system(f'xdg-open "{audio_file}"')
        
        print("✅ システムプレーヤーで再生を開始しました")
        return True
    except Exception as e:
        print(f"❌ システム再生エラー: {e}")
        return False

def test_multiple_sentences(client):
    """複数文の連続音声生成テスト"""
    print("\n=== 複数文の連続音声生成テスト ===")
    sentences = [
        "こんにちは、CSIRT AIです。",
        "ウイルスが検出されました。",
        "落ち着いて対応してください。"
    ]
    
    audio_files = []
    for i, sentence in enumerate(sentences):
        print(f"\n文 {i+1}: {sentence}")
        try:
            response = client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=sentence,
                response_format="mp3"
            )
            
            filename = f"test_sentence_{i+1}.mp3"
            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"✅ 生成成功: {filename} ({len(response.content)} bytes)")
            audio_files.append(filename)
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    return audio_files

def main():
    """メイン処理"""
    print("OpenAI TTS 音声機能検証スクリプト")
    print("=" * 50)
    
    # 1. API接続テスト
    client = test_api_connection()
    if not client:
        print("\n❌ API接続に失敗しました。.envファイルを確認してください。")
        return
    
    # 2. 単一音声生成テスト
    audio_file = test_tts(client)
    if audio_file:
        # Pygameで再生を試す
        if not play_audio_pygame(audio_file):
            # 失敗したらシステムプレーヤーで再生
            play_audio_system(audio_file)
    
    # 3. 複数文テスト
    print("\n複数文のテストを実行しますか？ (y/n): ", end="")
    if input().lower() == 'y':
        audio_files = test_multiple_sentences(client)
        print(f"\n✅ {len(audio_files)}個の音声ファイルを生成しました")
        
        # 連続再生
        print("\n連続再生しますか？ (y/n): ", end="")
        if input().lower() == 'y':
            pygame.mixer.init()
            for i, file in enumerate(audio_files):
                print(f"\n🔊 再生中 {i+1}/{len(audio_files)}: {file}")
                pygame.mixer.music.load(file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            pygame.mixer.quit()
    
    # 4. 環境情報
    print("\n=== 環境情報 ===")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working Directory: {os.getcwd()}")
    
    # 5. Streamlitでの使用方法
    print("\n=== Streamlitでの音声再生 ===")
    print("Streamlitでは以下の方法で音声を再生できます：")
    print("1. st.audio() - 音声プレーヤーを表示")
    print("2. HTML <audio> タグ with autoplay - 自動再生")
    print("3. JavaScript Audio API - より詳細な制御")
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    main()