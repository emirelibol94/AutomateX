import time
import os # v167.3: Fix missing import
import logging
import threading
from typing import Callable, Optional

from drivers.base_driver import BaseDriver
from core.scenario import Scenario, Action

class AutomationRunner:
    def __init__(self, driver: BaseDriver, db=None):
        self.driver = driver
        self.db = db
        # v73: Inject stop callback to driver if supported
        # v167.47: Inject stop callback to StructureDriver too
        stop_lambda = lambda: self.stop_requested
        if hasattr(self.driver, 'stop_check_callback'):
            self.driver.stop_check_callback = stop_lambda
            
        self.logger = logging.getLogger("Runner")
        self.is_running = False
        self.stop_requested = False
        self.current_thread = None
        self.action_delay = 0.5 # Default delay in seconds
        self.variables = {} # v167.16: Senaryo Değişkenleri

        # v168: Global ESC abort listener (using pynput instead of keyboard)
        try:
            from pynput import keyboard
            def on_press(key):
                if key == keyboard.Key.esc:
                    self.stop()
            self.esc_listener = keyboard.Listener(on_press=on_press)
            self.esc_listener.daemon = True
            self.esc_listener.start()
        except Exception as e:
            self.logger.warning(f"Global ESC tuşu ayarlanamadı: {e}")

    def run_scenario(self, scenario: Scenario, on_step_complete: Optional[Callable] = None, on_finish: Optional[Callable] = None, start_index: int = 0):
        """
        Senaryoyu ayrı bir iş parçacığında (thread) çalıştırır.
        UI'ın donmasını engellemek için arka planda işlem yapar.
        start_index: Senaryonun hangi adımından başlayacağını belirtir (0-based).
        """
        if self.is_running:
            self.logger.warning("Şu anda zaten bir senaryo çalışıyor.")
            if on_finish:
                on_finish(False, "Başka bir senaryo halihazırda çalışıyor.")
            return

        self.stop_requested = False
        self.is_running = True
        
        def _run():
            self.logger.info(f"Senaryo başlatıldı: {scenario.name} (Başlangıç Adımı: {start_index + 1})")
            success = True
            error_msg = ""
            
            try:
                # v167.17: Senaryo bazlı değişkenleri yükle
                self.variables = scenario.variables.copy() if scenario.variables else {} 
                self.logger.info(f"Senaryo Değişkenleri Yüklendi: {self.variables}")
            
                # v160.3: Start From Here Support
                actions_to_run = scenario.actions[start_index:]
                
                if not actions_to_run:
                    self.logger.warning("Çalıştırılacak adım bulunamadı.")

                # v160.4: Auto-Focus Logic (Debug Start)
                # Eğer ortadan başladıysak, daha önce hangi uygulama açıldıysa onu bulup öne getirelim.
                if start_index > 0:
                    self.logger.info("Debug modu: Hedef uygulama taranıyor...")
                    import os
                    found_target = False
                    
                    # Geriye doğru tara (start_index - 1 down to 0)
                    for i in range(start_index - 1, -1, -1):
                        act = scenario.actions[i]
                        if act.type == "LAUNCH_APP":
                            path = act.params.get("path")
                            if path:
                                # v167.39: Fix - Auto-Focus için tam adı kullan (Process Match için .exe uzantısı şart)
                                app_name = os.path.basename(path)
                                self.logger.info(f"Hedef uygulama bulundu (Adım {i+1}): {app_name}")
                                # Sadece öne getirmeyi dene (Driver'da var olan logic)
                                # DesktopDriver olup olmadığını kontrol etsek iyi olur ama base driver'da yoksa patlamasın
                                if hasattr(self.driver, 'bring_to_front'):
                                    self.driver.bring_to_front(app_name)
                                found_target = True
                                break
                        elif act.type == "OPEN_URL":
                            self.logger.info(f"Hedef tarayıcı bulundu (Adım {i+1})")
                            if hasattr(self.driver, 'bring_to_front'):
                                self.driver.bring_to_front("browser")
                            found_target = True
                            break
                    
                    if not found_target:
                        self.logger.info("Auto-Focus: Öne getirilecek aktif bir uygulama/tarayıcı bulunamadı.")
                    else:
                        self.logger.info("Auto-Focus: Hedef uygulama/tarayıcı odaklama sinyali gönderildi.")
                
                # Note: We need to keep track of the REAL index for logging/UI updates
                for relative_index, action in enumerate(actions_to_run):
                    real_index = start_index + relative_index
                    
                    if self.stop_requested:
                        self.logger.info("Senaryo kullanıcı tarafından durduruldu.")
                        success = False
                        error_msg = "Kullanıcı durdurdu."
                        break

                    self.logger.info(f"Adım {real_index + 1}/{len(scenario.actions)}: {action.type} - {action.description}")
                    
                    # Küresel stabilizasyon gecikmesi
                    if real_index > 0: # Changed from 'index' to 'real_index'
                        # v73: Durdurma kontrolü yapan stabilizasyon gecikmesi
                        delay_start = time.time()
                        while time.time() - delay_start < self.action_delay:
                            if self.stop_requested: break
                            time.sleep(0.05)
                        
                    step_success = self._execute_action(action)

                    if on_step_complete:
                        on_step_complete(real_index, step_success, action)

                    if not step_success:
                        self.logger.error(f"Adım başarısız: {action.description}")
                        success = False
                        error_msg = f"Adım başarısız: {real_index+1}" # Changed from 'index' to 'real_index'
                        # Başarısızlık durumunda durdurmalı mı? Şimdilik evet.
                        break
                    
            except Exception as e:
                self.logger.error(f"Senaryo yürütülürken beklenmeyen hata: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                success = False
                error_msg = f"Kritik Hata: {str(e)}"
                
            finally:
                self.is_running = False
                self.logger.info(f"Senaryo tamamlandı. Başarılı: {success}")
                if on_finish:
                    on_finish(success, error_msg)

        self.current_thread = threading.Thread(target=_run)
        self.current_thread.daemon = True
        self.current_thread.start()

    def stop(self):
        """Çalışan senaryoyu durdurma sinyali gönderir."""
        if self.is_running:
            self.stop_requested = True
            self.logger.info("Durdurma isteği gönderildi...")

    def _substitute_variables(self, text):
        """v167.16: Metin içindeki {degisken} ifadelerini değerleriyle değiştirir."""
        if not isinstance(text, str): return text
        if not self.variables: return text
        
        for var_name, var_value in self.variables.items():
            placeholder = f"${{{var_name}}}" # v167.19: Format changed to ${var}
            if placeholder in text:
                text = text.replace(placeholder, str(var_value))
        return text

    def _execute_action(self, action: Action) -> bool:
        try:
            # v167.16: Değişken Tanımlama
            if action.type == "DEFINE_VARIABLES":
                vars_list = action.params.get("variables", [])
                for v in vars_list:
                    self.variables[v["name"]] = v["value"]
                self.logger.info(f"Değişkenler tanımlandı: {self.variables}")
                return True

            if action.type == "CLICK":
                target = action.params.get("target")
                # Variable Substitution
                if isinstance(target, str): target = self._substitute_variables(target)
                
                text_hint = action.params.get("text_hint")
                if text_hint: text_hint = self._substitute_variables(text_hint)
                
                button = action.params.get("button", "left")
                timeout = int(action.params.get("timeout", 10))
                confidence = action.params.get("confidence")
                # v63: Action modelinden yeni parametreler
                return self.driver.click(
                    target, 
                    timeout=timeout, 
                    text_hint=text_hint, 
                    button=button, 
                    confidence=confidence,
                    match_index=action.match_index,
                    click_offset=action.offset
                )
            
            elif action.type == "TYPE":
                text = action.params.get("text", "")
                text = self._substitute_variables(text) # v167.16
                interval = action.params.get("interval", 0.1)
                return self.driver.type_text(text, interval)
            
            elif action.type == "WAIT":
                seconds = float(action.params.get("seconds", 1.0))
                self.driver.wait(seconds)
                return True
            
            elif action.type == "LAUNCH_APP":
                path = action.params.get("path")
                path = self._substitute_variables(path) # v167.16
                return self.driver.launch_app(path)

            elif action.type == "KILL_PROCESS":
                app_name = action.params.get("app_name")
                app_name = self._substitute_variables(app_name) # v167.16
                return self.driver.kill_process(app_name)

            elif action.type == "OPEN_URL":
                url = action.params.get("url")
                url = self._substitute_variables(url) # v167.16
                return self.driver.open_url(url)
            
            elif action.type == "ASSERT_EXISTS":
                target = action.params.get("target")
                timeout = int(action.params.get("timeout", 10))
                return self.driver.assert_exists(
                    target, 
                    timeout=timeout,
                    match_index=action.match_index,
                    click_offset=action.offset
                )

            # v167.24: CHECK_TEXT Action (Assertion)
            elif action.type == "CHECK_TEXT":
                variable_name = action.params.get("variable")
                expected_value = action.params.get("value")
                condition = action.params.get("condition", "equals") # equals, contains
                
                # Get variable value
                actual_value = str(self.variables.get(variable_name, ""))
                expected_value = self._substitute_variables(str(expected_value))
                
                self.logger.info(f"CHECK_TEXT: ${{{variable_name}}} ('{actual_value}') vs '{expected_value}' ({condition})")
                
                if condition == "equals":
                    if actual_value == expected_value:
                        self.logger.info("CHECK_TEXT: Başarılı (Eşit)")
                        return True
                    else:
                        self.logger.error(f"CHECK_TEXT: Başarısız! Beklenen: '{expected_value}', Gelen: '{actual_value}'")
                        return False
                        
                elif condition == "contains":
                    if expected_value in actual_value:
                        self.logger.info("CHECK_TEXT: Başarılı (İçeriyor)")
                        return True
                    else:
                        self.logger.error(f"CHECK_TEXT: Başarısız! '{actual_value}', '{expected_value}' içermiyor.")
                        return False
                
                return False

            elif action.type == "POPUP_CHECK":
                triggers = action.params.get("triggers", [])
                any_clicked = False
                
                for trig in triggers:
                    t_type = trig.get("type")
                    t_value = trig.get("value") # Name
                    
                    try:
                        if t_type == "image":
                            # Asset'ten görseli al, geçici dosyaya yaz
                            if hasattr(self.driver, 'db') and self.driver.db:
                                asset_row = self.driver.db.get_asset_by_name(t_value)
                                if asset_row:
                                    # (id, name, data, type, created)
                                    blob = asset_row[2]
                                    import tempfile
                                    
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                                        tmp.write(blob)
                                        tmp_path = tmp.name
                                    
                                    try:
                                        # Click dene
                                        if self.driver.click(tmp_path, timeout=2, confidence=0.8):
                                            self.logger.info(f"Pop-up yakalandı ve tıklandı (Görsel): {t_value}")
                                            any_clicked = True
                                            break # v160.8: Bir tane bulunduysa dur.
                                    finally:
                                        try:
                                            # import os # v167.4: Removed local import
                                            os.remove(tmp_path)
                                        except: pass

                    except Exception as e:
                        self.logger.warning(f"Pop-up tetikleyici hatası ({t_value}): {e}")
                
                # Pop-up olsa da olmasa da bu adım başarılı sayılır (Blocking değil)
                return True
            
            elif action.type == "VALIDATE_WINDOW":
                title = action.params.get("title")
                timeout = int(action.params.get("timeout", 5))
                return self.driver.validate_window(title, timeout)

            elif action.type == "VALIDATE_ELEMENT":
                window_title = action.params.get("window_title")
                element_name = action.params.get("element_name")
                timeout = int(action.params.get("timeout", 5))
                return self.driver.validate_element(window_title, element_name, timeout)
            
            elif action.type == "PRESS_KEY":
                key = action.params.get("key")
                return self.driver.press_key(key)

            elif action.type == "HOTKEY":
                keys = action.params.get("keys", [])
                return self.driver.hotkey(keys)

            elif action.type == "MULTI_PRESS":
                key = action.params.get("key")
                count = action.params.get("count", 1)
                return self.driver.multi_press(key, count)

            elif action.type == "SCROLL":
                amount = int(action.params.get("amount", 0))
                return self.driver.scroll(amount)

            elif action.type == "SCROLL_UNTIL":
                direction = action.params.get("direction", "down")
                step = int(action.params.get("step", 500)) # v167.14: Default 300 -> 500
                max_steps = int(action.params.get("max_steps", 10))
                
                target = action.params.get("target")
                
                # v165.0: Library Asset Support
                tmp_target = None
                # Check if target is a file path; if not, assume it might be a library asset name
                # But first, we need to handle if target is None
                if target and not os.path.exists(target):
                    # v167.1: Use self.db instead of self.driver.db
                    if self.db:
                        asset_row = self.db.get_asset_by_name(target)
                        if asset_row:
                            blob = asset_row[2]
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                                tmp.write(blob)
                                tmp_target = tmp.name
                            target = tmp_target
                            self.logger.info(f"Kütüphane görseli kullanılıyor: {tmp_target}")
                
                try:
                    return self.driver.scroll_until_found(
                        target, 
                        direction, 
                        step=step, 
                        max_steps=max_steps,
                        match_index=action.match_index,
                        click_offset=action.offset
                    )
                finally:
                    if tmp_target:
                        try: os.remove(tmp_target)
                        except: pass

            elif action.type == "READ_TEXT":
                region = action.params.get("region")
                result = self.driver.read_text(region)
                action.result = result
                return True
            
            elif action.type == "HANDLE_POPUP":
                target = action.params.get("target")
                return self.driver.handle_popup(target)

            else:
                self.logger.error(f"Bilinmeyen aksiyon tipi: {action.type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Aksiyon hatası ({action.type}): {e}")
            return False
