import tkinter as tk
import ctypes
from ctypes import windll, c_int, byref

class ExecutionOverlay:
    def __init__(self):
        self.root = None

    def show(self):
        if self.root: return
        
        self.root = tk.Toplevel()
        self.root.title("Automation Overlay")
        
        # Tam ekran ve çerçevesiz
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-toolwindow", True)
        
        # Şeffaflık ayarı (Windows için)
        start_color = "#000001" # Neredeyse siyah (Transparency Key)
        border_color = "red"
        border_thickness = 5
        
        self.root.config(bg=start_color)
        self.root.attributes("-transparentcolor", start_color)
        
        # Canvas oluştur ve çerçeve çiz
        canvas = tk.Canvas(self.root, width=sw, height=sh, bg=start_color, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        # Kırmızı Çerçeve
        # create_rectangle(x1, y1, x2, y2, outline=color, width=thickness)
        # İç çerçeve çiziyoruz ki ekran dışına taşmasın
        canvas.create_rectangle(
            0, 0, sw, sh,
            outline=border_color,
            width=border_thickness * 2 # Yarısı dışarıda kalacağı için 2 katı
        )

        # CLICK-THROUGH YAPMA (Kritik Bölüm)
        # Pencere handle (HWND) al
        hwnd = windll.user32.GetParent(self.root.winfo_id())
        
        # Mevcut stili al
        old_style = windll.user32.GetWindowLongW(hwnd, -20) # GWL_EXSTYLE
        
        # Yeni stilleri ekle: WS_EX_LAYERED (0x80000) | WS_EX_TRANSPARENT (0x20)
        # WS_EX_TRANSPARENT: Fare tıklamalarını arkaya geçirir.
        new_style = old_style | 0x80000 | 0x20
        windll.user32.SetWindowLongW(hwnd, -20, new_style)
        
        self.root.update()

    def hide(self):
        if self.root:
            self.root.destroy()
            self.root = None
