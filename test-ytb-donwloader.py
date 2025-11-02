"""
itubego_app.py

Application GUI simple pour télécharger des vidéos YouTube avec yt-dlp.
- Entrée pour coller l'URL
- Choix du dossier de sortie (par défaut: S:\\itubego)
- Bouton Télécharger
- Zone de log / statut

Dépendances:
    pip install yt-dlp

Usage:
    python itubego_app.py

Note: utilise yt-dlp (plus fiable que pytube). Ce logiciel doit être utilisé conformément
aux lois sur le droit d'auteur et uniquement pour des usages permis (ex: sauvegarde
personnelle si autorisée).
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import yt_dlp
except Exception:
    raise SystemExit("Module 'yt_dlp' introuvable. Installe-le avec: pip install yt-dlp")

DEFAULT_OUTPUT = r"S:\\itubego"

class ItubeGoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ItubeGo - Téléchargeur YouTube")
        self.geometry("700x380")
        self.resizable(False, False)

        # URL frame
        frm_url = ttk.Frame(self, padding=10)
        frm_url.pack(fill='x')

        ttk.Label(frm_url, text="URL YouTube:").pack(side='left')
        self.url_var = tk.StringVar()
        self.entry_url = ttk.Entry(frm_url, textvariable=self.url_var)
        self.entry_url.pack(side='left', fill='x', expand=True, padx=8)

        # Output frame
        frm_out = ttk.Frame(self, padding=10)
        frm_out.pack(fill='x')

        ttk.Label(frm_out, text="Dossier de sortie:").pack(side='left')
        self.out_var = tk.StringVar(value=DEFAULT_OUTPUT)
        self.entry_out = ttk.Entry(frm_out, textvariable=self.out_var, width=50)
        self.entry_out.pack(side='left', padx=8)
        ttk.Button(frm_out, text="Parcourir", command=self.browse_folder).pack(side='left')

        # Options frame
        frm_opt = ttk.Frame(self, padding=10)
        frm_opt.pack(fill='x')

        ttk.Label(frm_opt, text="Format/Qualité:").pack(side='left')
        self.quality_var = tk.StringVar(value='bestvideo+bestaudio')
        self.quality_cb = ttk.Combobox(frm_opt, textvariable=self.quality_var, state='readonly', width=30)
        self.quality_cb['values'] = (
            'bestvideo+bestaudio (meilleure qualité)',
            'best (meilleur combiné)',
            'bestaudio (audio uniquement)',
            'bestvideo (vidéo uniquement)'
        )
        self.quality_cb.current(0)
        self.quality_cb.pack(side='left', padx=8)

        # Buttons
        frm_btn = ttk.Frame(self, padding=10)
        frm_btn.pack(fill='x')

        self.btn_download = ttk.Button(frm_btn, text="Télécharger", command=self.start_download_thread)
        self.btn_download.pack(side='left')

        self.btn_clear = ttk.Button(frm_btn, text="Effacer log", command=self.clear_log)
        self.btn_clear.pack(side='left', padx=8)

        # Log / status
        frm_log = ttk.Frame(self, padding=10)
        frm_log.pack(fill='both', expand=True)

        self.log = tk.Text(frm_log, height=12, state='disabled', wrap='word')
        self.log.pack(fill='both', expand=True)

        # Progress label
        self.progress_var = tk.StringVar(value='Prêt')
        self.lbl_progress = ttk.Label(self, textvariable=self.progress_var, padding=6)
        self.lbl_progress.pack(side='bottom', fill='x')

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.out_var.get() or os.path.expanduser('~'))
        if folder:
            self.out_var.set(folder)

    def log_write(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text + "\n")
        self.log.see('end')
        self.log.configure(state='disabled')

    def clear_log(self):
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        self.log.configure(state='disabled')

    def start_download_thread(self):
        url = self.url_var.get().strip()
        outdir = self.out_var.get().strip() or DEFAULT_OUTPUT

        if not url:
            messagebox.showwarning("URL manquante", "Colle l'URL de la vidéo YouTube avant de lancer le téléchargement.")
            return

        # Créer le dossier si nécessaire
        try:
            os.makedirs(outdir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur dossier", f"Impossible de créer ou d'accéder au dossier:\n{outdir}\n\n{e}")
            return

        self.btn_download.configure(state='disabled')
        self.progress_var.set('Démarrage...')
        self.log_write(f"Démarrage du téléchargement: {url}")

        t = threading.Thread(target=self.download_worker, args=(url, outdir), daemon=True)
        t.start()

   def download_worker(self, url, outdir):
    # Configurer les options en fonction du choix de qualité
    q = self.quality_cb.get()
    if 'bestaudio' in q and '+' not in q:
        format_str = 'bestaudio'
    elif 'bestvideo+bestaudio' in q:
        format_str = 'bestvideo+bestaudio/best'
    elif 'bestvideo' in q and '+' not in q:
        format_str = 'bestvideo'
    else:
        format_str = 'best'

    ydl_opts = {
        'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'),
        'format': format_str,
        'noplaylist': True,
        'progress_hooks': [self.ydl_progress_hook],
        'quiet': True,
        'no_warnings': True,
        # 🔽 Conversion automatique en MP4
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # Forcer sortie en .mp4
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        self.log_write('Téléchargement terminé avec succès.')
        self.progress_var.set('Terminé')
    except Exception as e:
        self.log_write(f'Erreur durant le téléchargement: {e}')
        self.progress_var.set('Erreur')
    finally:
        self.btn_download.configure(state='normal')


        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # download may raise; capture logs
                ydl.download([url])
            self.log_write('Téléchargement terminé avec succès.')
            self.progress_var.set('Terminé')
        except Exception as e:
            self.log_write(f'Erreur durant le téléchargement: {e}')
            self.progress_var.set('Erreur')
        finally:
            self.btn_download.configure(state='normal')

    def ydl_progress_hook(self, d):
        # Called repeatedly by yt-dlp
        status = d.get('status')
        if status == 'downloading':
            # d contains 'downloaded_bytes' and 'total_bytes' (sometimes)
            downloaded = d.get('downloaded_bytes')
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            speed = d.get('speed')
            eta = d.get('eta')
            if total and downloaded:
                try:
                    pct = downloaded / total * 100
                    self.progress_var.set(f"Téléchargement: {pct:.1f}% - ETA {eta}s")
                    self.log_write(f"{d.get('filename','')} - {pct:.1f}% - {d.get('speed')} B/s")
                except Exception:
                    pass
        elif status == 'finished':
            self.progress_var.set('Merging/Finalisation...')
            self.log_write('Téléchargement terminé. Finalisation...')
        elif status == 'error':
            self.progress_var.set('Erreur')
            self.log_write('Erreur signalée par yt-dlp')


if __name__ == '__main__':
    app = ItubeGoApp()
    app.mainloop()
