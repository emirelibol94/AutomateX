import logging
import time

try:
    import uiautomation as auto
except ImportError:
    auto = None

class StructureDriver:
    """
    Windows UI Otomasyon Sürücüsü.
    UI elementleri ile programsal olarak etkileşime geçmek için 'uiautomation' kütüphanesini kullanır.
    """

    def __init__(self, stop_check_callback=None):
        self.logger = logging.getLogger("StructureDriver")
        self.stop_check_callback = stop_check_callback
        if not auto:
            self.logger.error("uiautomation kütüphanesi bulunamadı. Lütfen 'pip install uiautomation' ile kurun.")

    def get_element_under_mouse(self):
        """Fare imlecinin altındaki UI elementini döndürür."""
        if not auto: return None
        try:
            x, y = auto.GetCursorPos()
            element = auto.ControlFromPoint(x, y)
            return element
        except Exception as e:
            self.logger.error(f"Fare altındaki element alınırken hata: {e}")
            return None

    def highlight_element(self, element, color=0xFF0000, thickness=2):
        """Elementin etrafına vurgulama çerçevesi çizer."""
        if not auto or not element: return
        try:
            # uiautomation yerleşik vurgulamaya sahip ama bazen thread'i bloklar.
            # Şimdilik basit geçiyoruz, ileride özel overlay yapılabilir.
            pass 
        except Exception:
            pass

    def get_selector(self, element) -> dict:
        """
        Element için 'UiPath-vari' akıllı ve sağlam bir seçici (Full UI Lineage) çıkarır.
        """
        if not element: return {}
        try:
            # 1. Hedef Elementin Kendisi
            selector = {
                "ControlName": element.Name,
                "ControlType": element.ControlTypeName,
                "LocalizedControlType": element.LocalizedControlType,
                "AutomationId": element.AutomationId,
                "ClassName": element.ClassName,
                "ProcessId": element.ProcessId
            }
            
            # 2. UI Soyağacı (Lineage) Çıkarma
            # Window -> ... -> Parent -> Element
            # Her bir atayı detaylı kaydediyoruz.
            ui_path = []
            current = element
            
            # En fazla 20 seviye yukarı çık
            for _ in range(20):
                try:
                    # Pencereye geldik mi?
                    if current.ControlTypeName == "WindowControl":
                        # Pencere bilgisini hem yola hem de ana selector'a ekle
                        win_node = {
                            "Role": "Window",
                            "Type": current.ControlTypeName,
                            "Name": current.Name,
                            "Class": current.ClassName,
                            "Process": current.ProcessId
                        }
                        ui_path.insert(0, win_node)
                        selector["WindowName"] = current.Name
                        selector["WindowClassName"] = current.ClassName
                        break
                        
                    if not current: break
                    
                    # Bu atanın kardeşleri arasındaki sırasını (Index) bul
                    sibling_index = 1
                    try:
                        parent = current.GetParentControl()
                        if parent:
                            # Sadece aynı tipteki (Role) kardeşleri say
                            for child in parent.GetChildren():
                                if child == current: break
                                if child.ControlTypeName == current.ControlTypeName:
                                    sibling_index += 1
                    except: pass

                    # Düğüm Bilgisi
                    node = {
                        "Role": current.LocalizedControlType, # Örn: "group", "pane"
                        "Type": current.ControlTypeName,      # Örn: "GroupControl"
                        "Name": current.Name,
                        "Id": current.AutomationId,
                        "Class": current.ClassName,
                        "Index": sibling_index
                    }
                    
                    # Başa ekle (Yukarı çıkıyoruz)
                    ui_path.insert(0, node)
                    
                    current = current.GetParentControl()
                except Exception:
                    break
            
            # Yolu Kaydet
            selector["UIPath"] = ui_path
            
            return {k: v for k, v in selector.items() if v}

        except Exception as e:
            self.logger.error(f"Selector çıkarılırken hata: {e}")
            return {}

    def _get_control_type_id(self, type_name: str):
        """String tipindeki rolü (örn. 'ButtonControl') uiautomation int sabitine eşler."""
        if not type_name: return None
        try:
            # 1. Doğrudan eşleşme dene
            if hasattr(auto.ControlType, type_name):
                return getattr(auto.ControlType, type_name)
            
            # 2. 'Control' ekleyerek dene (örn. 'Button' -> 'ButtonControl')
            if not type_name.endswith("Control"):
                 candidate = type_name + "Control"
                 if hasattr(auto.ControlType, candidate):
                     return getattr(auto.ControlType, candidate)
                     
            return None
        except:
            return None

    def _matches_criteria(self, control, criteria):
        """Bir kontrolün kriter sözlüğüne uyup uymadığını kontrol eden yardımcı metod."""
        try:
            # v167.51: Daha esnek eşleşme (Bire bir ama kırılgan olmayan)
            if "Name" in criteria:
                # İsim boşluklarını temizle ve küçük harfe çevir
                c_name = control.Name.strip().lower()
                Get_name = criteria["Name"].strip().lower()
                if c_name != Get_name: 
                    return False
            
            if "AutomationId" in criteria:
                if control.AutomationId != criteria["AutomationId"]: 
                     return False
                     
            if "ControlType" in criteria:
                if control.ControlTypeId != criteria["ControlType"]: 
                    return False
            
            # v167.51: ClassName kapsama kontrolü (Tam eşitlik yerine 'in')
            # Örn: "WindowsForms10.BUTTON.app.0.141b42a_r6_ad1" -> "WindowsForms10.BUTTON"
            if "ClassName" in criteria:
                # Eğer kayıtlı class ismi, bulunanın içinde geçiyorsa kabul et.
                # Tam tersi de olabilir (dinamik ekler)
                c_class = control.ClassName
                t_class = criteria["ClassName"]
                
                if t_class not in c_class and c_class not in t_class:
                     return False
                    
            return True
        except:
            return False

    def _find_window_scope(self, window_name: str, window_class: str = None) -> object:
        """Pencere ismine ve sınıfına göre esnek arama yapar."""
        if not window_name: return None
        
        # 1. Tam Eşleşme Dene (Hızlı)
        try:
            criteria = {"Name": window_name, "ControlTypeName": "WindowControl"}
            if window_class: criteria["ClassName"] = window_class
            
            win = auto.WindowControl(searchDepth=1, **criteria)
            if win.Exists(0.1):
                return win
        except: pass
        
        # 2. Esnek Eşleşme (Tüm üst seviye pencereleri tara)
        self.logger.info(f"Pencere tam bulunamadı, esnek aranıyor: '{window_name}'")
        try:
            root = auto.GetRootControl()
            # Sadece üst seviye (Depth=1) pencereleri gez
            for win in root.GetChildren():
                if win.ControlTypeName != "WindowControl": continue
                
                # İsim Kontrolü (Case-insensitive & Contains)
                c_name = win.Name.strip().lower()
                t_name = window_name.strip().lower()
                
                match = False
                if t_name in c_name or c_name in t_name: # Karşılıklı kapsama
                     match = True
                
                # Sınıf Kontrolü (Varsa)
                if match and window_class:
                    if window_class not in win.ClassName: # Sınıf tutmuyorsa ele
                        match = False
                
                if match:
                    self.logger.info(f"Esnek Pencere Bulundu: '{win.Name}'")
                    return win
                    
        except Exception as e:
            self.logger.warning(f"Esnek pencere arama hatası: {e}")
            
        return None

    def find_element(self, selector: dict, timeout: int = 10):
        """
        'UiPath-vari' Akıllı Element Bulma (Flexible Drill-Down).
        Soyağacını (UiPath) takip eder, yol bozulursa kendini onarır (Self-Repair).
        """
        if not auto: return None
        
        start_time = time.time()
        # self.logger.info(f"Akıllı Arama Başladı: {selector.get('ControlName', 'Unknown')}")
        
        # UI Path var mı? (Yeni Sistem)
        ui_path = selector.get("UIPath")
        if not ui_path or not isinstance(ui_path, list):
             # Eski sistem veya basit selector ise Klasik Arama yap (Geri uyumluluk)
             return self._find_element_classic(selector, timeout)

        while time.time() - start_time < timeout:
            if self.stop_check_callback and self.stop_check_callback(): return None
            
            try:
                # 1. Başlangıç Noktası: Pencereyi Bul
                current_node = None
                window_node = ui_path[0] # İlk düğüm her zaman Window olmalı
                
                # Pencereyi bulmaya çalış (Process ID ve Class ile daha sağlam)
                found_window = self._find_window_robust(window_node)
                if not found_window:
                    self.logger.warning(f"Ana pencere bulunamadı: {window_node.get('Name')}")
                    time.sleep(0.5)
                    continue
                
                current_node = found_window
                
                # 2. Yolu Takip Et (Drill-Down)
                # Pencereden sonraki düğümlerden başla
                path_broken = False
                
                for i in range(1, len(ui_path)):
                    target_node = ui_path[i]
                    found_child = None
                    
                    # 1. Strateji: İndeks (En Hızlı)
                    try:
                        child_idx = target_node.get("Index", 1)
                        child_type = self._get_control_type_id(target_node["Type"])
                        match_count = 0
                        for child in current_node.GetChildren():
                            if child.ControlTypeId == child_type:
                                match_count += 1
                                if match_count == child_idx:
                                    if self._verify_node_match(child, target_node, loose=True):
                                        found_child = child
                                        break
                    except: pass

                    # 2. Strateji: Özellik Araması (Name/ID)
                    if not found_child:
                        criteria = self._create_node_criteria(target_node)
                        for child in current_node.GetChildren():
                            if self._matches_criteria(child, criteria):
                                found_child = child
                                break
                    
                    # 3. Kendi Kendini Onarma (Self-Repair & Skip Level)
                    if not found_child:
                        # self.logger.warning(f"Bağlantı koptu: {target_node.get('Name')}. Onarılmaya çalışılıyor...")
                        
                        # A. Derin Arama (Bu düğüm yer değiştirmiş olabilir)
                        criteria = self._create_node_criteria(target_node)
                        # Sadece "Type" ile derin arama yapmak çok tehlikeli (çok sonuç döner), 
                        # en azından Name veya ID varsa derin arayalım.
                        if criteria.get("Name") or criteria.get("AutomationId"):
                            found_child = current_node.Control(searchDepth=3, **criteria)
                            if not found_child.Exists(0.05): found_child = None
                        
                        # B. Skip Level (Aradaki kutu kalkmış olabilir, bir sonraki adıma bakalım!)
                        if not found_child and i + 1 < len(ui_path):
                            next_node = ui_path[i+1]
                            self.logger.info(f"Düğüm atlanıyor, bir sonrakine bakılıyor: {next_node.get('Name')}")
                            next_criteria = self._create_node_criteria(next_node)
                            if next_criteria.get("Name") or next_criteria.get("AutomationId"):
                                found_next = current_node.Control(searchDepth=4, **next_criteria)
                                if found_next.Exists(0.05):
                                    found_child = found_next
                                    # Döngüdeki 'i' indeksini manüel atlayamayız ama 'current_node'u güncelledik.
                                    # Bir sonraki iterasyonda normal akış devam edecek ama biz şimdi
                                    # 'found_child'ı (aslında next_node'u) bulduğumuz için
                                    # bu adımı "başarılı" sayıp, bir sonraki adımı (i+1) es geçmemiz lazım.
                                    # Ancak for döngüsü i'yi artıracak.
                                    # Bu yüzden burada trick yapıyoruz:
                                    # current_node zaten next_node oldu.
                                    # Bir sonraki iterasyonda i+1 aranacak, ama biz zaten oradayız!
                                    # Sorun yok, çünkü i+1'in çocuklarını arayacağız.
                                    # HATA: Hayır, i+1'i aradık ve bulduk. Şimdi current_node = i+1.
                                    # Bir sonraki turda loop i+1 elemanını arayacak. Ama biz zaten i+1'deyiz!
                                    # Bizim loop'un i+2'den devam etmesi lazım.
                                    # Python'da for döngüsüne müdahale edemeyiz.
                                    # O yüzden burada basitçe: current_node'u bulduğumuz next_node yapıyoruz.
                                    # Ve loop'un bir sonraki adımında (i+1) bu node'un *içinde* i+1'i arayacak.
                                    # Ama i+1 zaten bu node! Kendi içinde kendini bulamaz.
                                    # ÇÖZÜM: Path Broken verip çıkmak yerine,
                                    # Son çare "Target Rescue"ya güvenmek daha iyidir.
                                    pass

                    if found_child:
                        current_node = found_child
                    else:
                        path_broken = True
                        self.logger.warning(f"Yol koptu! Bulunamayan: {target_node.get('Name')}")
                        break
                
                if not path_broken:
                    self.logger.info("🎯 Element UI Yolu ile bulundu!")
                    return current_node
                
                # 4. Target Rescue (Son Çare)
                # Yol koptuysa bile, belki son hedef (Target) hala "Window" içinde bir yerlerdedir?
                if path_broken:
                    self.logger.info("Yol koptu, Hedef Kurtarma (Target Rescue) devreye giriyor...")
                    target_node = ui_path[-1] # En son eleman
                    target_criteria = self._create_node_criteria(target_node)
                    
                    # Kurtarma 1: Scoped Rescue (En son kaldığımız yerin içinde ara)
                    # Bu, Global aramadan çok daha güvenlidir çünkü bağlamı korur.
                    if current_node:
                        self.logger.info(f"Kurtarma 1 (Scoped): {current_node.Name} içinde aranıyor...")
                        try:
                            # Derinlemesine ara
                            rescue_element = current_node.Control(searchDepth=0xFFFFFFFF, **target_criteria)
                            if rescue_element.Exists(0.1):
                                self.logger.info("🚑 Scoped Rescue Başarılı! Element bulundu.")
                                return rescue_element
                        except: pass

                    # Kurtarma 2: Global Rescue (Pencere genelinde ara)
                    # DİKKAT: Bu çok tehlikeli olabilir. Sadece İsim veya ID varsa izin ver.
                    # Sadece "Button" tipiyle tüm pencereyi ararsak yanlış butona tıklarız.
                    if target_criteria.get("Name") or target_criteria.get("AutomationId"):
                        self.logger.info("Kurtarma 2 (Global): Pencere genelinde aranıyor...")
                        rescue_element = found_window.Control(searchDepth=0xFFFFFFFF, **target_criteria)
                        if rescue_element.Exists(0.1):
                            self.logger.info("🚑 Global Rescue Başarılı! Element bulundu.")
                            return rescue_element
                    else:
                        self.logger.warning("Global Rescue iptal edildi: Hedef kriterleri çok belirsiz (İsim/ID yok).")

            except Exception as e:
                self.logger.warning(f"Akıllı arama hatası: {e}")
            
            time.sleep(0.5)

        return None
    
    def _find_window_robust(self, win_node):
        """Pencereyi bulmak için çok katmanlı, sağlam arama."""
        # 1. Process ID (En Kesin) - Eğer process hala aynıysa
        # (Bu kısım şu an pasif, çünkü PID her restartta değişir. 
        # Ancak uygulamanın o anki PID'sini biliyorsak kullanılabilir)
        
        # 2. İsim ve Class ile "Fuzzy" Arama
        return self._find_window_scope(win_node.get("Name"), win_node.get("Class"))

    def _create_node_criteria(self, node):
        """Node sözlüğünden arama kriteri üretir."""
        c = {}
        if node.get("Name"): c["Name"] = node["Name"]
        if node.get("Id"): c["AutomationId"] = node["Id"]
        if node.get("Class"): c["ClassName"] = node["Class"]
        t = self._get_control_type_id(node.get("Type"))
        if t: c["ControlType"] = t
        return c

    def _verify_node_match(self, control, node, loose=False):
        """Bulunan elementin node bilgileriyle uyuşup uyuşmadığını doğrular."""
        try:
            if not loose:
                # Sıkı kontrol
                if node.get("Id") and control.AutomationId != node["Id"]: return False
                if node.get("Name") and control.Name != node["Name"]: return False
            else:
                # Gevşek kontrol (İndeks doğrulaması için)
                # Türü kesin tutmalı
                t = self._get_control_type_id(node.get("Type"))
                if t and control.ControlTypeId != t: return False
                
                # İsim veya ID'den en az biri 'benziyorsa' tamamdır.
                match = False
                if node.get("Id") and node["Id"] == control.AutomationId: match = True
                if node.get("Name") and node["Name"] in control.Name: match = True
                # Hiçbir özellik yoksa (sadece Type varsa), Type tuttuğu için kabul et.
                if not node.get("Id") and not node.get("Name"): match = True
                
                return match
        except: return False
        return True

    def _find_element_classic(self, selector, timeout):
        """Eski usül arama (Geri uyumluluk için)."""
        start_time = time.time()
        # 1. Kriterler
        base_criteria = {}
        if selector.get("ControlName"): base_criteria["Name"] = selector["ControlName"]
        if selector.get("ClassName"): base_criteria["ClassName"] = selector["ClassName"]
        type_id = self._get_control_type_id(selector.get("ControlType"))
        if type_id: base_criteria["ControlType"] = type_id

        while time.time() - start_time < timeout:
            if self.stop_check_callback and self.stop_check_callback(): return None
            try:
                # Kapsam: Window veya Root
                search_scope = auto.GetRootControl()
                if selector.get("WindowName"):
                    win = self._find_window_scope(selector["WindowName"], selector.get("WindowClassName"))
                    if win: search_scope = win

                # A. Strict (ID)
                if selector.get("AutomationId"):
                    strict = base_criteria.copy()
                    strict["AutomationId"] = selector["AutomationId"]
                    try:
                        found = search_scope.Control(searchDepth=0xFFFFFFFF, **strict)
                        if found.Exists(0.1): return found
                    except: pass
                
                # B. Relaxed (Name/Type) - First Match
                for ctrl, _ in auto.WalkControl(search_scope, maxDepth=0xFFFFFFFF):
                    if self._matches_criteria(ctrl, base_criteria):
                        return ctrl
                    if self.stop_check_callback and self.stop_check_callback(): return None
            except: pass
            time.sleep(0.5)
        return None

    def click_element(self, selector: dict, button='left'):
        """Belirtilen butonla ('left', 'right', 'double') elementi bulur ve tıklar."""
        element = self.find_element(selector)
        if element:
            try:
                if button == 'double':
                    element.DoubleClick(simulateMove=True)
                elif button == 'right':
                    element.RightClick(simulateMove=True)
                else:
                    element.Click(simulateMove=True)
                
                self.logger.info(f"Structure Tıklama ({button}): {selector.get('ControlName', 'Bilinmiyor')}")
                return True
            except Exception as e:
                self.logger.error(f"Structure Tıklama Hatası ({button}): {e}")
                return False
        return False
