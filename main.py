import wave
import os
from funasr import AutoModel
import speech_recognition as sr
import dashscope
from dashscope.audio.tts_v2 import *
import pygame
import threading
import json
import requests
from datetime import datetime

# 加载语音识别模型
model = AutoModel(model="paraformer-zh")

# 聊天记录存储
CHAT_HISTORY_FILE = "chat_history.json"

def load_chat_history(limit=10):
    """加载最近limit次聊天记录"""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
        # 获取最近limit次对话
        return history[-limit:] if len(history) > limit else history
    return []

def save_chat_history(user_input, bot_response):
    """保存聊天记录到JSON文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_entry = {
        "timestamp": timestamp,
        "user": user_input,
        "bot": bot_response
    }
    
    # 读取现有历史记录
    history = []
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    # 添加新记录
    history.append(history_entry)
    
    # 保存更新后的历史记录
    with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_local_llm_response(user_input, max_tokens=1000):
    """调用本地OpenAI格式的大模型，包含最近10次聊天记录"""
    try:
        url = "http://127.0.0.1:3333/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        
        # 加载最近10次聊天记录
        chat_history = load_chat_history(limit=10)
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": "你是一个助手小爱，请根据用户的输入和聊天记录给出亲切的回复，称呼用户为主人。"}
        ]
        
        # 将历史记录加入消息列表
        for entry in chat_history:
            messages.append({"role": "user", "content": entry["user"]})
            messages.append({"role": "assistant", "content": entry["bot"]})
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        data = {
            "model": "local-model",  # 根据你的本地模型名称调整
            "messages": messages,
            "max_tokens": max_tokens
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=3000)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"调用本地大模型时出错: {e}")
        return "抱歉，主人，暂时无法获取回复，请稍后再试。"

def play_audio(audio_path):
    """播放音频文件"""
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()
    pygame.mixer.quit()

def wake_word_detection():
    r = sr.Recognizer()
    
    # 指定输出目录
    output_directory = os.path.join(os.getcwd(), "voices")
    os.makedirs(output_directory, exist_ok=True)

    # 配置DashScope API Key
    dashscope.api_key = "sk-4bed2f0173bb480983147da6e4af8589"

    with sr.Microphone() as source:
        print("请说出唤醒词...")
        while True:
            audio = r.listen(source)
            try:
                # 保存音频
                audio_file_path = os.path.join(output_directory, "myvoices.wav")
                with open(audio_file_path, "wb") as f:
                    f.write(audio.get_wav_data())
                print(f"音频已保存到: {audio_file_path}")

                # 语音识别
                command = model.generate(input=audio_file_path)
                print("识别结果:", command)

                if command and isinstance(command, list) and len(command) > 0 and "text" in command[0]:
                    recognized_text = command[0]["text"]
                    print("识别结果2:", recognized_text)
                    
                    if "小 爱" in recognized_text:
                        response_text = "检测到了！正在处理您的请求..."
                        print("提示:", response_text)
                        # 使用本地大模型获取回复，包含聊天记录
                        llm_response = get_local_llm_response(recognized_text)
                        
                        # 保存聊天记录
                        save_chat_history(recognized_text, llm_response)
                        
                        # 语音合成
                        vmodel = "cosyvoice-v2"
                        voice = "longxiaochun_v2"
                        synthesizer = SpeechSynthesizer(model=vmodel, voice=voice)
                        audio = synthesizer.call(llm_response)
                        
                        print('[Metric] requestId: {}, first package delay ms: {}'.format(
                            synthesizer.get_last_request_id(),
                            synthesizer.get_first_package_delay()))
                        
                        # 保存合成音频
                        audio_file_path2 = os.path.join(output_directory, "output.mp3")
                        with open(audio_file_path2, 'wb') as f:
                            f.write(audio)
                        
                        # 播放音频
                        audio_thread = threading.Thread(target=play_audio, args=(audio_file_path2,))
                        audio_thread.start()
                    else:
                        response_text = f"你说了：{recognized_text}，但没有检测到唤醒词‘小爱’。"
                        print("提示:", response_text)
                       
                else:
                    response_text = "未能识别音频内容。"
                    print("提示:", response_text)
                    
            except sr.UnknownValueError:
                print("未能理解音频")
            except sr.RequestError as e:
                print(f"无法请求结果; {e}")
            except Exception as e:
                print(f"发生错误: {e}")

if __name__ == "__main__":
    wake_word_detection()