import tkinter as tk
from PIL import ImageGrab
import os
import datetime

class SnipTool(tk.Toplevel):
    def __init__(self, master, on_snip_complete):
        super().__init__(master)
        self.withdraw() # Pencereyi gizle (başlangıçta)
        self.attributes('-fullscreen', True)
        self.attributes('-alpha', 0.3)
        self.attributes('-topmost', True)
        self.configure(background='black')
        self.overrideredirect(True) # Pencere kenarlıklarını kaldır

        self.on_snip_complete = on_snip_complete
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        
        # v63: Rölatif Tıklama (F3) Durumu
        self.f3_mode = False
        self.target_rect_coords = None # (x1, y1, x2, y2)
        self.click_point_marker = None

        self.canvas = tk.Canvas(self, cursor="cross", bg="grey11")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        # ESC ile çıkış
        self.bind("<Escape>", lambda e: self.destroy())
        
        # F2 ile Gecikmeli Yakalama (v42)
        self.bind("<F2>", self.start_delay)
        
        # F3 ile Rölatif Tıklama (v63)
        self.bind("<F3>", self.enable_f3_mode)

    def start_delay(self, event=None):
        """5 saniye geri sayım başlatır, bu sırada ekranı serbest bırakır."""
        self.withdraw() # SnipTool'u gizle
        
        # Geri sayım penceresi
        self.countdown_win = tk.Toplevel()
        self.countdown_win.overrideredirect(True)
        self.countdown_win.attributes('-topmost', True)
        self.countdown_win.attributes('-alpha', 0.8)
        self.countdown_win.config(bg="black")
        
        # Ekran ortasına yerleştir
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        w, h = 200, 100
        x = (screen_w // 2) - (w // 2)
        y = (screen_h // 2) - (h // 2)
        self.countdown_win.geometry(f"{w}x{h}+{x}+{y}")
        
        self.lbl_count = tk.Label(self.countdown_win, text="5", font=("Arial", 48, "bold"), fg="white", bg="black")
        self.lbl_count.pack(expand=True)
        
        self.remaining = 5
        self.update_countdown()

    def update_countdown(self):
        if self.remaining > 0:
            self.lbl_count.config(text=str(self.remaining))
            self.remaining -= 1
            self.after(1000, self.update_countdown)
        else:
            self.countdown_win.destroy()
            
            # v69.2: Dondur & Ekranı Karart (v145)
            try:
                from PIL import ImageTk, ImageEnhance
                self.frozen_img = ImageGrab.grab()
                
                # Görsel geri bildirim için görseli karart (Dimming)
                enhancer = ImageEnhance.Brightness(self.frozen_img)
                display_img = enhancer.enhance(0.6) # %60 parlaklık
                
                self.tk_frozen_img = ImageTk.PhotoImage(display_img)
                self.canvas.create_image(0, 0, image=self.tk_frozen_img, anchor="nw")
                
                # Karartılmış görsel ile tam opaklıkta göster
                self.attributes('-alpha', 1.0)
            except Exception as e:
                print(f"Dondurma hatası: {e}")
                self.attributes('-alpha', 0.3)

            self.deiconify() 
            self.focus_force() 
            self.grab_set() 

    def enable_f3_mode(self, event=None):
        """F3 modunu aktifleştirir: Önce resim, sonra tıklama noktası."""
        self.f3_mode = True
        # Kullanıcıya bilgi ver (Sol üstte geçici etiket)
        info_lbl = tk.Label(self.canvas, text="F3 AKTİF: Önce alanı seçin, sonra tıklanacak noktayı seçin.", bg="red", fg="white", font=("Arial", 12, "bold"))
        info_lbl.place(x=10, y=10)
        self.after(3000, info_lbl.destroy)

    def start_selection(self):
        """Seçim ekranını başlatır."""
        self.deiconify() # Pencereyi göster
        self.focus_force() # Zorla odakla
        self.grab_set() # Tüm olayları yakala (Modal yap)

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, 
            outline='red', width=2
        )

    def on_move_press(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.current_rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # Koordinatları sırala (soldan sağa, yukarıdan aşağıya)
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        # Çok küçükse iptal et (yanlışlıkla tıklama)
        if (x2 - x1) < 5 or (y2 - y1) < 5:
            # Eğer F3 modundaysak ve bir alan zaten seçiliyse, bu bir "tıklama noktası" seçimi olabilir
            if self.f3_mode and self.target_rect_coords:
                self.handle_f3_click_point(event.x, event.y)
                return
            else:
                self.destroy()
                return

        if self.f3_mode:
            # v64.2 Düzeltme: Eğer alan zaten seçiliyse, ikinci sürükleme de olsa bunu "Click Noktası" olarak algıla
            if self.target_rect_coords:
                 # Kullanıcı tıklamak yerine sürüklese bile, bıraktığı noktayı (veya merkezi) tıklama noktası yapalım
                 self.handle_f3_click_point(event.x, event.y)
                 return

            # Sadece alanı belirle, pencereyi kapatma
            self.target_rect_coords = (x1, y1, x2, y2)
            self.canvas.create_rectangle(x1, y1, x2, y2, outline='yellow', width=3, dash=(4,4))
            # Bilgi güncelle
            info_lbl = tk.Label(self.canvas, text="ALAN SEÇİLDİ. Şimdi alan İÇERİSİNDE tıklanacak noktayı seçin.", bg="green", fg="white")
            info_lbl.place(x=10, y=40)
        else:
            self.capture_screen(x1, y1, x2, y2)
            self.destroy() # Pencereyi kapat (v64: capture sonrası)

    def handle_f3_click_point(self, click_x, click_y):
        """F3 modunda tıklama noktasını işler ve offset hesaplar (Sınırlı v64)."""
        x1, y1, x2, y2 = self.target_rect_coords
        
        # v64: Tıklama noktasını alanın dışına çıkmaması için kısıtla (Clamp)
        final_x = max(x1, min(click_x, x2))
        final_y = max(y1, min(click_y, y2))
        
        # Resmin merkezi
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Offset (Merkezden uzaklık)
        offset_x = final_x - center_x
        offset_y = final_y - center_y
        
        self.capture_screen(x1, y1, x2, y2, offset=(offset_x, offset_y))
        self.destroy() # v64: İşlem bitince kesin kapat

    def capture_screen(self, x1, y1, x2, y2, offset=(0, 0)):
        """Ekrandan belirtilen alanı keser ve kaydeder."""
        try:
            from core.config import DATA_DIR
            filename = f"snip_{datetime.datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}.png"
            # v67 Düzeltme: Assets klasörü silindiği için geçici olarak DATA_DIR'e kaydet
            filepath = os.path.join(DATA_DIR, filename)

            # Ekran görüntüsü al
            # v64.1 Düzeltme: Overlay'in rengi resme geçmesin diye pencereyi gizle
            self.withdraw()
            import time
            time.sleep(0.2) # Ekranın tazelenmesi için kısa bekleme
            
            # v69: Eğer Freeze Mode (F2) aktifse, donmuş resimden kes
            if hasattr(self, 'frozen_img') and self.frozen_img:
                img = self.frozen_img.crop((x1, y1, x2, y2))
            else:
                # Normal mod (Anlık Yakalama)
                img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            img.save(filepath)
            
            if self.on_snip_complete:
                # v63: filepath + offset bilgisini dön
                self.on_snip_complete(filepath, offset)
                
        except Exception as e:
            print(f"Hata: {e}")
