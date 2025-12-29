
import customtkinter as ctk
import os
import threading
import re
import ctypes
from pathlib import Path
from yt_dlp import YoutubeDL
from tkinter import messagebox
from plyer import notification

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
        self.title("YouTube Professional")
        self.geometry("720x440")
        self.resizable(False, False)
        self.configure(fg_color=THEME["bg"])

        # Main Layout
        self.grid_columnconfigure(0, weight=1)

        # 1. Unified Input Row
        self.input_parent = ctk.CTkFrame(self, fg_color="transparent")
        self.input_parent.grid(row=0, column=0, padx=40, pady=(70, 10), sticky="ew")
        self.input_parent.grid_columnconfigure(0, weight=1)

        # URL Entry
        self.url_entry = ctk.CTkEntry(
            self.input_parent, 
            placeholder_text="Linkinizi buraya bırakın...", 
            height=52, 
            fg_color=THEME["input_bg"], 
            border_color="#2D333B", 
            border_width=1,
            corner_radius=12,
            font=ctk.CTkFont(size=14)
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        # Quality Select (Customized ComboBox for "Filled" feel)
        self.qualities = ["Otomatik (1080p)", "2160p 4K", "1440p 2K", "1080p FHD", "720p HD", "480p SD", "MP3 Sadece Ses"]
        self.quality_var = ctk.StringVar(value=self.qualities[0])
        self.quality_menu = ctk.CTkComboBox(
            self.input_parent, 
            values=self.qualities, 
            variable=self.quality_var,
            width=180, 
            height=52, 
            fg_color=THEME["input_bg"],
            border_color="#2D333B",
            button_color=THEME["accent"],      # İçi boyalı ok alanı
            button_hover_color=THEME["accent_sub"],
            border_width=0,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13),
            dropdown_fg_color=THEME["input_bg"],
            dropdown_hover_color=THEME["accent"]
        )
        self.quality_menu.grid(row=0, column=1, padx=(0, 10))

        # Action Button (Solid Icon: ➤)
        self.go_btn = ctk.CTkButton(
            self.input_parent, 
            text="➤", # Solid-filled arrow icon
            command=self.start_download_thread, 
            height=52, 
            width=65, 
            fg_color=THEME["accent"], 
            hover_color=THEME["accent_sub"], 
            font=ctk.CTkFont(size=20, weight="bold"),
            corner_radius=12
        )
        self.go_btn.grid(row=0, column=2)

        # 3. Status Area
        self.status = ctk.CTkLabel(self, text="Sistem Hazır", font=ctk.CTkFont(size=13), text_color=THEME["text_dim"])
        self.status.grid(row=1, column=0, pady=(15, 8))
        
        self.bar = ctk.CTkProgressBar(self, width=640, height=8, progress_color=THEME["accent"], fg_color="#1E232E", corner_radius=4)
        self.bar.grid(row=2, column=0, pady=(0, 40))
        self.bar.set(0)

        self._alive = True


    # --- LOGIC ---

    def start_download_thread(self):
        url = self.url_entry.get()
        if not url: return
        self.go_btn.configure(state="disabled", text="•")
        self.status.configure(text="İndirme işlemi başlatıldı...", text_color=THEME["accent"])
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
                self.after(0, lambda v=p, t=f"%{pct}  •  İndirme Hızı: {sp}": self.update_ui(v, t))
            except: pass
        elif d['status'] == 'finished':
            self.after(0, lambda: self.update_ui(1.0, "FFmpeg süreci işleniyor...", THEME["success"]))

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
        self.go_btn.configure(state="normal", text="➤")
        if success:
            self.status.configure(text="İŞLEM BAŞARIYLA TAMAMLANDI", text_color=THEME["success"])
            try:
                notification.notify(title='Aura Pro', message='Dosya indirildi!', timeout=3)
                if os.name == 'nt': ctypes.windll.user32.FlashWindow(self.winfo_id(), True)
            except: pass
        else:
            self.status.configure(text="HATA", text_color=THEME["error"])
            messagebox.showerror("Hata", f"İşlem başarısız: {err}")

if __name__ == "__main__":
    app = YoutubeDownloaderApp()
    app.mainloop()
