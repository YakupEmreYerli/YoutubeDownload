import customtkinter as ctk
import os
import threading
from yt_dlp import YoutubeDL
from tkinter import messagebox

# App Configuration
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class YoutubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Config
        self.title("YouTube İndirici - MP3 & MP4")
        self.geometry("600x400")
        self.resizable(False, False)

        # Layout Grid Config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        # Title
        self.title_label = ctk.CTkLabel(self, text="YouTube Video/Ses İndirici", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # URL Input
        self.url_entry = ctk.CTkEntry(self, placeholder_text="YouTube Linkini Buraya Yapıştırın", width=400)
        self.url_entry.grid(row=1, column=0, padx=20, pady=10)

        # Type Selection (MP3/MP4)
        self.type_var = ctk.StringVar(value="mp4")
        self.radio_frame = ctk.CTkFrame(self)
        self.radio_frame.grid(row=2, column=0, padx=20, pady=10)
        
        self.radio_mp4 = ctk.CTkRadioButton(self.radio_frame, text="MP4 (Video)", variable=self.type_var, value="mp4")
        self.radio_mp4.grid(row=0, column=0, padx=20, pady=10)
        
        self.radio_mp3 = ctk.CTkRadioButton(self.radio_frame, text="MP3 (Ses)", variable=self.type_var, value="mp3")
        self.radio_mp3.grid(row=0, column=1, padx=20, pady=10)

        # Download Button
        self.download_btn = ctk.CTkButton(self, text="İndir", command=self.start_download_thread, height=40, font=ctk.CTkFont(size=16, weight="bold"))
        self.download_btn.grid(row=3, column=0, padx=20, pady=10)

        # Status & Progress
        self.status_label = ctk.CTkLabel(self, text="Hazır", text_color="gray")
        self.status_label.grid(row=4, column=0, padx=20, pady=(0, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=(0, 20))
        self.progress_bar.set(0)

    def start_download_thread(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Hata", "Lütfen bir YouTube linki girin.")
            return
        
        self.download_btn.configure(state="disabled", text="İndiriliyor...")
        self.status_label.configure(text="İşlem başlıyor...", text_color="orange")
        self.progress_bar.set(0)
        
        # Start download in a separate thread to keep UI responsive
        thread = threading.Thread(target=self.download_content, args=(url,))
        thread.start()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%', '')
                self.progress_bar.set(float(p) / 100)
                self.status_label.configure(text=f"İndiriliyor: {d.get('_percent_str')} - {d.get('_eta_str', '')} kaldı", text_color="blue")
            except:
                pass
        elif d['status'] == 'finished':
            self.progress_bar.set(1)
            self.status_label.configure(text="İndirme tamamlandı! Dönüştürülüyor/Kaydediliyor...", text_color="green")

    def download_content(self, url):
        download_type = self.type_var.get()
        output_path = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(output_path, exist_ok=True)

        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'noplaylist': True,
        }

        if download_type == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # MP4 - Video
            # format 'best' ensures we get a single file with audio and video, 
            # which works better if ffmpeg isn't installed. 
            # 'bestvideo+bestaudio' usually requires ffmpeg to merge.
            ydl_opts.update({
                'format': 'best', 
            })

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.after(0, lambda: self.finish_download(True))
        except Exception as e:
            self.after(0, lambda: self.finish_download(False, str(e)))

    def finish_download(self, success, error_msg=""):
        self.download_btn.configure(state="normal", text="İndir")
        if success:
            self.status_label.configure(text="İşlem Başarıyla Tamamlandı!", text_color="green")
            messagebox.showinfo("Başarılı", "İndirme tamamlandı! 'downloads' klasörünü kontrol edin.")
        else:
            self.status_label.configure(text="Hata oluştu.", text_color="red")
            messagebox.showerror("Hata", f"İndirme başarısız oldu:\n{error_msg}")

if __name__ == "__main__":
    app = YoutubeDownloaderApp()
    app.mainloop()
