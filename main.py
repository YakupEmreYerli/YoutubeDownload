import customtkinter as ctk
import os
import threading
import re
import ctypes  # Windows bildirimleri için
from pathlib import Path
from yt_dlp import YoutubeDL
from tkinter import messagebox

# App Configuration
ctk.set_appearance_mode("Dark")
ACCENT_COLOR = "#404b62"
ACCENT_HOVER = "#4d5b78"
BG_COLOR = "#242424"
ENTRY_BG = "#2b2b2b"
TEXT_COLOR = "#ffffff"
SECONDARY_TEXT = "#bbbbbb"

class YoutubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Config
        self.title("YouTube İndirici Pro")
        self.geometry("620x420") 
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        # Layout Grid Config
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="YouTube Çoklu İndirici", 
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        # Main Input Frame
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        # URL Entry - Width adjusted to prevent overlap
        self.url_entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="YouTube Linkini Girin", 
            height=45,
            width=320,
            fg_color=ENTRY_BG,
            border_color="#3f3f3f",
            text_color="white"
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 2))

        # Quality Selection - Width fixed and padded slightly
        self.qualities = [
            "MP4 - Otomatik (1080p)",
            "MP4 - 2160p 4K",
            "MP4 - 1440p 2K",
            "MP4 - 1080p Full HD",
            "MP4 - 720p HD",
            "MP4 - 480p SD",
            "MP3 - Sadece Ses"
        ]
        self.quality_var = ctk.StringVar(value=self.qualities[0])
        self.quality_dropdown = ctk.CTkComboBox(
            self.input_frame, 
            values=self.qualities, 
            variable=self.quality_var,
            width=200, 
            height=45,
            fg_color=ENTRY_BG,
            button_color=ACCENT_COLOR,
            button_hover_color=ACCENT_HOVER,
            border_color="#444444",
            dropdown_fg_color=ENTRY_BG,
            dropdown_hover_color=ACCENT_COLOR
        )
        self.quality_dropdown.grid(row=0, column=1, padx=(0, 2))

        # Download Button - Smaller Enter Icon (⏎)
        self.download_btn = ctk.CTkButton(
            self.input_frame, 
            text="⏎",
            command=self.start_download_thread, 
            height=45, 
            width=50,
            font=ctk.CTkFont(size=20, weight="bold"), # Slightly smaller for better look
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color="#ffffff"
        )
        self.download_btn.grid(row=0, column=2, padx=0)

        # Status & Progress
        self.status_label = ctk.CTkLabel(self, text="Hazır", text_color=SECONDARY_TEXT, font=ctk.CTkFont(size=13, weight="bold"))
        self.status_label.grid(row=2, column=0, padx=20, pady=(20, 5))
        
        self.progress_bar = ctk.CTkProgressBar(
            self, 
            width=580, 
            progress_color=ACCENT_COLOR,
            fg_color="#333333"
        )
        self.progress_bar.grid(row=3, column=0, padx=20, pady=(0, 30))
        self.progress_bar.set(0)

        self._is_running = True

    def on_closing(self):
        self._is_running = False
        self.destroy()

    def start_download_thread(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Hata", "Lütfen bir YouTube linki girin.")
            return
        
        self.download_btn.configure(state="disabled", text="...")
        self.status_label.configure(text="İşlem başlıyor...", text_color=ACCENT_COLOR)
        self.progress_bar.set(0)
        
        thread = threading.Thread(target=self.download_content, args=(url,), daemon=True)
        thread.start()

    def progress_hook(self, d):
        if not self._is_running: return
        
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                
                if total:
                    percentage = downloaded / total
                    percent_str = f"{percentage*100:.1f}"
                else:
                    percent_raw = d.get('_percent_str', '100%')
                    percent_clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', percent_raw)
                    percentage = float(percent_clean.replace('%', '').strip()) / 100
                    percent_str = f"{percentage*100:.1f}"

                speed_raw = d.get('_speed_str', '0KB/s').strip()
                speed_clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', speed_raw)
                speed = speed_clean.replace('iB/s', ' MB').replace('B/s', ' B')
                
                self.after(0, lambda p=percentage, s=speed, ps=percent_str: 
                           self.update_progress(p, f"%{ps}   İndirme Hızı: {s}"))
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.after(0, lambda: self.update_progress(1.0, "Uzantı Değiştiriliyor... FFmpeg Aktif", "#2ecc71"))

    def update_progress(self, value, status_text, color="#aaaaaa"):
        if not self._is_running: return
        self.status_label.configure(text=status_text, text_color=color)
        self.progress_bar.set(value)

    def download_content(self, url):
        quality_choice = self.quality_var.get()
        output_path = str(Path.home() / "Downloads")
        
        format_str = "best"
        is_audio = False

        if "2160p" in quality_choice:
            format_str = "bestvideo[height<=2160]+bestaudio/best"
        elif "1440p" in quality_choice:
            format_str = "bestvideo[height<=1440]+bestaudio/best"
        elif "1080p" in quality_choice:
            format_str = "bestvideo[height<=1080]+bestaudio/best"
        elif "720p" in quality_choice:
            format_str = "bestvideo[height<=720]+bestaudio/best"
        elif "480p" in quality_choice:
            format_str = "bestvideo[height<=480]+bestaudio/best"
        elif "Ses" in quality_choice:
            is_audio = True
            format_str = "bestaudio/best"

        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'noplaylist': True,
            'ffmpeg_location': 'C:/ffmpeg/bin',
            'no_color': True,
            'format': format_str,
        }

        if is_audio:
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts.update({'merge_output_format': 'mp4'})

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if self._is_running:
                self.after(0, lambda: self.finish_download(True))
        except Exception as e:
            error_text = str(e)
            if self._is_running:
                self.after(0, lambda msg=error_text: self.finish_download(False, msg))

    def finish_download(self, success, error_msg=""):
        if not self._is_running: return
        self.download_btn.configure(state="normal", text="⏎")
        if success:
            self.status_label.configure(text="Başarıyla Tamamlandı!", text_color="#2ecc71")
            # Windows Görev Çubuğu Bildirimi (Yanıp Sönme)
            try:
                if os.name == 'nt':
                    # HWND'yi alalım (winfo_id Windows'ta HWND'dir)
                    hwnd = self.winfo_id()
                    
                    # FLASHWINFO yapısı
                    class FLASHWINFO(ctypes.Structure):
                        _fields_ = [
                            ('cbSize', ctypes.c_uint),
                            ('hwnd', ctypes.c_void_p),
                            ('dwFlags', ctypes.c_uint),
                            ('uCount', ctypes.c_uint),
                            ('dwTimeout', ctypes.c_uint)
                        ]
                    
                    # dwFlags Sabitleri: FLASHW_TRAY | FLASHW_TIMERNOFG (Pencere odağa gelene kadar yanıp sön)
                    FLASHW_TRAY = 0x00000002
                    FLASHW_TIMERNOFG = 0x0000000C
                    
                    info = FLASHWINFO(
                        cbSize=ctypes.sizeof(FLASHWINFO),
                        hwnd=hwnd,
                        dwFlags=FLASHW_TRAY | FLASHW_TIMERNOFG,
                        uCount=0,
                        dwTimeout=0
                    )
                    ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))
            except Exception as e:
                print(f"Bildirim Hatası: {e}")
        else:
            self.status_label.configure(text="Hata Oluştu.", text_color="#e74c3c")
            messagebox.showerror("Hata", f"İndirme başarısız!")

if __name__ == "__main__":
    app = YoutubeDownloaderApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
