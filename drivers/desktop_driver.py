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
                # Zamanla düşen güven eşiği (Artık %95'ten başlıyor)
                elapsed = time.time() - start_time
                current_confidence = max(0.75, 0.95 - (elapsed / timeout) * 0.20)
            
            # KATMAN 1: MUTLAK GÖRÜŞ (OpenCV - Renkli ve 1:1 Ölçek Tercihli)
            if self.has_opencv:
                coords = self._find_image_opencv(target, threshold=current_confidence, match_index=match_index, click_offset=click_offset)
                if coords: return coords
            
            # KATMAN 2: ŞEKİL EŞLEŞTİRME (Rengi Yoksayarak Siyah/Beyaz Arama)
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
            # Blur kaldırıldı
            
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
            # Blur kaldırıldı
            
            # GÜNCELLEME: Siyah-Beyaz zorlamasını kaldır, gerekirse Renkli (BGR) ara
            if ignore_color:
                match_screen = screen_gray
                match_template = template_gray
            else:
                match_screen = screen_bgr
                match_template = template_bgr
            
            # FAZ 1: YAPAY ZEKA (Keypoint Matching - SIFT) - "Akıllı Göz" 🧠
            # Kullanıcı talebi: Ana yöntem olarak her zaman Keypoint Matching çalışsın.
            all_matches = [] # (val, loc, scale, rw, rh)
            
            if self.has_opencv:
                try:
                    self.logger.info("Vision: Yapay Zeka (SIFT Keypoint Matching) ile aranıyor...")
                    # 1. ORB yerine SIFT (Daha hassas, ölçek/dönüşüm bağımsız, patent kısıtlaması kalktı)
                    sift = cv2.SIFT_create()
                    kp1, des1 = sift.detectAndCompute(template_gray, None)
                    kp2, des2 = sift.detectAndCompute(screen_gray, None)
                    
                    if des1 is not None and des2 is not None and len(des1) > 4 and len(des2) > 4:
                        # FLANN veya BFMatcher (SIFT için NORM_L2)
                        bf = cv2.BFMatcher(cv2.NORM_L2)
                        matches = bf.knnMatch(des1, des2, k=2)
                        
                        # 2. Lowe's Ratio Test (Kesinlik Filtresi - Halüsinasyonları Engeller)
                        # Sadece "açık ara" en iyi olan, rakiplerinden %30 daha iyi eşleşmeleri al.
                        good_matches = []
                        for m_n in matches:
                            if len(m_n) == 2:
                                m, n = m_n
                                if m.distance < 0.7 * n.distance:
                                    good_matches.append(m)
                        
                        if len(good_matches) >= 4: # En az 4 güvenilir nokta (Homografi için şart)
                            # 3. Kümeleme (Clustering) - Çoklu hedefler için basit mesafe tabanlı gruplama
                            # Aynı ekranda birden fazla aynı butondan varsa RANSAC şaşırır. Bunları kümelere ayırıyoruz.
                            h_t, w_t = template_gray.shape
                            cluster_threshold = max(h_t, w_t) * 1.5 # Şablon boyutunun 1.5 katı mesafedekiler aynı gruptur
                            
                            clusters = []
                            for m in good_matches:
                                pt = np.array(kp2[m.trainIdx].pt)
                                matched_cluster = False
                                for cluster in clusters:
                                    # Kümeye ait noktaların ortalaması ile mesafe kontrolü
                                    center = np.mean([p for _, p in cluster], axis=0)
                                    if np.linalg.norm(pt - center) < cluster_threshold:
                                        cluster.append((m, pt))
                                        matched_cluster = True
                                        break
                                if not matched_cluster:
                                    clusters.append([(m, pt)])
                            
                            valid_clusters = []
                            for cluster in clusters:
                                if len(cluster) >= 4: # RANSAC için minimum 4 nokta
                                    c_matches = [m_item for m_item, _ in cluster]
                                    src_pts = np.float32([kp1[m_item.queryIdx].pt for m_item in c_matches]).reshape(-1, 1, 2)
                                    dst_pts = np.float32([p for _, p in cluster]).reshape(-1, 1, 2)
                                    
                                    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                                    if M is not None:
                                        pts = np.float32([[0, 0], [0, h_t - 1], [w_t - 1, h_t - 1], [w_t - 1, 0]]).reshape(-1, 1, 2)
                                        dst = cv2.perspectiveTransform(pts, M)
                                        
                                        x_min = int(np.min(dst[:, 0, 0]))
                                        y_min = int(np.min(dst[:, 0, 1]))
                                        x_max = int(np.max(dst[:, 0, 0]))
                                        y_max = int(np.max(dst[:, 0, 1]))
                                        box_w = x_max - x_min
                                        box_h = y_max - y_min
                                        
                                        # Şekil anormallik kontrolü (Çok küçük veya çok büyük hatalı alanları ele)
                                        if 0.5 * w_t < box_w < 2.0 * w_t and 0.5 * h_t < box_h < 2.0 * h_t:
                                            valid_clusters.append({
                                                "score": len(c_matches), 
                                                "match": (0.95, (x_min, y_min), 1.0, box_w, box_h),
                                                "loc": (x_min, y_min)
                                            })
                            
                            if valid_clusters:
                                # Uzamsal (Grid) Sıralama: Önce Y, sonra X ekseninde butonları sırala
                                def sort_key(c):
                                    x, y = c["loc"]
                                    return (int(y // 10) * 10, x)
                                    
                                valid_clusters.sort(key=sort_key)
                                
                                self.logger.info(f"Vision AI: {len(valid_clusters)} benzersiz eşleşme bulundu. İstenen İndeks: {match_index}")
                                
                                if 0 <= match_index < len(valid_clusters):
                                    target_cluster = valid_clusters[match_index]
                                    self.logger.info(f"Vision AI: İndeks {match_index} seçildi (Keypoints: {target_cluster['score']})")
                                    all_matches.append(target_cluster["match"])
                                else:
                                    self.logger.warning(f"Vision AI: İstenen indeks ({match_index}) bulunanların dışında. En iyi eşleşme (0) kullanılıyor.")
                                    all_matches.append(valid_clusters[0]["match"])
                except Exception as e:
                    self.logger.warning(f"Keypoint Eşleştirme Hatası: {e}")

            # FAZ 2: STANDART EŞLEŞTİRME (Sessiz Yedek Yöntem)
            # Eğer Yapay Zeka nesneyi bulamazsa (örn: "dsg" gibi düz, pürüzsüz ve keypoint barındırmayan
            # basit butonlar), sistem hemen standart eşleştirmeyi devreye sokarak eksikliği kapatır.
            if not all_matches:
                found_matches = []
                h_sm, w_sm = match_template.shape[:2]
                res = cv2.matchTemplate(match_screen, match_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                
                if max_val >= threshold:
                    while True:
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                        if max_val < threshold: break
                        found_matches.append((max_val, max_loc, 1.0, w_sm, h_sm))
                        mx, my = max_loc
                        cv2.rectangle(res, (mx - w_sm//2, my - h_sm//2), (mx + w_sm//2, my + h_sm//2), -1, -1)
                else:
                    best_scale_score = -1
                    best_scale = 1.0
                    best_rw, best_rh = 0, 0
                    scales = np.linspace(0.8, 1.2, 10)
                    for scale in scales:
                        if abs(scale - 1.0) < 0.01: continue
                        rw, rh = int(w_sm * scale), int(h_sm * scale)
                        if rw < 10 or rh < 10: continue
                        resized_template = cv2.resize(match_template, (rw, rh))
                        res_scale = cv2.matchTemplate(match_screen, resized_template, cv2.TM_CCOEFF_NORMED)
                        _, max_val_scale, _, _ = cv2.minMaxLoc(res_scale)
                        if max_val_scale > best_scale_score:
                            best_scale_score = max_val_scale
                            best_scale = scale
                            best_rw, best_rh = rw, rh

                    if best_scale_score >= threshold:
                        rw, rh = best_rw, best_rh
                        resized_template = cv2.resize(match_template, (rw, rh))
                        res_scale = cv2.matchTemplate(match_screen, resized_template, cv2.TM_CCOEFF_NORMED)
                        while True:
                            min_val, max_val_scale, min_loc, max_loc = cv2.minMaxLoc(res_scale)
                            if max_val_scale < threshold: break
                            found_matches.append((max_val_scale, max_loc, best_scale, rw, rh))
                            mx, my = max_loc
                            cv2.rectangle(res_scale, (mx - rw//2, my - rh//2), (mx + rw//2, my + rh//2), -1, -1)

                if found_matches:
                    def sort_key(match):
                        score, (x, y), s, w, h = match
                        return (int(y // 10) * 10, x)
                    found_matches.sort(key=sort_key)
                    
                    if 0 <= match_index < len(found_matches):
                        target_match = found_matches[match_index]
                        self.logger.info(f"Vision Fallback (Standart): İndeks {match_index} seçildi (Skor: %{int(target_match[0]*100)})")
                        all_matches.append(target_match)
                    else:
                        all_matches.append(found_matches[0])

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

    def press_key(self, key: str) -> bool:
        self.logger.info(f"Tuşa basılıyor: {key}")
        try:
            pyautogui.press(key)
            return True
        except Exception as e:
            self.logger.error(f"Tuşa basılamadı: {e}")
            return False

    def hotkey(self, keys: list) -> bool:
        self.logger.info(f"Hotkey basılıyor: {' + '.join(keys)}")
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            self.logger.error(f"Hotkey hatası: {e}")
            return False

    def multi_press(self, key: str, count: int) -> bool:
        self.logger.info(f"Çoklu tuş basılıyor: {key} ({count}x)")
        try:
            pyautogui.press(key, presses=count)
            return True
        except Exception as e:
            self.logger.error(f"Çoklu tuş hatası: {e}")
            return False



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

    def kill_process(self, app_name: str) -> bool:
        """Kapatılmak istenen uygulamanın işlemini sonlandırır."""
        try:
            self.logger.info(f"İşlem kapatılıyor: {app_name}")
            # Ensure ending with .exe
            if not app_name.lower().endswith(".exe"):
                app_name += ".exe"
            # Windows command to forcefully kill process
            import subprocess
            CREATE_NO_WINDOW = 0x08000000
            result = subprocess.run(
                ["taskkill", "/f", "/im", app_name],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # returncode returns 0 on success
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Uygulama kapatılamadı ({app_name}): {e}")
            return False

    def scroll(self, amount: int) -> bool:
        try:
            self.logger.info(f"Fare tekerleği ile kaydırılıyor: {amount}")
            pyautogui.scroll(amount)
            return True
        except: return False

    def scroll_until_found(self, target: str, direction: str = "down", step: int = 1000, max_steps: int = 10, timeout: int = 10, match_index: int = 0, click_offset: tuple = (0, 0)) -> bool:
        """Belirtilen görseli bulana kadar kaydırır (Akıllı Kaydırma / Smart Scroll)."""
        self.logger.info(f"Akıllı Kaydırma Başladı: {direction} yönüne, hedef: {os.path.basename(target)}")
        
        # Yön belirle (PyAutoGUI: Pozitif = Yukarı, Negatif = Aşağı)
        scroll_amount = -step if direction == "down" else step
        
        # Fareyi ortaya çek (Hover efektini önle)
        sw, sh = pyautogui.size()
        pyautogui.moveTo(sw//2, sh//2)
        
        for i in range(max_steps):
            # 1. Görseli ARA (Tıklama ile birebir aynı güvenlikte)
            self.logger.info(f"Akıllı Kaydırma: Aranıyor... (Adım {i+1}/{max_steps})")
            
            # Durdurma Kontrolü
            if self.stop_check_callback and self.stop_check_callback(): return False
            
            try:
                # Tıklamadaki orijinal motor parametrelerine dokunmadan arama yapıyoruz.
                # Tıpkı tıklama gibi davranması için confidence vs. eklenmedi, motorun kendi fall-back sistemi çalışsın.
                # Ekranda tarama yapabilmesi için her adımda 1.0 saniye kadar zaman veriyoruz.
                coords = self.wait_for_element(target, timeout=1.0, match_index=match_index, click_offset=click_offset)
                if coords:
                    self.logger.info(f"Akıllı Kaydırma: Hedef bulundu! (Adım {i+1})")
                    return True
            except Exception as e:
                 self.logger.warning(f"Akıllı Kaydırma: Arama hatası (Adım {i+1}): {e}")

            # 2. Bulamazsa KAYDIR (Doğrudan fare tekerleği simülasyonu)
            self.logger.info(f"Akıllı Kaydırma: Bulunamadı, fare tekerleği simüle ediliyor ({i+1}/{max_steps})...")
            try:
                pyautogui.scroll(scroll_amount)
                # Kaydırma sonrası ekranın oturması ve yeni görsellerin render edilmesi için yeterli süre bekle (örneğin 0.5 saniye)
                time.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Akıllı Kaydırma: SCROLL Hatası: {e}")
            
        self.logger.warning("Akıllı Kaydırma: Maksimum adım sayısına ulaşıldı, hedef bulunamadı.")
        return False
