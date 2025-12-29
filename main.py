import customtkinter as ctk
import os
import threading
import re
import ctypes
from pathlib import Path
from yt_dlp import YoutubeDL
from tkinter import messagebox
from plyer import notification

import sys

# ... (imports)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- PREMIUM MINIMALIST DESIGN ---
ctk.set_appearance_mode("Dark")
THEME = {
    "bg": "#0B0E14",         
    "accent": "#0095FF",     
    "accent_sub": "#0077CC", 
    "text_main": "#E1E7EF", 
    "text_dim": "#718096",
    "success": "#22C55E",
    "error": "#EF4444",
    "input_bg": "#151921",
    "button_dark": "#1E232E"
}

class YoutubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Youtube Downloader")
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        self.geometry("750x520")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg"])
        
        # Center grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main Container (Centered)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure((0, 4), weight=1) # Spacer top/bottom

        # 1. Header Section
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(20, 40))
        
        self.header_label = ctk.CTkLabel(
            self.header_frame, 
            text="Youtube Downloader", 
            font=ctk.CTkFont(family="Arial", size=32, weight="bold"),
            text_color=THEME["accent"]
        )
        self.header_label.pack()
        
        self.subheader_label = ctk.CTkLabel(
            self.header_frame, 
            text="", 
            font=ctk.CTkFont(family="Arial", size=13, weight="normal"),
            text_color=THEME["text_dim"]
        )
        self.subheader_label.pack(pady=(2, 0))

        # 2. Input Section
        self.input_parent = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_parent.grid(row=1, column=0, sticky="ew", padx=60)
        self.input_parent.grid_columnconfigure(0, weight=1)

        # URL Entry
        self.url_entry = ctk.CTkEntry(
            self.input_parent, 
            placeholder_text="YouTube video bağlantısını yapıştırın...", 
            height=54, 
            fg_color=THEME["input_bg"], 
            border_color="#2D333B", 
            border_width=1,
            corner_radius=14,
            font=ctk.CTkFont(size=14),
            placeholder_text_color=THEME["text_dim"],
            text_color=THEME["text_main"]
        )
        self.url_entry.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        # Controls Row
        self.controls_frame = ctk.CTkFrame(self.input_parent, fg_color="transparent")
        self.controls_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.controls_frame.grid_columnconfigure((0, 1), weight=1) # Equal split

        # Quality Select
        self.qualities = ["Otomatik (1080p)", "2160p 4K", "1440p 2K", "1080p FHD", "720p HD", "480p SD", "MP3 Sadece Ses"]
        self.quality_var = ctk.StringVar(value=self.qualities[0])
        self.quality_menu = ctk.CTkComboBox(
            self.controls_frame, 
            values=self.qualities, 
            variable=self.quality_var,
            height=50, 
            fg_color=THEME["input_bg"],
            border_color="#2D333B",
            button_color=THEME["button_dark"],
            button_hover_color=THEME["accent_sub"],
            border_width=1,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13),
            dropdown_fg_color=THEME["input_bg"],
            dropdown_hover_color=THEME["button_dark"],
            text_color=THEME["text_main"]
        )
        self.quality_menu.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        # Action Button
        self.go_btn = ctk.CTkButton(
            self.controls_frame, 
            text="İndirmeyi Başlat", 
            command=self.start_download_thread, 
            height=50, 
            fg_color=THEME["accent"], 
            hover_color=THEME["accent_sub"], 
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=12,
            text_color="#FFFFFF"
        )
        self.go_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        # 3. Status Section
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, pady=(40, 0))
        
        self.status = ctk.CTkLabel(
            self.status_frame, 
            text="İndirme yapmak için hazırım", 
            font=ctk.CTkFont(size=13), 
            text_color=THEME["text_dim"]
        )
        self.status.pack(pady=(0, 10))
        
        self.bar = ctk.CTkProgressBar(
            self.status_frame, 
            width=500, 
            height=6, 
            progress_color=THEME["accent"], 
            fg_color=THEME["button_dark"], 
            corner_radius=3
        )
        self.bar.pack()
        self.bar.set(0)

        self._alive = True


    # --- LOGIC ---

    def start_download_thread(self):
        url = self.url_entry.get()
        if not url: return
        self.go_btn.configure(state="disabled", text="İşleniyor...")
        self.status.configure(text="Bağlantı analiz ediliyor...", text_color=THEME["accent"])
        self.bar.set(0)
        threading.Thread(target=self.download_core, args=(url,), daemon=True).start()

    def progress_hook(self, d):
        if not self._alive: return
        if d['status'] == 'downloading':
            try:
                tot = d.get('total_bytes') or d.get('total_bytes_estimate')
                cur = d.get('downloaded_bytes', 0)
                p = cur / (tot if tot else 1)
                sp_raw = d.get('_speed_str', '0KB/s').strip()
                sp = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', sp_raw).replace('iB/s', ' MB')
                pct = f"{p*100:.1f}"
                self.after(0, lambda v=p, t=f"%{pct}  •  {sp}": self.update_ui(v, t))
            except: pass
        elif d['status'] == 'finished':
            self.after(0, lambda: self.update_ui(1.0, "Dönüştürme işlemi yapılıyor...", THEME["success"]))

    def update_ui(self, val, txt, color=None):
        if not color: color = THEME["text_dim"]
        self.bar.set(val)
        self.status.configure(text=txt, text_color=color)

    def download_core(self, url):
        qual = self.quality_var.get()
        out_path = str(Path.home() / "Downloads")
        
        fmt = "best"
        audio_only = "Ses" in qual
        if "2160p" in qual: fmt = "bestvideo[height<=2160]+bestaudio/best"
        elif "1440p" in qual: fmt = "bestvideo[height<=1440]+bestaudio/best"
        elif "1080p" in qual: fmt = "bestvideo[height<=1080]+bestaudio/best"
        elif "720p" in qual: fmt = "bestvideo[height<=720]+bestaudio/best"
        elif "Ses" in qual: fmt = "bestaudio/best"

        opts = {
            'outtmpl': os.path.join(out_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'ffmpeg_location': 'C:/ffmpeg/bin',
            'no_color': True,
            'format': fmt,
        }

        if audio_only:
            opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}]
        else:
            opts['merge_output_format'] = 'mp4'

        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.after(0, lambda: self.download_done(True))
        except Exception as e:
            self.after(0, lambda msg=str(e): self.download_done(False, msg))

    def download_done(self, success, err=""):
        self.go_btn.configure(state="normal", text="İndirmeyi Başlat")
        if success:
            self.status.configure(text="İndirme Tamamlandı!", text_color=THEME["success"])
            try:
                notification.notify(title='Youtube Downloader', message='Dosya başarıyla indirildi.', timeout=3)
                if os.name == 'nt': ctypes.windll.user32.FlashWindow(self.winfo_id(), True)
            except: pass
        else:
            self.status.configure(text="Hata Oluştu", text_color=THEME["error"])
            messagebox.showerror("Hata", f"İşlem başarısız: {err}")

if __name__ == "__main__":
    app = YoutubeDownloaderApp()
    app.mainloop()
