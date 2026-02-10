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
    def __init__(self):
        self.logger = logging.getLogger("StructureDriver")
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
        """Element için benzersiz bir seçici (selector) çıkarır."""
        if not element: return {}
        try:
            selector = {
                "ControlName": element.Name,
                "ControlType": element.ControlTypeName,
                "LocalizedControlType": element.LocalizedControlType, # v87: Yerelleştirilmiş tip adı
                "AutomationId": element.AutomationId,
                "ClassName": element.ClassName,
                # v93: Akıllı Ebeveyn Yakalama
                "ParentName": None,
                "ParentControlType": None,
                # v102: Pencere Kapsamı
                "WindowName": None,
                "WindowClassName": None
            }
            
            # Ebeveyni Yakala (Bir Üst Seviye)
            try:
                parent = element.GetParent()
                if parent:
                    selector["ParentName"] = parent.Name
                    selector["ParentControlType"] = parent.ControlTypeName
            except:
                pass
            
            # v102: Pencere ve Kapsam İndeksini Yakala
            search_scope = None
            try:
                top_level = element.GetTopLevelControl()
                if top_level:
                    selector["WindowName"] = top_level.Name
                    selector["WindowClassName"] = top_level.ClassName
                    search_scope = top_level
            except:
                pass
            
            # Boş değerleri temizle
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
            if "Name" in criteria and control.Name != criteria["Name"]: return False
            if "AutomationId" in criteria and control.AutomationId != criteria["AutomationId"]: return False
            if "ControlType" in criteria and control.ControlTypeId != criteria["ControlType"]: return False
            if "ClassName" in criteria and control.ClassName != criteria["ClassName"]: return False
            return True
        except:
            return False

    def find_element(self, selector: dict, timeout: int = 10):
        """Katı (Strict) ve yerel-bağımsız eşleşme kullanarak elementi bulur (UiPath Tarzı)."""
        if not auto: return None
        
        start_time = time.time()
        self.logger.info(f"Katı Arama: {selector} (Zaman Aşımı: {timeout}s)")
        
        # v81: Eğer çapa (Anchor) kullanıyorsak, Ebeveyn kapsamında sığ arama yapmak isteriz
        search_depth = 0xFFFFFFFF
        root = auto.GetRootControl()

        # 1. Kriterleri Hazırla
        # Stringler (Dil bağımlı) yerine Integer ID'lere (Platform bağımsız) güveniyoruz.
        criteria = {}
        
        # İsim (Name)
        if selector.get("ControlName"): 
            criteria["Name"] = selector["ControlName"]
            
        # Otomasyon ID (AutomationId)
        if selector.get("AutomationId"): 
            criteria["AutomationId"] = selector["AutomationId"]
            
        # Sınıf Adı (ClassName - Opsiyonel ama iyi)
        if selector.get("ClassName"):
            criteria["ClassName"] = selector["ClassName"]

        # Kontrol Tipi (Control Type)
        # String -> Int dönüşümü yapmalıyız. Başarısız olursak filtrelemeye eklemeyiz.
        if selector.get("ControlType"):
            type_id = self._get_control_type_id(selector["ControlType"])
            if type_id:
                criteria["ControlType"] = type_id

        # v99: İndeks Desteği
        target_index = selector.get("foundIndex", 1) # Varsayılan: 1. eşleşme

        while time.time() - start_time < timeout:
            try:
                # v81: Çapa Mantığı (Sibling Fallback ile - v85)
                # Eğer seçicide 'anchor' varsa, önce çapayı bulmalıyız.
                search_scope = None
                
                if "anchor" in selector:
                    anchor_sel = selector["anchor"]
                    self.logger.info(f"Çapa Aranıyor: {anchor_sel.get('ControlName', 'Bilinmiyor')}")
                    
                    # Çapayı Bul (Özyinelemeli çağrı)
                    anchor_element = self.find_element(anchor_sel, timeout=1) 
                    
                    if anchor_element and anchor_element.Exists(0.1):
                        self.logger.info("Çapa BULUNDU!")
                        
                        # Strateji A: Ebeveyn Kapsamı (İdeal)
                        # Hedefi ebeveyn kapsamı İÇİNDE bulmaya çalışırız.
                        # Eğer orada bulamazsak YUKARI tırmanmalıyız.
                        
                        current_scope_element = None
                        
                        try:
                            parent = anchor_element.GetParentControl()
                            if parent:
                                current_scope_element = parent
                                self.logger.info("Çapa Stratejisi A: Ebeveyn Kapsamı Kontrol Ediliyor...")
                                pass
                        except:
                            self.logger.warning("Çapa Stratejisi A Başarısız: Ebeveyn alınamadı.")

                        # Strateji C: Yukarı Tırman (Grandparent / Great-Grandparent) - v85.2
                        # "Kuzen" problemini çözer (div/div/label vs div/div/input)
                        # 3 seviyeye kadar yukarı deneriz.
                        
                        found_valid_scope = False
                        climber = anchor_element
                        
                        for level in range(3): # 0=Parent, 1=Grandparent, 2=GreatGrandparent
                            try:
                                climber = climber.GetParentControl()
                                if not climber: break
                                
                                # Hedef bu kapsamda var mı kontrol et?
                                # Hızlı kontrol için geçici kriterler
                                val_criteria = criteria.copy()
                                if not val_criteria: 
                                    pass
                                    
                                # Hızlı Kontrol: Bu kapsam hedefi içeriyor mu?
                                # Tek bir eşleşme bulmak için WalkControl kullan
                                found_in_scope = False
                                for _ in auto.WalkControl(climber, maxDepth=2 + level): # Sığ kontrol
                                     if self._matches_criteria(_, criteria):
                                         found_in_scope = True
                                         break
                                
                                if found_in_scope:
                                    search_scope = climber
                                    self.logger.info(f"Çapa Stratejisi C: Ortak ata Seviye {level+1} bulundu (Kapsam: {climber.Name} {climber.ClassName})")
                                    found_valid_scope = True
                                    break
                                else:
                                    self.logger.debug(f"Çapa Stratejisi C: Hedef Seviye {level+1} kapsamında bulunamadı. Tırmanılıyor...")
                                    
                            except Exception as e:
                                self.logger.warning(f"Çapa Tırmanma Hatası (Seviye {level}): {e}")
                                break
                        
                        if not found_valid_scope:
                            pass
                            # Aşağıda global aramaya (fallback) düşecek.
                            
                        # Strateji B: Kardeş Kapsamı (Ebeveyn başarısızsa veya güvenli olmak istiyorsak)
                        # NOT: Ebeveyn almak genelde daha güvenlidir çünkü Hedef ağaçta Çapa'dan ÖNCE olabilir.
                        if not search_scope:
                            try:
                                next_sibling = anchor_element.GetNextSiblingControl()
                                if next_sibling:
                                    search_scope = next_sibling
                                    self.logger.info("Çapa Stratejisi B: Sonraki Kardeş Kapsamı kullanılıyor.")
                            except:
                                self.logger.warning("Çapa Stratejisi B Başarısız: Sonraki Kardeş alınamadı.")
                                
                    else:
                        self.logger.warning("Çapa BULUNAMADI. Geri çekilme (Global Arama) deneniyor...")

                # Kök Kapsamı Belirle
                current_root = root
                if search_scope:
                     current_root = search_scope
                
                # Pencere Kapsamı (Opsiyonel ama önerilir)
                elif selector.get("WindowName"):
                    # İsme göre Hızlı Pencere Araması
                    win_params = {"Name": selector["WindowName"], "ControlTypeName": "WindowControl"}
                    if selector.get("WindowClassName"): win_params["ClassName"] = selector["WindowClassName"]
                    
                    # Pencereyi bulmaya çalış
                    window_candidate = root.WindowControl(Name=selector["WindowName"], searchDepth=1)
                    if not window_candidate.Exists(0.1):
                        pass 
                    else:
                        current_root = window_candidate
                        
                # Birincil Arama (Katı) - Artık muhtemelen 'current_root' kapsamında
                if len(criteria) > 0:
                    # Gürültü Filtreleme: ClassName CSS sınıfları içeriyorsa katı aramada sorun çıkarabilir.
                    # Şimdilik katı aramayı KATI tutalım, aşağıda esnek fallback var.
                    
                    if target_index > 1:
                        matches = []
                        for ctrl, _ in auto.WalkControl(current_root, maxDepth=search_depth):
                            if self._matches_criteria(ctrl, criteria):
                                matches.append(ctrl)
                                if len(matches) >= target_index:
                                    break
                        if len(matches) >= target_index:
                            candidate = matches[target_index - 1]
                    else:
                        # İndeks 1 için Hızlı Yol
                        candidate = current_root.Control(**criteria, searchDepth=search_depth)
                
                # Geri Çekilme Stratejileri (v120: Sağlamlık)
                if not candidate or not candidate.Exists(0.1):
                    # Strateji 1: ClassName'i Yoksay (Eğer kullanıldıysa)
                    if "ClassName" in criteria:
                        relaxed = criteria.copy()
                        del relaxed["ClassName"]
                        self.logger.info("Fallback 1: ClassName yoksayılıyor...")
                        candidate = current_root.Control(**relaxed, searchDepth=search_depth)

                if not candidate or not candidate.Exists(0.1):
                    # Strateji 2: Bulanık İsim Eşleşmesi (İçerir / Contains)
                    if "Name" in criteria and len(criteria["Name"]) > 5:
                         partial_name = criteria["Name"][:20] # İlk 20 karakter
                         self.logger.info(f"Fallback 2: Bulanık İsim Araması ('{partial_name}')...")
                         
                         for ctrl, _ in auto.WalkControl(current_root, maxDepth=1): 
                             
                             if "ControlType" in criteria and ctrl.ControlTypeId != criteria["ControlType"]:
                                 continue
                                 
                             # İsim İçeriyor mu?
                             if partial_name in ctrl.Name:
                                 candidate = ctrl
                                 break
                                 
                if not candidate or not candidate.Exists(0.1):
                    # Strateji 3: AutomationId'ye Güven (UiPath Tarzı: ID Kraldır 👑)
                    # İsim değişmiş olabilir ama ID sabit kalabilir.
                    if "AutomationId" in criteria:
                         trust_id_criteria = {"AutomationId": criteria["AutomationId"]}
                         if "ControlType" in criteria:
                             trust_id_criteria["ControlType"] = criteria["ControlType"]
                             
                         self.logger.info("Fallback 3: AutomationId'ye güveniliyor (İsim yoksayılıyor)...")
                         candidate = current_root.Control(**trust_id_criteria, searchDepth=search_depth)

                if not candidate or not candidate.Exists(0.1):
                     # Strateji 4: AutomationId'yi Yoksay, İsme Güven (Son Çare)
                     if target_index == 1 and "AutomationId" in criteria and "Name" in criteria:
                          relaxed = criteria.copy()
                          del relaxed["AutomationId"]
                          self.logger.info("Fallback 4: AutomationId yoksayılıyor, İsme güveniliyor...")
                          candidate = current_root.Control(**relaxed, searchDepth=search_depth)

                # Otomatik Ebeveyn Doğrulama (v95) 🛡️
                # Eğer ebeveyn bilgisi varsa, yanlış pozitifleri elemeli (örn: li vs h1)
                if candidate and candidate.Exists(0.1):
                    parent_type = selector.get("ParentControlType")
                    parent_name = selector.get("ParentName")
                    
                    if parent_type or parent_name:
                        try:
                            cand_parent = candidate.GetParent()
                            if cand_parent:
                                if parent_type and cand_parent.ControlTypeName != parent_type:
                                    self.logger.warning(f"Ebeveyn Uyuşmazlığı! Beklenen Tip: {parent_type}, Alınan: {cand_parent.ControlTypeName}. Reddediliyor.")
                                    candidate = None # Reddet
                                elif parent_name and cand_parent.Name != parent_name:
                                     # İsim kontrolü esnek olabilir, şimdilik sadece uyar.
                                     pass
                        except:
                            pass # Ebeveyn alınamadı, güvenli varsay?

                if candidate and candidate.Exists(0.1):
                    return candidate

            except Exception:
                pass
            
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
