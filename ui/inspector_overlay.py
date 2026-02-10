import customtkinter as ctk
import tkinter as tk
import threading
import time
from drivers.structure_driver import StructureDriver
import uiautomation as auto
import pyautogui
import io

class SpyController(ctk.CTkToplevel):
    """
    Spy oturumunu kontrol eden küçük yüzen pencere.
    """
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.driver = StructureDriver()
        
        self.title("Spy")
        self.geometry("300x120+50+50")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        self.lbl_info = ctk.CTkLabel(self, text="Hedefin üzerine gelin ve:\n[SOL CTRL] : Normal Seçim\n[F2] : Çapalı Seçim", font=("Arial", 13))
        self.lbl_info.pack(pady=10)
        
        self.lbl_status = ctk.CTkLabel(self, text="...", text_color="gray")
        self.lbl_status.pack(pady=5)
        
        self.btn_cancel = ctk.CTkButton(self, text="İptal (ESC)", command=self.on_cancel, fg_color="red", height=24)
        self.btn_cancel.pack(pady=5)
        
        # Vurgulayıcı Penceresi (Ayrı şeffaf pencere)
        self.highlighter = tk.Toplevel(self)
        self.highlighter.overrideredirect(True) # Başlık çubuğu yok
        self.highlighter.attributes("-topmost", True)
        self.highlighter.attributes("-transparentcolor", "lime") # Lime rengini şeffaf yap
        self.highlighter.config(bg="lime") 
        self.highlighter.withdraw()
        
        self.canvas = tk.Canvas(self.highlighter, bg="lime", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.running = True
        self.current_element = None
        self.temp_target_selector = None # v81: Çapa seçerken hedefi sakla
        self.temp_image_data = None # v121: Görsel verisini sakla
        self.selecting_anchor = False # v81: Durum bayrağı
        
        # Döngüyü Başlat
        self.thread = threading.Thread(target=self._spy_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def _spy_loop(self):
        while self.running:
            try:
                # 1. VURGULAYICIYI GEÇİCİ OLARAK GİZLE (Kendini tespit etmemesi için)
                self.after(0, self.highlighter.withdraw)
                time.sleep(0.01) 
                
                # 2. Elementi Al
                element = self.driver.get_element_under_mouse()
                
                if element:
                    self.current_element = element
                    rect = element.BoundingRectangle
                    if rect:
                        self.after(0, lambda r=rect: self._update_highlighter(r))
                        
                        name = element.Name or element.AutomationId or element.ClassName
                        role = element.ControlTypeName
                        display_text = f"[{role}] {name[:30]}"
                        
                        if not name or name.strip() == "":
                             display_text = f"<{role}>"
                             
                        if self.selecting_anchor:
                            display_text = f"[ÇAPA] {display_text}"
                             
                        self.after(0, lambda t=display_text: self.lbl_status.configure(text=t))
                
                # 3. Girdiyi Kontrol Et
                # CTRL: Seç
                if auto.IsKeyPressed(auto.Keys.VK_LCONTROL):
                    self.after(0, self.on_select)
                    time.sleep(0.5) 
                
                # F2: Çapalı Seçimi Başlat (v135)
                if not self.selecting_anchor and auto.IsKeyPressed(auto.Keys.VK_F2):
                    self.after(0, self._init_anchor_mode)
                    time.sleep(0.5)

                if auto.IsKeyPressed(auto.Keys.VK_ESCAPE):
                    self.after(0, self.on_cancel)
                    break
                    
            except Exception as e:
                print(f"Spy Hatası: {e}")
                pass
                
            time.sleep(0.1)

    def _init_anchor_mode(self):
        """v135: F2 mantığı - hedefi ayarla ve çapa moduna geç"""
        if not self.current_element: return
        
        try:
            # 1. Hedefi Yakala
            self.temp_target_selector = self.driver.get_selector(self.current_element)
            
            # 2. Görseli Yakala
            self.temp_image_data = None
            rect = self.current_element.BoundingRectangle
            if rect:
                w, h = rect.right-rect.left, rect.bottom-rect.top
                if w > 0 and h > 0:
                    img = pyautogui.screenshot(region=(rect.left, rect.top, w, h))
                    o = io.BytesIO()
                    img.save(o, format="PNG")
                    self.temp_image_data = o.getvalue()
            
            # 3. Anında Çapa Moduna Geç (v140)
            self.selecting_anchor = True
            self.lbl_info.configure(text="HEDEF KİLİTLENDİ! 🎯\nLütfen ÇAPA elemanını seçin.", text_color="blue")
            
            # Bip sesi
            try:
                import winsound
                winsound.Beep(800, 200)
            except: pass
            
        except Exception as e:
            print(f"Çapa Başlatma Hatası: {e}")

    def _update_highlighter(self, rect):
        left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
        width = right - left
        height = bottom - top
        
        if width > 0 and height > 0:
            self.highlighter.deiconify()
            self.highlighter.geometry(f"{width}x{height}+{left}+{top}")
            self.canvas.delete("all")
            color = "#00BFFF" if self.selecting_anchor else "red"
            self.canvas.create_rectangle(0, 0, width, height, outline=color, width=4)
        else:
            self.highlighter.withdraw()

    def on_select(self):
        """Kullanıcı seçmek için CTRL'ye bastığında çağrılır."""
        if not self.current_element: return
        
        # Döngüyü anında durdur
        self.running = False
        
        try:
            if self.selecting_anchor:
                # Çapalı Sonlandırma
                anchor_selector = self.driver.get_selector(self.current_element)
                final_selector = self.temp_target_selector
                final_selector["anchor"] = anchor_selector
                
                name = final_selector.get("ControlName") or final_selector.get("AutomationId") or "Element"
                role = final_selector.get("ControlType", "Control")
                desc = f"Tıkla {role}: {name} (Çapalı)"
                
                # KRİTİK: Modal bloklamayı önlemek için geri aramadan ÖNCE pencereyi kapat
                selector_to_send = final_selector
                img_to_send = self.temp_image_data
            else:
                # Doğrudan Seçim
                selector = self.driver.get_selector(self.current_element)
                
                image_data = None
                rect = self.current_element.BoundingRectangle
                if rect:
                    w, h = rect.right-rect.left, rect.bottom-rect.top
                    if w > 0 and h > 0:
                        img = pyautogui.screenshot(region=(rect.left, rect.top, w, h))
                        o = io.BytesIO()
                        img.save(o, format="PNG")
                        image_data = o.getvalue()
                
                name = selector.get("ControlName") or selector.get("AutomationId") or "Element"
                role = selector.get("ControlType", "Control")
                desc = f"Tıkla {role}: {name}"
                
                selector_to_send = selector
                img_to_send = image_data
            
            # Önce UI'ı kapat
            self.highlighter.withdraw()
            self.withdraw()
            
            # UI'ın gizlendiğinden emin olmak için kısa bir gecikme ile geri aramayı çalıştır
            def final_cmd():
                self.callback("CLICK_SELECTOR", selector_to_send, desc, img_to_send)
                self.on_cancel()

            self.after(50, final_cmd)
                 
        except Exception as e:
            print(f"HATA on_select: {e}")
            self.on_cancel()

    def on_cancel(self):
        self.running = False
        if self.highlighter:
            self.highlighter.destroy()
        self.destroy()

# Ana pencereden çağırma kodu ile uyumluluk için takma ad
InspectorOverlay = SpyController
