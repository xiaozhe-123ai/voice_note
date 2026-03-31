# ==============================================
# 项目：AI语音便签工具
# 开发工具：PyCharm
# 调用能力：百度语音识别 + 百度语音合成
# 姓名：肖哲
# 学号：423830134
# ==============================================

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import requests
import wave
import os

# 百度API密钥（已填写）
API_KEY = "AUNtaJi5VtS5kwxQR2Q2b7pC"
SECRET_KEY = "GzdlGYKlTgoAyi5RxzwsX4YRM5Yky7ye"

# 百度API地址
TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
ASR_URL = "https://vop.baidu.com/server_api"
TTS_URL = "https://tsn.baidu.com/text2audio"

class VoiceNoteApp:
    def __init__(self, root):
        # 所有实例属性统一在__init__中声明，消除报错
        self.root = root
        self.root.title("AI语音便签 - 肖哲 423830134")
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        # 预声明所有实例变量
        self.token = None
        self.audio = None
        self.stream = None
        self.recording = False
        self.frames = []
        self.audio_path = None
        self.tts_data = None
        self.tab1 = None
        self.tab2 = None
        self.text1 = None
        self.text2 = None

        # 获取API令牌
        self.token = self.get_token()
        if not self.token:
            messagebox.showerror("错误", "获取API令牌失败，请检查网络或密钥！")
            self.root.destroy()
            return

        # 初始化音频（pyaudio可选，无则提示安装）
        try:
            import pyaudio
            self.audio = pyaudio.PyAudio()
        except ImportError:
            messagebox.showwarning("依赖缺失", "未安装pyaudio，录音功能不可用，仅可使用上传音频/文字转语音功能")

        # 创建界面
        self.create_ui()

    def get_token(self):
        """获取百度API access_token"""
        try:
            res = requests.get(TOKEN_URL, params={
                "grant_type": "client_credentials",
                "client_id": API_KEY,
                "client_secret": SECRET_KEY
            }, timeout=10)
            res.raise_for_status()
            result = res.json()
            return result.get("access_token")
        except Exception as e:
            print(f"获取token失败：{str(e)}")
            return None

    def create_ui(self):
        """创建GUI界面"""
        tab_control = ttk.Notebook(self.root)
        self.tab1 = ttk.Frame(tab_control)
        self.tab2 = ttk.Frame(tab_control)
        tab_control.add(self.tab1, text="语音转文字")
        tab_control.add(self.tab2, text="文字转语音")
        tab_control.pack(expand=1, fill="both", padx=10, pady=10)

        # ========== 标签页1：语音转文字 ==========
        btn_frame1 = ttk.Frame(self.tab1)
        btn_frame1.pack(pady=5)
        ttk.Button(btn_frame1, text="开始录音", command=self.start_record).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame1, text="停止录音", command=self.stop_record).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame1, text="上传音频", command=self.upload_audio).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame1, text="开始识别", command=self.recognize_audio).grid(row=0, column=3, padx=5)

        tk.Label(self.tab1, text="识别结果：").pack(pady=5)
        self.text1 = scrolledtext.ScrolledText(self.tab1, width=70, height=12, font=("微软雅黑", 10))
        self.text1.pack(pady=5)

        # ========== 标签页2：文字转语音 ==========
        tk.Label(self.tab2, text="输入文字：").pack(pady=5)
        self.text2 = scrolledtext.ScrolledText(self.tab2, width=70, height=10, font=("微软雅黑", 10))
        self.text2.pack(pady=5)

        btn_frame2 = ttk.Frame(self.tab2)
        btn_frame2.pack(pady=5)
        ttk.Button(btn_frame2, text="朗读语音", command=self.text_to_speech).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame2, text="保存语音", command=self.save_audio).grid(row=0, column=1, padx=5)

    def start_record(self):
        """开始录音"""
        if not self.audio:
            messagebox.showerror("错误", "未安装pyaudio，无法使用录音功能！")
            return
        if self.recording:
            return
        self.recording = True
        self.frames = []
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        self.record_loop()
        messagebox.showinfo("提示", "正在录音...")

    def record_loop(self):
        """录音循环"""
        if self.recording:
            data = self.stream.read(1024)
            self.frames.append(data)
            self.root.after(10, self.record_loop)

    def stop_record(self):
        """停止录音并保存"""
        if not self.recording:
            return
        self.recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None

        # 保存为WAV格式
        self.audio_path = "record.wav"
        with wave.open(self.audio_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b"".join(self.frames))
        messagebox.showinfo("完成", "录音已保存！")

    def upload_audio(self):
        """上传本地WAV音频"""
        path = filedialog.askopenfilename(filetypes=[("WAV音频文件", "*.wav")])
        if path:
            self.audio_path = path
            messagebox.showinfo("完成", f"已选择音频：{os.path.basename(path)}")

    def recognize_audio(self):
        """调用百度语音识别API"""
        if not self.audio_path or not os.path.exists(self.audio_path):
            messagebox.showwarning("提示", "请先录音或上传音频文件！")
            return

        try:
            with open(self.audio_path, "rb") as f:
                audio_data = f.read()

            params = {
                "dev_pid": 1537,
                "cuid": "voice_note_423830134",
                "token": self.token,
                "len": len(audio_data),
                "rate": 16000,
                "format": "wav",
                "channel": 1
            }
            res = requests.post(ASR_URL, params=params, data=audio_data, timeout=10)
            res.raise_for_status()
            result = res.json()

            if result.get("err_no") == 0:
                text = "\n".join(result.get("result", []))
                self.text1.insert(tk.END, text + "\n\n")
                messagebox.showinfo("成功", "语音识别完成！")
            else:
                messagebox.showerror("识别失败", f"错误信息：{result.get('err_msg')}")
        except Exception as e:
            messagebox.showerror("错误", f"识别异常：{str(e)}")

    def text_to_speech(self):
        """调用百度语音合成API"""
        text = self.text2.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "请输入要朗读的文字！")
            return
        if len(text) > 1024:
            messagebox.showwarning("提示", "文本长度不能超过1024字符！")
            return

        try:
            params = {
                "tex": text,
                "tok": self.token,
                "cuid": "voice_note_423830134",
                "ctp": 1,
                "lan": "zh",
                "spd": 5,
                "pit": 5,
                "vol": 5,
                "per": 0
            }
            res = requests.get(TTS_URL, params=params, timeout=10)
            res.raise_for_status()

            if res.headers.get("Content-Type") == "audio/mp3":
                self.tts_data = res.content
                # 临时保存并播放
                with open("temp_tts.mp3", "wb") as f:
                    f.write(self.tts_data)
                os.startfile("temp_tts.mp3")
                messagebox.showinfo("成功", "语音朗读中！")
            else:
                result = res.json()
                messagebox.showerror("合成失败", f"错误信息：{result.get('err_msg')}")
        except Exception as e:
            messagebox.showerror("错误", f"合成异常：{str(e)}")

    def save_audio(self):
        """保存语音为MP3"""
        if not self.tts_data:
            messagebox.showwarning("提示", "请先生成语音！")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3音频文件", "*.mp3")]
        )
        if path:
            with open(path, "wb") as f:
                f.write(self.tts_data)
            messagebox.showinfo("成功", f"语音已保存到：{path}")

    def __del__(self):
        """释放音频资源"""
        if self.audio:
            self.audio.terminate()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceNoteApp(root)
    root.mainloop()