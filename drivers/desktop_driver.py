import time
import os
import logging
import pyautogui
from pywinauto import Desktop as WinDesktop
from PIL import Image

from drivers.base_driver import BaseDriver

import psutil # v167.38: Strict Process Matching

# PyAutoGUI fail-safe
pyautogui.FAILSAFE = True

class DesktopDriver(BaseDriver):
    def __init__(self, db=None, stop_check_callback=None):
        self.logger = logging.getLogger("DesktopDriver")
        self.db = db # v63: Veritabanı Yöneticisi referansı
        self.stop_check_callback = stop_check_callback # v73: Anında Durdurma
        # OpenCV Kontrolü
        try:
            import cv2
            self.logger.info("OpenCV (cv2) Aktif. Super-Vision motoru hazır.")
            self.has_opencv = True
        except ImportError:
            self.logger.warning("OpenCV bulunamadı. Lütfen 'opencv-python' paketini kurun.")
            self.has_opencv = False
        
    def launch_app(self, app_path: str) -> bool:
        self.logger.info(f"Uygulama başlatılıyor: {app_path}")
        try:
            os.startfile(app_path)
            # v167.38: Fix - Exe adını tam olarak kullan
            app_name = os.path.basename(app_path)
            return self.bring_to_front(app_name)
        except Exception as e:
            self.logger.error(f"Uygulama başlatılamadı: {e}")
            return False

    def _normalize_title(self, title: str) -> str:
        """v160.14: Pencere başlığındaki boşluk ve özel karakterleri temizler."""
        if not title: return ""
        return "".join(c for c in title.lower() if c.isalnum())

    def bring_to_front(self, name_hint: str) -> bool:
        """Belirtilen isme sahip pencereyi bulup öne getirir ve maksimize eder (Public API)."""
        self.logger.info(f"Pencere aranıyor ve öne getiriliyor: {name_hint} (Maks 15s)...")
        start_time = time.time()
        max_wait = 15
        our_tool_title = "Desktop Otomasyon"
        
        # Tarayıcı başlıkları için anahtar kelimeler
        browser_keywords = ["chrome", "edge", "firefox", "opera", "brave", "internet explorer", "yandex"]
        
        # v160.11: Arama türünü belirle
        is_browser_search = name_hint in ["browser", "web"] or name_hint in browser_keywords
        
        # v167.38: Strict Process Matching Mode
        # Eğer name_hint ".exe" ile bitiyorsa, Process Matching (PID) kullan.
        is_process_match = name_hint.lower().endswith(".exe")
        
        keywords = []
        if name_hint in ["browser", "web"]:
             keywords = browser_keywords
        else:
             # v160.10: Fix - Sadece exe adını ara, browser fallback'ini kaldır.
             keywords = [name_hint] 

        # v160.14: Normalleştirilmiş anahtar kelimeler listesi
        norm_keywords = [self._normalize_title(k) for k in keywords]

        while time.time() - start_time < max_wait:
            try:
                desktop = WinDesktop(backend="uia")
                for win in desktop.windows():
                    title = win.window_text()
                    if not title: continue
                    title_lower = title.lower()
                    title_norm = self._normalize_title(title)
                    
                    # Kendi aracımızı ASLA maksimize etme
                    if our_tool_title.lower() in title_lower: continue
                    
                    match = False
                    
                    # YÖNTEM 1: STRICT PROCESS MATCHING (PID Kontrolü)
                    if is_process_match:
                        try:
                            pid = win.process_id()
                            proc = psutil.Process(pid)
                            proc_name = proc.name().lower()
                            # Hedef exe adı ile çalışan process adı aynı mı?
                            if proc_name == name_hint.lower():
                                match = True
                                self.logger.info(f"Process Match Onaylandı: {proc_name} (PID: {pid})")
                        except Exception as pe:
                            # Erişim hatası veya process kapanmış olabilir
                            pass
                    
                    # YÖNTEM 2: STANDARD TITLE MATCHING (Process Match değilse veya başarısızsa)
                    if not match and not is_process_match:
                        # Hedef pencereyi bulmaya çalış (Hem tam hem de normalleştirilmiş eşleşme)
                        for i, kw in enumerate(keywords):
                            kw_norm = norm_keywords[i]
                            if kw in title_lower or (kw_norm and kw_norm in title_norm):
                                match = True
                                break
                    
                    if match and not is_browser_search and not is_process_match:
                        # v160.11: Akıllı Filtreleme - Eğer uygulama arıyorsak ama pencere başlığında 
                        # başka bir tarayıcı adı geçiyorsa (örn: JMeter araması yapılan Chrome sekmesi), atla.
                        if any(bkw in title_lower for bkw in browser_keywords if bkw != name_hint):
                            # Bu bir tarayıcı sekmesi olabilir, asıl uygulamayı aramaya devam et.
                            match = False
                                
                    if match:
                        if win.is_visible():
                            # Eğer zaten maximize ise tekrar yapma (titreme olmasın)
                            # win.maximize() her zaman güvenli olmayabilir ama deneyelim.
                            # Win11 Uyumluluğu: SetForegroundWindow Hack
                            try:
                                # v160.13: Agresif Odaklama ve Maksimize (Keyboard Fallback)
                                if win.is_minimized():
                                    win.restore()
                                
                                win.set_focus()
                                time.sleep(0.2) # UI tepkisi için daha uzun bekleme
                                
                                # Yöntem 1: Standart UIA Maximize
                                try:
                                    win.maximize()
                                except:
                                    pass
                                
                                # Yöntem 2: Klavye Kısayolu (Alt + Space + X)
                                # Bazı Java/Win11 pencereleri sadece buna yanıt verir
                                try:
                                    time.sleep(0.2)
                                    from pywinauto.keyboard import send_keys
                                    # Alt + Boşluk (Sistem Menüsü) -> X (Ekranı Kapla)
                                    send_keys('% {x}')
                                except Exception as k_err:
                                    self.logger.debug(f"Klavye kısayolu başarısız: {k_err}")
                                
                                self.logger.info(f"Pencere yakalandı ve odaklandı: {title}")
                                return True
                            except Exception as e:
                                self.logger.warning(f"Odaklama hatası (Tekrar denenecek): {e}")
            except: pass
            time.sleep(1.0)
        
        self.logger.warning("Hedef pencere tam olarak bulunamadı veya odaklanamadı.")
        return True # Hata döndürme, belki açılmıştır ama maximize olmamıştır.

    def open_url(self, url: str) -> bool:
        self.logger.info(f"Site açılıyor: {url}")
        try:
            import webbrowser
            webbrowser.open(url)
            
            # Tarayıcıyı bul ve maksimize et
            # "browser" hint'i veriyoruz, böylece Chrome/Edge vb. arayacak
            return self.bring_to_front("browser")
        except Exception as e:
            self.logger.error(f"Site açılamadı: {e}")
            return False

    def wait_for_element(self, target: str, timeout: float = 10, confidence: float = None, text_hint: str = None, match_index: int = 0, click_offset: tuple = (0, 0)) -> tuple:
        """
        Ortak Görsel Arama Motoru (Unified Vision Engine)
        Görseli arar ve bulursa (x, y) koordinatlarını döndürür. Bulamazsa None döndürür.
        """
        start_time = time.time()
        
        # Koordinat mı?
        if "," in target and os.path.sep not in target:
            x, y = map(int, target.split(","))
            return (x, y)

        while time.time() - start_time < timeout:
            # v73: Zorla durdurma kontrolü
            if self.stop_check_callback and self.stop_check_callback():
                self.logger.info("Vision Engine: Kullanıcı tarafından durduruldu.")
                return None

            # GÜNCELLEME (v47): Sabit confidence varsa dinamik düşüşü iptal et
            if confidence is not None:
                current_confidence = confidence
            else:
                # Zamanla düşen güven eşiği
                elapsed = time.time() - start_time
                current_confidence = max(0.65, 0.85 - (elapsed / timeout) * 0.20)
            
            # KATMAN 1: MUTLAK GÖRÜŞ (OpenCV)
            if self.has_opencv:
                coords = self._find_image_opencv(target, threshold=current_confidence, match_index=match_index, click_offset=click_offset)
                if coords: return coords
            
            # KATMAN 2: ŞEKİL EŞLEŞTİRME (Rengi Yoksay) - Sadece OpenCV varsa ve normal eşleşme başarısızsa
            if self.has_opencv:
                coords = self._find_image_opencv(target, threshold=max(0.6, current_confidence - 0.1), ignore_color=True, match_index=match_index, click_offset=click_offset)
                if coords: return coords

            # KATMAN 3: STANDART GERİ ÇEKİLME (Fallback) (v63: Sadece index ve offset yoksa güvenli)
            # Çünkü pyautogui.locateOnScreen index ve offset desteklemiyor.
            if match_index == 0 and click_offset == (0, 0):
                try:
                    from PIL import Image
                    needle = Image.open(target)
                    location = pyautogui.locateOnScreen(needle, grayscale=True, confidence=min(0.8, current_confidence))
                    if location:
                        center = pyautogui.center(location)
                        from core.config import get_dpi_scaling
                        scaling = get_dpi_scaling()
                        return (center.x / scaling, center.y / scaling)
                except: pass

            # KATMAN 4: UIA (Metin Tanıma)
            if text_hint:
                try:
                    from pywinauto import Desktop
                    desktop = Desktop(backend="uia")
                    for win in desktop.windows(visible_only=True):
                        try:
                            child = win.child_window(title_re=f".*{text_hint}.*", found_index=0)
                            if child.exists():
                                rect = child.rectangle()
                                # UIA'da offset desteği (Henüz prototip)
                                target_x = (rect.left + rect.right) // 2 + click_offset[0]
                                target_y = (rect.top + rect.bottom) // 2 + click_offset[1]
                                from core.config import get_dpi_scaling
                                scaling = get_dpi_scaling()
                                return (target_x / scaling, target_y / scaling)
                        except: continue
                except: pass

            time.sleep(0.3)
        return None
    def click(self, target: str, timeout: int = 10, text_hint: str = None, button: str = 'left', confidence: float = None, match_index: int = 0, click_offset: tuple = (0, 0)) -> bool:
        """v63: İndeks ve Ofset destekli Tıklama."""
        coords = self.wait_for_element(target, timeout=timeout, text_hint=text_hint, confidence=confidence, match_index=match_index, click_offset=click_offset)
        
        if coords:
            target_x, target_y = coords
            # Görsel onay için taşı
            pyautogui.moveTo(target_x, target_y, duration=0.2)
            time.sleep(0.3) 

            if button == 'double':
                pyautogui.doubleClick()
            else:
                pyautogui.mouseDown(button=button)
                time.sleep(0.05)
                pyautogui.mouseUp(button=button)
            
            self.logger.info(f"Tıklandı: {os.path.basename(target)} (İndeks: {match_index})")
            return True
        return False

    def _find_image_opencv(self, target_path: str, threshold: float = 0.8, ignore_color: bool = False, match_index: int = 0, click_offset: tuple = (0, 0)):
        """Mutlak Görüş (Absolute Vision): Çoklu-Ölçek + Çoklu-Eşleşme + İndeksleme + Ofset."""
        try:
            import cv2
            import numpy as np
            
            # Ekranı al ve normalize et
            screen_img = np.array(pyautogui.screenshot())
            screen_bgr = cv2.cvtColor(screen_img, cv2.COLOR_RGB2BGR)
            screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
            screen_gray = cv2.GaussianBlur(screen_gray, (3, 3), 0)
            
            template_bgr = None # Şablon başlat
            # FAZ 0: DB ARAMASI (v66: Birincil Kaynak)
            if self.db:
                # Target path aslında bir ID veya isim olabilir, ya da dosya silinmiş olabilir
                assets = self.db.list_assets()
                # En yakını bulmaya çalış (basename üzerinden)
                target_name = os.path.basename(target_path)
                for asset in assets:
                    # asset: (id, name, created_at, data)
                    if asset[1] == target_name:
                        if asset[3]: # Binary veri
                            nparr = np.frombuffer(asset[3], np.uint8)
                            template_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            if template_bgr is not None:
                                self.logger.debug(f"Vision: Görsel Veritabanından yüklendi: {asset[1]}")
                                break
            # FAZ 0.5: DOSYA FALLBACK (Eski Yöntem)
            if template_bgr is None and os.path.exists(target_path):
                template_bgr = cv2.imread(target_path)
                
            if template_bgr is None: return None
            
            template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.GaussianBlur(template_gray, (3, 3), 0)
            
            h, w = template_gray.shape[:2]
            scales = np.linspace(0.7, 1.3, 7) # Performans için ölçek sayısını biraz azalttık v63
            
            all_matches = [] # (val, loc, scale, rw, rh)
            
            # FAZ 1: STANDART ÇOKLU-ÖLÇEKLİ ŞABLON EŞLEŞTİRME
            # (Hızlı ve Kesin - %100 Renk ve Şekil Uyumu)
            found_matches = []
            best_scale_score = -1
            best_scale = 1.0
            best_rw, best_rh = 0, 0
            
            # Adım 1: En iyi ölçeği bul
            for scale in scales:
                rw, rh = int(w * scale), int(h * scale)
                if rw < 10 or rh < 10: continue
                
                resized_gray = cv2.resize(template_gray, (rw, rh))
                res = cv2.matchTemplate(screen_gray, resized_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                
                if max_val > best_scale_score:
                    best_scale_score = max_val
                    best_scale = scale
                    best_rw, best_rh = rw, rh

            # Adım 2: Belirlenen ölçekte TÜM eşleşmeleri bul (Multi-Instance)
            if best_scale_score >= threshold:
                rw, rh = best_rw, best_rh
                resized_gray = cv2.resize(template_gray, (rw, rh))
                res = cv2.matchTemplate(screen_gray, resized_gray, cv2.TM_CCOEFF_NORMED)
                
                while True:
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    
                    if max_val < threshold:
                        break
                        
                    # Eşleşmeyi kaydet: (score, (x,y), scale, w, h)
                    found_matches.append((max_val, max_loc, best_scale, rw, rh))
                    
                    # Bulunan alanı maskele (Tekrar bulmasın diye)
                    # Maskeleme: Bulunan noktanın etrafını -1 yap
                    # Dikkat: Grid yapıda yan yana olabilir, çok büyük maskeleme yapma.
                    # Yarım boyutta maskeleme genellikle güvenlidir.
                    mx, my = max_loc
                    cv2.rectangle(res, (mx - rw//2, my - rh//2), (mx + rw//2, my + rh//2), -1, -1)

            if found_matches:
                # v160: Uzamsal Sıralama (Grid Sort)
                # Önce Y (Satır), sonra X (Sütun) değerine göre sırala
                # Tolerans: Satırlar arası küçük piksel farklarını yok say (örn: 10px)
                def sort_key(match):
                    score, (x, y), s, w, h = match
                    return (int(y // 10) * 10, x)
                
                found_matches.sort(key=sort_key)
                
                self.logger.info(f"Vision: Toplam {len(found_matches)} eşleşme bulundu. İstenen İndeks: {match_index}")
                
                if 0 <= match_index < len(found_matches):
                    # İstenen indeksteki eşleşmeyi seç
                    # all_matches listesine ekleyip aşağıdaki akışa bırakıyoruz
                    target_match = found_matches[match_index]
                    self.logger.info(f"Vision: İndeks {match_index} seçildi (Skor: %{int(target_match[0]*100)})")
                    all_matches.append(target_match)
                else:
                    self.logger.warning(f"Vision: İstenen indeks ({match_index}) bulunanların dışında (Toplam: {len(found_matches)}). En iyi eşleşme (0) kullanılıyor.")
                    all_matches.append(found_matches[0]) 

            # FAZ 2: ANAHTAR NOKTA EŞLEŞTİRME (SIFT/ORB) - "Akıllı Göz" 🧠
            # Eğer standart arama başarısızsa veya düşük skorluysa devreye girer.
            # Renk değişimlerine, hafif bozulmalara ve dönmelere karşı dayanıklıdır.
            elif self.has_opencv:
                try:
                    self.logger.info("Vision: Standart arama yetersiz, Yapay Zeka (Keypoint Matching) devreye giriyor...")
                    
                    # ORB dedektörünü başlat (Hızlı ve etkili)
                    orb = cv2.ORB_create(nfeatures=1000)
                    
                    # Anahtar noktaları ve tanımlayıcıları bul
                    kp1, des1 = orb.detectAndCompute(template_gray, None)
                    kp2, des2 = orb.detectAndCompute(screen_gray, None)
                    
                    if des1 is not None and des2 is not None and len(des1) > 5 and len(des2) > 5:
                        # Eşleştirici (Hamming mesafeli BFMatcher)
                        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                        matches = bf.match(des1, des2)
                        
                        # Mesafeye göre sırala (En iyi eşleşmeler önce)
                        matches = sorted(matches, key=lambda x: x.distance)
                        
                        # İlk N eşleşmeyi al
                        good_matches = matches[:20] # En iyi 20 nokta
                        
                        if len(good_matches) >= 5: # En az 5 nokta tutmalı
                            # İyi eşleşmelerin konumunu çıkar
                            src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                            
                            # Homografi Bul (Perspektif dönüşümü)
                            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                            
                            if M is not None:
                                # Şablon boyutlarını al
                                h, w = template_gray.shape
                                pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                                
                                # Ekran koordinatlarına dönüştür
                                dst = cv2.perspectiveTransform(pts, M)
                                
                                # Sınırlayıcı Kutuyu (Bounding Box) al
                                x_min = int(np.min(dst[:, 0, 0]))
                                y_min = int(np.min(dst[:, 0, 1]))
                                x_max = int(np.max(dst[:, 0, 0]))
                                y_max = int(np.max(dst[:, 0, 1]))
                                
                                # Doğrulama: Boyut kontrolü (Aşırı büyük/küçük olmamalı)
                                box_w = x_max - x_min
                                box_h = y_max - y_min
                                
                                if 0.5 * w < box_w < 2.0 * w and 0.5 * h < box_h < 2.0 * h:
                                    self.logger.info(f"Vision AI: Nesne şekil özellikleri ile bulundu! (Keypoints: {len(good_matches)})")
                                    # Format: (Val, Loc(x,y), Scale, W, H)
                                    # RANSAC geçtiyse Keypoint skoru genellikle güvenilirdir (1.0)
                                    all_matches.append((0.95, (x_min, y_min), 1.0, box_w, box_h))
                    
                except Exception as e:
                    self.logger.warning(f"Keypoint Eşleştirme Hatası: {e}")

            if not all_matches:
                self.logger.debug(f"Vision Teşhis: Hiç eşleşme bulunamadı (Eşik: %{int(threshold*100)}).")
                return None

            # En iyi eşleşmeyi seç
            # (Multi-match mantığı burada basitleştirildi, çünkü keypoint tek sonuç döner genelde)
            target_match = all_matches[0] 

            val, loc, scale, rw, rh = target_match
            
            # Renk Onayı (v63: Ignore_color değilse) - Keypoint için opsiyonel yapılabilir ama şimdilik tutalım
            if not ignore_color and val != 0.95: # 0.95 ise Keypoint'tir, renk bakma
                detected_region = screen_bgr[loc[1]:loc[1]+rh, loc[0]:loc[0]+rw]
                # Resize template to matched size
                if detected_region.shape[0] > 0 and detected_region.shape[1] > 0:
                    target_resized_bgr = cv2.resize(template_bgr, (rw, rh))
                    color_res = cv2.matchTemplate(detected_region, target_resized_bgr, cv2.TM_CCORR_NORMED)
                    _, color_val, _, _ = cv2.minMaxLoc(color_res)
                    if color_val < 0.60:
                        self.logger.info(f"Vision: Renk Onayı Başarısız (%{int(color_val*100)})")
                        return None
                    self.logger.info(f"Vision Teşhis: Renk Onayı Skoru: %{int(color_val*100)} (Eşik: %60)")

            # Koordinat Hesaplama
            center_x = loc[0] + rw // 2
            center_y = loc[1] + rh // 2
            
            # RÖLATİF TIKLAMA (v63): Ofset Uygula
            center_x += click_offset[0]
            center_y += click_offset[1]
            
            from core.config import get_dpi_scaling
            scaling = get_dpi_scaling()
            
            self.logger.info(f"Hassas Koordinatlar Hesaplandı: ({int(center_x / scaling)}, {int(center_y / scaling)}) [DPI Skaler: {scaling:.2f}]")
            return (center_x / scaling, center_y / scaling)

        except Exception as e:
            self.logger.debug(f"OpenCV Vision Hatası: {e}")
            return None


    def type_text(self, text: str, interval: float = 0.1) -> bool:
        """
        Metin yazar. (v167.47: Immediate Stop Support)
        """
        try:
            import random
            from pynput.keyboard import Controller
            
            keyboard = Controller()
            self.logger.info(f"Metin yazılıyor (İnsan Modu + Türkçe): '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Character-by-character typing with random jitter
            for char in text:
                # v167.47: Immediate stop check
                if self.stop_check_callback and self.stop_check_callback():
                    self.logger.info("Metin yazımı durduruldu.")
                    return False
                
                # Add random variation to typing speed (human-like)
                jitter = random.uniform(0, 0.05) if interval >= 0.05 else random.uniform(0, 0.01)
                
                # Type the character using pynput (supports Unicode/Turkish)
                keyboard.type(char)
                
                # Wait with jitter
                time.sleep(interval + jitter)
            
            self.logger.info(f"Metin yazıldı: {len(text)} karakter")
            return True

        except Exception as e: 
            self.logger.error(f"Yazma hatası: {e}")
            return False


    def get_text(self, selector: str) -> str:
        """
        v167.24: Belirtilen seçiciden metin okur.
        Selector formatı: {'type': 'uia', 'title': '...', 'control_type': '...'} veya string.
        """
        try:
            self.logger.info(f"Metin okunuyor: {selector}")
            import json
            import uiautomation as auto
            
            sel_dict = {}
            if isinstance(selector, dict):
                sel_dict = selector
            elif isinstance(selector, str):
                try: sel_dict = json.loads(selector)
                except: sel_dict = {"title": selector} # Basit string ise title kabul et
                
            # UIA ile eleman bulma
            # Varsayılan olarak Root'tan başla
            root = auto.GetRootControl()
            search_depth = sel_dict.get("depth", 0xFFFFFFFF)
            
            # Parametreleri hazırla (v167.29: Mapping Improved)
            kwargs = {}
            # Name Mapping
            if "title" in sel_dict: kwargs["Name"] = sel_dict["title"]
            elif "Name" in sel_dict: kwargs["Name"] = sel_dict["Name"]
            elif "ControlName" in sel_dict: kwargs["Name"] = sel_dict["ControlName"]
            
            # AutomationId Mapping
            if "automation_id" in sel_dict: kwargs["AutomationId"] = sel_dict["automation_id"]
            elif "AutomationId" in sel_dict: kwargs["AutomationId"] = sel_dict["AutomationId"]
            
            # ClassName Mapping
            if "class_name" in sel_dict: kwargs["ClassName"] = sel_dict["class_name"]
            elif "ClassName" in sel_dict: kwargs["ClassName"] = sel_dict["ClassName"]
            
            # ControlType Mapping
            if "control_type" in sel_dict: 
                try: kwargs["ControlType"] = getattr(auto.ControlType, sel_dict["control_type"])
                except: pass
            elif "ControlType" in sel_dict:
                 try: kwargs["ControlType"] = getattr(auto.ControlType, sel_dict["ControlType"])
                 except: pass

            self.logger.debug(f"UIA Search Params: {kwargs}")
                
            found_control = None
            if kwargs:
                # v167.30: GetFirstChildControl yerine doğrudan Control tanımla ve arat
                # v167.31: Exists(maxSearchSeconds, searchInterval) positional usage
                candidate = auto.Control(**kwargs)
                if candidate.Exists(3, 0.1): 
                    found_control = candidate
                else:
                    found_control = None
            
            if found_control:
                # Metin alma stratejileri: ValuePattern > Name > Validation
                # 1. Value Pattern (Input alanları için)
                try: 
                    pattern = found_control.GetValuePattern()
                    if pattern:
                        val = pattern.Value
                        self.logger.info(f"Metin okundu (Value): {val}")
                        return val
                except: pass
                
                # 2. Text Pattern (Dökümanlar için)
                try:
                    pattern = found_control.GetTextPattern()
                    if pattern:
                        val = pattern.DocumentRange.GetText(-1)
                        self.logger.info(f"Metin okundu (TextPattern): {val}")
                        return val
                except: pass

                # 3. Name (Label, Button vb. için)
                name = found_control.Name
                self.logger.info(f"Metin okundu (Name): {name}")
                return name
                
            self.logger.warning("Eleman bulunamadı, boş metin dönülüyor.")
            return ""
            
        except Exception as e:
            self.logger.error(f"Metin okuma hatası: {e}")
            return ""
        except: return False

    def wait(self, seconds: float):
        self.logger.info(f"Bekleniyor: {seconds} sn")
        # v73: Parçalı bekleme (Anında Durdurma için)
        start = time.time()
        while time.time() - start < seconds:
            if self.stop_check_callback and self.stop_check_callback():
                self.logger.info("Bekleme: Kullanıcı tarafından durduruldu.")
                break
            time.sleep(min(0.1, seconds - (time.time() - start)))

    def assert_exists(self, target: str, timeout: int = 10, match_index: int = 0, click_offset: tuple = (0, 0)) -> bool:
        """Unified Vision Engine kullanan Durum Kontrolü (Check State)."""
        self.logger.info(f"Check State (Assert) Başladı: {os.path.basename(target)}")
        
        # wait_for_element zaten tüm yeteneklere (renk, şekil, uia, index, offset) sahip.
        coords = self.wait_for_element(target, timeout=timeout, match_index=match_index, click_offset=click_offset)
        
        if coords:
            self.logger.info(f"Check State: Başarılı, görsel bulundu.")
            return True
            
        self.logger.warning(f"Check State: Başarısız, {timeout}sn içinde bulunamadı.")
        return False

    def take_screenshot(self, save_path: str) -> str:
        try:
            pyautogui.screenshot().save(save_path)
            return save_path
        except: return ""

    def handle_popup(self, target: str) -> bool:
        """Belirtilen popup görselini arar, bulursa tıklar ve ENTER'a basar."""
        try:
            # target parametresi artık bir asset ismi olabilir
            loc = self._find_image_opencv(target)
            if loc:
                self.logger.info(f"Popup yakalandı: {target}")
                pyautogui.click(loc)
                time.sleep(0.5)
                pyautogui.press('enter')
                return True
            return False
        except Exception as e:
            self.logger.error(f"Popup işleyici hatası: {e}")
            return False

    def validate_window(self, title: str, timeout: int = 5) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                desktop = WinDesktop(backend="uia")
                for win in desktop.windows():
                    if title.lower() in win.window_text().lower(): return True
            except: pass
            time.sleep(0.5)
        return False

    def press_key(self, key: str) -> bool:
        try:
            pyautogui.press(key)
            return True
        except: return False

    def scroll(self, amount: int) -> bool:
        try:
            pyautogui.scroll(amount)
            return True
        except: return False

    def scroll_until_found(self, target: str, direction: str = "down", step: int = 500, max_steps: int = 10, timeout: int = 10, match_index: int = 0, click_offset: tuple = (0, 0)) -> bool:
        """Belirtilen görseli bulana kadar kaydırır (Akıllı Kaydırma / Smart Scroll)."""
        self.logger.info(f"Akıllı Kaydırma Başladı: {direction} yönüne, hedef: {os.path.basename(target)}")
        
        # Yön belirle (PyAutoGUI: Pozitif = Yukarı, Negatif = Aşağı)
        scroll_amount = -step if direction == "down" else step
        
        # v57: Fareyi ortaya çek (Hover efektini önle ve odakla)
        sw, sh = pyautogui.size()
        pyautogui.moveTo(sw//2, sh//2)
        
        for i in range(max_steps):
            # 1. Görseli ARA (Unified Engine)
            # v58: "Click ile aynı motoru kullan" isteği üzerine.
            # wait_for_element ile tüm katmanları (OpenCV, Shape, Fallback) 0.8sn boyunca dener.
            self.logger.info(f"Akıllı Kaydırma: Aranıyor... (Adım {i+1}/{max_steps})")
            
            # v73: Durdurma Kontrolü
            if self.stop_check_callback and self.stop_check_callback(): return False
            
            try:
                # v167.6: False Positive Fix - Sabit ve yüksek güven eşiği (0.85)
                # Süre kısa olduğu için dinamik düşüşe izin verme.
                coords = self.wait_for_element(target, timeout=0.8, confidence=0.85, match_index=match_index, click_offset=click_offset)
                if coords:
                    self.logger.info(f"Akıllı Kaydırma: Hedef bulundu! (Adım {i+1})")
                    return True
            except Exception as e:
                 self.logger.warning(f"Akıllı Kaydırma: Arama hatası (Adım {i+1}): {e}")

            # 2. Bulamazsa KAYDIR
            self.logger.info(f"Akıllı Kaydırma: Bulunamadı, kaydırılıyor ({i+1}/{max_steps})...")
            try:
                pyautogui.scroll(scroll_amount)
            except Exception as e:
                self.logger.error(f"Akıllı Kaydırma: SCROLL Hatası: {e}")
                # Hata olsa bile devam et, belki bir sonraki adımda düzelir veya hedef zaten görünürdedir.
            
        self.logger.warning("Akıllı Kaydırma: Maksimum adım sayısına ulaşıldı, hedef bulunamadı.")
        return False
