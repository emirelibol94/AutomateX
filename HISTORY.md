# AutomateX Gelişim Günlüğü

## [v167.37] - 2026-02-10
- **Davranış Değişikliği**: Senaryo içe aktarma (Import) sonrası otomatik yükleme özelliği, mevcut çalışmayı bozmamak adına kaldırıldı. İçe aktarılan senaryolar artık sadece veritabanına kaydediliyor ve istenildiği zaman "Senaryolar" menüsünden manuel olarak yüklenebiliyor.

## [v167.36] - 2026-02-10
- **Düzeltme**: Değişken tanımlama (Variable Definition) sonrası çıkan gereksiz onay kutuları (MessageBox) kaldırıldı (Sessiz Kayıt).
- **İyileştirme**: Senaryo içe aktarma (Import) sonrası otomatik yükleme mantığı daha güvenli hale getirildi.
- **Güvenlik**: Aynı isimdeki senaryoların veritabanında birbirini ezmemesi için ID tabanlı ayrıştırma korundu.

## [v167.35] - 2026-02-10
- **İyileştirme**: Senaryo içe aktarırken (Import) tek bir senaryo geliyorsa otomatik olarak editöre yükleme özelliği eklendi.
- **Düzeltme**: Senaryo düzeyindeki değişkenlerin dışa aktarma (Export) ve içe aktarma (Import) süreçlerinde korunması ve yüklendikten sonra "Değişken Tanımla" menüsünde görünmesi garanti altına alındı.
- **Mantık**: Değişken tanımlamalarında aynı isimli değişkenlerin alttakinin üsttekini ezme (Last-one-wins) kuralı doğrulandı.

## [v167.34] - 2026-02-10
- **Belgelendirme**: Detaylı `FEATURES.md` oluşturuldu ve `USER_MANUAL.md` kapsamlı bir şekilde güncellendi. Tüm yeni özellikler (Değişkenler, Popup Yakalayıcı, Smart Recorder vb.) kılavuza eklendi.

## [v167.33] - 2026-02-10
- **Düzeltme**: "Popup Yakala" ve "Seçici Kütüphanesi" arayüzü yeniden düzenlendi. Seçim butonları, seçici bilgilerinin altına taşınarak görünümleri garanti altına alındı.

## [v167.32] - 2026-02-10
- **Düzeltme**: "Popup Yakala" ve "Selector Kütüphanesi" pencerelerinde uzun isimli veya detaylı seçicilerin butonları ekrandan taşırması engellendi. İsimler artık kısaltılarak gösteriliyor.

## [v167.31] - 2026-02-10
- **Düzeltme**: `uiautomation` kütüphanesinin bazı sürümlerinde `Exists` fonksiyonunun parametre hatası vermesi düzeltildi (`searchInterval` kaldırıldı).

## [v167.30] - 2026-02-10
- **Düzeltme**: Veri okuma sırasında oluşan `TypeError` hatası giderildi. Pencere öğesi arama yöntemi `auto.Control` kullanacak şekilde güncellendi.

## [v167.29] - 2026-02-10
- **Düzeltme**: `Get Text` fonksiyonunun kayıtlı seçicileri (Selector) tanıması için parametre eşleştirmesi genişletildi. Artık Inspector ile kaydedilen "ControlName" tabanlı seçiciler de sorunsuz okunuyor.

## [v167.28] - 2026-02-10
- **İyileştirme**: "Veri Oku (Get Text)" özelliğinde güvenlik önlemi. Kullanıcı henüz bir değişken tanımlamadıysa işlem engelleniyor ve önce değişken oluşturması isteniyor.

## [v167.27] - 2026-02-10
- **Arayüz Düzenlemesi**: "Hızlı Kayıt (Kütüphane)" butonu görünürlüğünü artırmak için "Depo" bölümüne taşındı.

## [v167.26] - 2026-02-10
- **Hata Düzeltme**: `MainWindow` içinde kaybolan "Hızlı Kayıt Paneli" fonksiyonları geri yüklendi.

## [v167.25] - 2026-02-10
- **Hata Düzeltme**: `DesktopDriver` sınıfında kod birleştirme hatası giderildi (Syntax Error).

## [v167.24] - 2026-02-10
- **Veri Okuma (Get Text)**: Ekranda seçilen bir alandaki metni okuyup değişkene kaydetme özelliği eklendi.
- **Veri Kontrolü (Check Text)**: Bir değişkenin değerini beklenen bir değerle kıyaslama (Eşit mi?, İçeriyor mu?) özelliği eklendi.

## [v167.23] - 2026-02-10
- **Optimizasyon**: Metin yapıştırma işleminde kararsızlık yaratan Windows API (Ctypes) yöntemi kaldırıldı. Artık tüm panoya kopyalama işlemleri, kullanıcının sisteminde başarısı kanıtlanmış olan **PowerShell** altyapısı üzerinden gerçekleştiriliyor. Bu değişiklik değişkenlerin yazımını etkilemez.

## [v167.22] - 2026-02-10
- **Güçlendirilmiş Türkçe Karakter Desteği**: Panoya erişim sorunları için ikinci bir katman eklendi. Standart yöntem (Ctypes) başarısız olursa, uygulama otomatik olarak PowerShell altyapısını kullanarak metni panoya kopyalar. Bu sayede "Kopyala-Yapıştır" işlemi Windows'un kendi araçlarıyla %100 garanti altına alınır.

## [v167.21] - 2026-02-10
- **Düzeltme**: Türkçe karakter yazımında kullanılan "Panoya Kopyala" (Clipboard) sırasında oluşan erişim hatası giderildi. Pano meşgul olduğunda yeniden deneme mekanizması eklendi. Ayrıca hata durumunda uygulamanın çökmesi yerine standart yazıma geçmesi sağlandı.

## [v167.20] - 2026-02-10
- **Türkçe Karakter Desteği**: Metin yazma (Type) işleminde "ç, ğ, ı, ö, ş, ü" gibi Türkçe karakterlerin düzgün yazılmaması sorunu giderildi. Artık metinler "Yapıştır" (Paste) yöntemiyle gönderilerek %100 doğruluk sağlanıyor.

## [v167.19] - 2026-02-10
- **Değişken Formatı Güncellemesi**: Değişken kullanım formatı, alışılagelmiş standartlara uygun olarak `${degisken_adi}` şeklinde değiştirildi. Artık aksiyonlarda (Metin Yazma vb.) değişkenleri bu formatta kullanmalısınız.

## [v167.18] - 2026-02-10
- **Acil Düzeltme**: `ui.main_window` modülünde oluşan ve uygulamanın açılmasını engelleyen bir kod hatası (SyntaxError) giderildi.

## [v167.17] - 2026-02-10
- **Küresel Senaryo Değişkenleri**: Değişkenler artık bir "aksiyon adımı" olarak değil, senaryonun genel bir ayarı olarak kaydediliyor. "Değişken Tanımla" butonu, senaryonun hafızasını düzenleyen özel bir panel açıyor. Bu sayede adım listesi kirlenmeden değişkenler kullanılabiliyor.

## [v167.16] - 2026-02-10
- **Değişken Desteği**: Senaryo içinde String ve Integer tipinde değişkenler tanımlama özelliği eklendi.
- **Dinamik Aksiyonlar**: Metin Yazma (Type), Tıklama (Click), Uygulama Açma (Launch) gibi aksiyonlarda `{degisken_adi}` formatıyla bu değerleri dinamik olarak kullanabilme yeteneği getirildi.

## [v167.15] - 2026-02-09
- **Hiper Hızlı Kaydırma**: Selector arama süresi 1 saniyeden 0.2 saniyeye düşürüldü. Artık sistem, her kaydırma adımında "Element burada mı?" diye çok daha hızlı bakıp geçiyor, bu da kaydırma akıcılığını %400 artırıyor.

## [v167.14] - 2026-02-09
- **Kaydırma Hızı Artırıldı**: Akıllı Kaydırma varsayılan adım miktarı 500 birime çıkarıldı ve her adım arası bekleme süresi 0.5 saniyeden 0.2 saniyeye düşürülerek işlem yaklaşık 2 kat hızlandırıldı.

## [v167.13] - 2026-02-09
- **Kütüphane Veri Sıralaması Düzeltildi**: Veritabanından selector listesi çekilirken sütunların sırası karışıyordu (`tip` ile `içerik` tersti). Bu yüzden program "xpath" yazısını kod sanıyordu. Sıralama düzeltildi, artık kodlar doğru yükleniyor.

## [v167.12] - 2026-02-09
- **Kütüphane Bağlantı Hatası Düzeltildi**: Runner modülünün veritabanına erişirken yaşadığı yetki sorunu (`self.db` yerine `self.driver.db` kullanımı) düzeltildi. Artık kütüphaneden seçilen selector'lar sorunsuz çözülüyor.

## [v167.11] - 2026-02-09
- **Sözdizimi Düzeltmesi**: `runner.py` dosyasında oluşan `IndentationError` (girintileme/try-except bloğu hatası) giderildi.

## [v167.10] - 2026-02-09
- **Paketleme Düzeltmesi**: PyInstaller yapılandırmasına (`.spec`), `core` modülleri (`runner`, `database` vb.) açıkça eklenerek "ModuleNotFoundError" açılış hatası giderildi.

## [v167.9] - 2026-02-09
- **Kütüphane Selector Desteği**: Akıllı Kaydırma aksiyonuna, kütüphaneden seçilen selector'ları (isim olarak gelenleri) veritabanından bulup çözme yeteneği eklendi. "Geçersiz format" hatası giderildi.

## [v167.8] - 2026-02-09
- **Selector Güvenliği**: Akıllı Kaydırma işlemine "Veri Doğrulama Kapısı" eklendi. Bozuk veya hatalı selector verisi gelirse sistem çökmek yerine işlemi güvenli şekilde iptal ediyor.
- **Pencere Odaklama**: Uygulama başlatıldığında hedef pencerenin arkada kalma sorunu, "Agresif Odaklama" (Restore + SetFocus) yöntemiyle çözüldü.

## [v167.7] - 2026-02-09
- **Selector Görünürlük Kontrolü**: Selector ile arama yapıldığında, element ağaçta bulunsa bile eğer ekran dışındaysa (Off-screen) "bulunamadı" sayılarak kaydırmaya devam edilmesi sağlandı.

## [v167.6] - 2026-02-09
- **Yalancı Pozitif Düzeltmesi**: Akıllı Kaydırma sırasında kısa süreli aramalarda yaşanan "hatalı bulma" (false positive) sorunu, güven eşiği %85'e sabitlenerek çözüldü.

## [v167.5] - 2026-02-09
- **Hata Düzeltmesi**: `scroll_until_found` fonksiyonuna eksik olan `match_index` ve `click_offset` parametreleri eklendi. `TypeError` giderildi.

## [v167.4] - 2026-02-09
- **Kritik Hata Düzeltmesi**: `runner.py` içindeki gölgelenmiş `import os` ifadesi kaldırılarak `UnboundLocalError` hatası kesin olarak çözüldü.

## [v167.3] - 2026-02-09
- **Acil Düzeltme**: Kaydırma işlemi sırasında geçici dosya temizliği yapılırken oluşan `os eksik` hatası giderildi.

## [v167.2] - 2026-02-09
- **Gelişmiş Hata Koruması**: Kaydırma (Scroll) işlemleri için "Hata Yakalama" kalkanı eklendi. `pyautogui.scroll` hataları artık akışı durdurmuyor.
- **Detaylı Loglama**: Akıllı Kaydırma adımları (arama/kaydırma) için detaylı loglama eklendi.

## [v167.1] - 2026-02-09
- **Kritik Hata Düzeltmesi**: Kütüphane görsellerinin ve selectorlerin kaydırma sırasında bulunamaması ve işlemi durdurması sorunu giderildi (DB inject eklendi).
- **Selector Kararlılığı**: Selector arama sırasında oluşabilecek hatalara karşı koruma eklendi.

## [v167.0] - 2026-02-09
- **Kesintisiz Seçici Yakalama**: "Yeni Seçici Yakala" modunda Kaydırma penceresi artık ekrandan tamamen kayboluyor.
- **Akıcı İş Akışı**: Seçici kaydedildikten sonra çıkan başarı mesajı kaldırıldı; sistem otomatik olarak Kaydırma ekranına odaklanmış şekilde dönüyor.

## [v166.0] - 2026-02-09
- **Kaydırma Diyaloğu Kararlılığı**: Kütüphaneden görsel seçimi algılama hatası düzeltildi.
- **Kesintisiz Akış**: Selector yakalandıktan sonra Kaydırma diyaloğunun otomatik geri gelmesi sağlandı (Pencere kapanma hatası giderildi).

## [v165.0] - 2026-02-09
- **Kaydırma İyileştirmeleri**: Kütüphaneden seçilen görsellerin akıllı kaydırmada çalışmama sorunu giderildi.
- **🎯 Yerinden Yakala (Smart Selector)**: Kaydırma ekranından çıkmadan yeni bir selector yakalayıp kütüphaneye ekleme ve anında seçme özelliği getirildi.
- **Arayüz Optimizasyonu**: Kaydırma ekranındaki buton yerleşimleri ve "Ekle" butonunun görünürlüğü iyileştirildi.

## [v164.0] - 2026-02-09
- **Kütüphane Entegrasyonlu Kaydırma**: Gelişmiş Kaydırma ekranında artık Görsel ve Selector kütüphaneleri doğrudan entegre edildi.
- **Dahili Selector Listesi**: Kaydırma ekranında kütüphanedeki tüm selectorler liste halinde sunulur ve hızlıca seçilebilir.

## [v163.0] - 2026-02-09
- **Akıllı Kaydırma (Selector)**: Görsel aramanın yanı sıra, bir element (selector) bulana kadar kaydırma özelliği eklendi.
- **Gelişmiş Kaydırma Menüsü**: Manuel, Görsel ve Seçici sekmeleriyle daha esnek kaydırma seçenekleri sunuldu.

## [v162.0] - 2026-02-09
- **Hızlı Kayıt (Quick Capture)**: Aksiyon eklemeden doğrudan kütüphaneye görsel veya selector kaydetme özelliği eklendi.
- **Z-Order Düzeltmeleri**: Alt pencerelerin (picker, select) katman sıralaması iyileştirildi.

## [v161.0] - 2026-02-09
- **Selector Seçimi Eklendi**: Seçici Kütüphanesi pick modunda açıldığındaık artık her row'da "Seç" butonu çıkıyor.
- **Pop-up Entegrasyonu Tamamlandı**: Artık kütüphaneden selector seçip doğrudan Pop-up Handler'a eklenebiliyor.

## [v160.9] - 2026-02-09
- **Pop-up Düzenleme Ekranı İyileştirmeleri**: Eklenen selector ve görseller için detaylı önizleme ve içerik bilgisi eklendi.
- **Pencere Katman Problemi Çözüldü**: Selector/Görsel seçim pencerelerinin arkada kalma sorunu giderildi.
- **Entegre Kütüphane Kullanımı**: Pop-up hedefleri seçilirken artık doğrudan Görsel ve Selector kütüphaneleri kullanılıyor.

## [v160.8] - 2026-02-09
- **Pop-up Handler Optimizasyonu**: Birden fazla hedef tanımlandığında, ilk eşleşme tıklandıktan sonra döngü sonlandırılır.
- **Selector Fix**: Pop-up içindeki selector'lerin doğru sürücü ile çalışması sağlandı.

## [v160.6] - 2026-02-09up & Engel Yakalayıcı
- **Pop-up Yakala (Auto-Close)**: İstenmeyen reklamlar veya uyarılar (Pop-up) senaryonuzu bölmesin. Bu aksiyon ile birden fazla hedef (Buton veya Görsel) tanımlayabilirsiniz. AutomateX, bu hedeflerden herhangi birekranda belirirse tıklar ve geçer.
- **Kesintisiz Akış**: Tanımlanan pop-up'lar ekranda yoksa, hata vermez ve senaryo normal şekilde devam eder.

### 👻 v160.5 - Hayalet Modu (Auto-Minimize)
- **Otomatik Gizlenme**: Senaryo (veya Debug) başlattığınızda, AutomateX kendini otomatik olarak görev çubuğuna küçültür. Böylece hedef uygulama ile aranıza girmez. İşlem bitince otomatik olarak ekrana geri döner ve raporu sunar.

### 🧠 v160.4 - Akıllı Odaklanma (Auto-Focus)
- **Hedef Odaklanma (Debug Focus)**: Senaryoyu ortadan başlattığınızda (Debug), AutomateX otomatik olarak geçmiş adımları tarar ve işlem yapılacak uygulamayı (veya tarayıcıyı) bulup **öne getirir** ve **tam ekran** yapar. Böylece manuel olarak pencere seçmenize gerek kalmaz.

### 🚀 v160.3 - Debug & Hızlı Başlangıç
- **Adımdan Başlat (Start From Here)**: Artık senaryoları en baştan başlatmak zorunda değilsiniz. Herhangi bir adımın yanındaki "▶" butonuna basarak, senaryoyu o adımdan itibaren çalıştırabilirsiniz. Debug işlemleri için büyük kolaylık sağlar.
- **Güvenli Başlangıç**: Arka planda çalışmayan bileşenlere (Log vb.) yapılan gereksiz çağrılar temizlendi.

### 📦 v160.1 - Selector & Visual Elements Entegrasyonu
- **Görsel Bağlantısı (Selector Sync)**: Artık bir Selectör kaydettiğinizde, kaydedilen ekran görüntüsü otomatik olarak **Visual Elements (Görsel Depo)** kütüphanesine de eklenir. Böylece hem teknik hem görsel olarak yönetilebilir.
- **Akıllı Import/Export**: Senaryolar dışa aktarılırken, içinde kullanılan Selectörler de pakete dahil edilir. İçe aktarıldığında bu selectörler ve görselleri veritabanına otomatik olarak işlenir.
- **Kapsamlı Yedekleme**: "Visual Elements" ve "Selectors Repository" artık senaryo dosyalarıyla birlikte tam senkronize şekilde taşınır.

## 🌟 Mevcut Yetenekler ve Özellikler (Current Capabilities)
Bu otomasyon aracı, modern RPA (Robotik Süreç Otomasyonu) standartlarında geliştirilmiş, hibrit ve güçlü bir altyapıya sahiptir.

### 1. Hibrit Otomasyon Motoru (Hybrid Engine)
*   **Görsel Zeka (Vision Engine)**: İnsan gözü gibi görür. Ekrandaki butonları resim olarak arar.
    *   **Akıllı Eşleşme**: Renk değişimlerini, çözünürlük farklarını ve %80-%120 arası zoom bozulmalarını tolere eder (SIFT/ORB algoritması).
    *   **Keypoint Matching**: Görselin sadece belirli köşeleri (örneğin bir logo) eşleşse bile doğru hedefi bulur.
*   **Yapısal Zeka (Structure Engine)**: UiPath/Selenium mantığıyla çalışır.
    *   **Seçici (Selector) Teknolojisi**: Uygulamanın arka plan kodlarını (AutomationID, XPath, Name) okur. Görsel değişse bile kod değişmediği sürece çalışır.
    *   **Dinamik Filtreleme**: "Tutar" veya "Tarih" gibi değişen metinleri algılar ve seçiciden otomatik olarak çıkarır.

### 2. Akıllı Kayıt ve Editör (Smart Recorder & Editor)
*   **Smart Recorder**: Sizi izler ve yaptığınız tıklamaları, yazdığınız yazıları otomatik olarak senaryoya döker.
*   **Drag & Drop**: Adımların sırasını sürükleyip bırakarak değiştirebilirsiniz.
*   **Işınlanma**: 100. adımdaki bir işlemi tek tuşla 1. sıraya taşıyabilirsiniz.

### 3. Veritabanı ve Taşınabilirlik (Portable DB)
*   **Tek Dosya Mimarisi**: Tüm senaryolar, görseller ve ayarlar tek bir `.db` dosyasında saklanır. Klasör kalabalığı yaratmaz.
*   **Tak-Çalıştır**: Uygulamayı USB belleğe atıp başka bir bilgisayarda (Kurulumsuz) çalıştırabilirsiniz.
*   **Hayalet Sürücü (Ghost Driver)**: Görselleri diske kaydetmeden, doğrudan RAM üzerinden okuyarak çalışır. İz bırakmaz.

### 4. Güvenlik ve Kararlılık
*   **Red Border (Görsel Feedback)**: Robot çalışırken işlem yaptığı alanı kırmızı çerçeve içine alır, böylece nereye tıkladığını veya nerede takıldığını anlık görebilirsiniz.
*   **Popup Killer**: Beklenmedik reklam veya uyarı pencereleri çıkarsa senaryoyu durdurmaz, kapatıp devam eder.
*   **Crash Koruması**: "Kuzen Desteği" ve "Anchor" teknolojileri sayesinde, hedef elementin yeri değişse bile etrafındaki sabit nesnelerden (Anchor) yola çıkarak hedefi bulur.

---

### 🇹🇷 v160.0 - Tam Türkçe Altyapı ve Kod İyileştirmeleri - [Major]
- **%100 Türkçe Kodlama**: Projenin tüm teknik dokümantasyonu (Docstrings) ve kod içi yorum satırları İngilizce'den Türkçe'ye çevrildi. Türk geliştiricilerin projeyi devralması ve geliştirmesi kolaylaştırıldı.
- **Refactoring**: Sürücü (Driver) ve Arayüz (UI) katmanlarında kod temizliği yapıldı.

### ⌨️ v155.0 - Hızlı Yazma (Fast Type)
- **Turbo Mod**: "Yazı Yaz" (Type) aksiyonu artık varsayılan olarak 0.01 sn gecikme ile çalışıyor. Uzun metinleri saniyeler içinde doldurur.

### 🛡️ v130.0 - Akıllı Girdi Filtreleme & Gelişmiş Seçiciler
- **Volatile Attribute Filtering**: Bir "Edit" (Yazı yazma) alanını kaydederken, içindeki yazının (örn: "Ahmet Yılmaz") değişken olduğunu algılar.
- **Kullanıcı Onayı**: "Bu alan metin içeriyor, seçiciye dahil edelim mi?" diye sorar. "Hayır" derseniz, o alana farklı bir isim yazılsa bile robot orayı tanımaya devam eder.

### 🔢 v125.0 - İndeks Düzenleme (Multi-Element Support)
- **Sıra Seçimi**: Ekranda aynı "Kaydet" butonundan 3 tane varsa, seçicinin kaçıncı butona gideceğini (Index) artık arayüzden değiştirebilirsiniz.

### 🔍 v115.0 - Seçici Büyüteci (Selector Zoom)
- **Detaylı İnceleme**: Kaydettiğiniz teknik seçicilerin (Selectors) ekran görüntülerini kütüphanede büyüteç ile detaylı inceleyebilirsiniz.

### 🖼️ v110.0 - Görsel Destekli Seçiciler (Visual Selectors)
- **Görsel Kanıt**: UiPath benzeri bir özellikle, teknik seçici (kod) kaydedilirken o anki ekran görüntüsü de veritabanına "kanıt" olarak eklenir. Böylece hangi kodun hangi butona ait olduğunu görsel olarak teyit edebilirsiniz.

### 🧠 v85.0 - AI Vision (Akıllı Göz) - [Major]
- **Multi-Scale Search (Zoom Toleransı)**: Tarayıcı zoom oranı değişse bile (%80 - %120), görseli yeniden boyutlandırıp arayarak bulur.
- **Keypoint Matching (Özellik Eşleştirme)**: Butonun rengi değişse (Dark/Light mod) veya hafifçe bozulsa bile, şekil özelliklerinden (köşe/kenar) tanır (ORB/SIFT mantığı).
- **Akıllı Fallback**: Önce milisaniyelik hızlı arama yapar, bulamazsa bu derin yapay zeka analizlerini devreye sokar.

### 🧗 v85.2 - Anchor Climb Up (Robust Scope)
- **Kuzen Desteği (Cousin Support)**: Eğer Çapa ve Hedef farklı div'lerin içindeyse (Cousin), robot otomatik olarak 3 seviye yukarı (Dede, Büyük Dede) tırmanarak ikisini de kapsayan ortak atayı bulur.
- **Akıllı Kapsam (Smart Scope)**: Hedefin içinde olmadığı yanlış kapsayıcıları (Parent) eler, doğru kapsayıcıyı (Common Ancestor) akıllıca seçer.

### 🧠 v85.1 - AI Vision & Robust Anchor - [Major]
- **Multi-Scale Search (Zoom Toleransı)**: Tarayıcı zoom oranı değişse bile (%80 - %120), görseli yeniden boyutlandırıp arayarak bulur.
- **Keypoint Matching (Özellik Eşleştirme)**: Butonun rengi değişse veya şekli hafifçe bozulsa bile, özelliklerinden (ORB/SIFT) tanır.
- **Anchor Sibling Fallback**: Çapa'nın "Babasına" (Parent) erişilemediğinde, "Kardeşine" (Sibling) bakarak hedefi bulma yeteneği eklendi. (Yan yana duran Etiket-Kutu yapıları için hayat kurtarıcı).

### ⚓ v81.0 (Anchor Support) - [Yeni]
- **Çapa (Anchor) Desteği**: Dinamik elementleri bulmak için sabit bir referans element (Anchor) kullanabilme.
- **Akıllı Scope**: Anchor bulunduğunda arama alanı otomatik olarak daraltılır.
- **Kullanıcı Dostu Akış**: Hedef seçildikten sonra "Çapa eklemek ister misiniz?" diye soran akıllı diyalog.

7.  **Sıra (Index) Desteği**: Aynı isme sahip birden fazla element varsa (örneğin listedeki 2. eleman), Selectors ekranındaki **Kalem (✏️)** butonuna basarak kaçıncı sıradakine tıklayacağını belirleyebilirsiniz.

### 🚀 v80.0 - Yapısal Zeka & Visual Elements (Major Release):
1.  **Görsel Depo -> Visual Elements**: Modül isimlendirmesi global standartlara uygun hale getirildi.
2.  **Selectors Repository (Seçiciler Deposu)**: Artık sadece görsellere bağımlı değiliz!
    *   **UiPath Tarzı Seçim**: Spy aracı ile ekran üzerindeki butonların kodlarını (XPath, AutomationID) yakalayıp kaydedebilirsiniz.
    *   **Çözünürlük Bağımsızlığı**: Bu seçiciler ekran çözünürlüğü değişse bile çalışmaya devam eder.
3.  **Akıllı Denetçi (Structure Driver)**:
    *   Arka planda çalışan yeni sürücü, pencerelerin ve butonların yapısal özelliklerini okur.
    *   **Click Selector**: Kaydedilen seçicilere doğrudan tıklama özelliği eklendi.
4.  **Veritabanı Genişlemesi**: `selectors` tablosu eklenerek hibrit (Görsel + Kod) otomasyon altyapısı kuruldu.
5.  **Görsel ve Detay (Rich Selectors)**:
    *   **Görsel Kanıt (Screenshot)**: Spy aracı artık seçicinin kaydını alırken o anki görüntüsünü de yakalayıp veritabanına kaydeder (UiPath Style).
    *   **Tam Görünürlük**: Selector içerikleri artık kesilmeden, kaydırılabilir tam metin olarak görüntülenir.
    *   **Görüntü Büyütme (Zoom)**: Selector listesindeki küçük resimlere 🔍 büyüteç ikonu ile tıklayarak büyük boyutta inceleyebilirsiniz.
6.  **Akıllı Selector (Robustness) 🧠**:
    *   **AutomationId Önceliği (ID is King)**: UiPath mantığına uygun olarak, ID varsa isim değişse bile element bulunur.
    *   **Fuzzy Matching**: İsimleri değişen elementleri %80 benzerlik ve içerik analizi ile bulabilme yeteneği eklendi.
    *   **AutomationId Önceliği (ID is King)**: UiPath mantığına uygun olarak, ID varsa isim değişse bile element bulunur.
    *   **Fuzzy Matching**: İsimleri değişen elementleri %80 benzerlik ve içerik analizi ile bulabilme yeteneği eklendi.
    *   **Noise Filtering**: "d-none", "active" gibi geçici CSS sınıflarını görmezden gelerek daha kararlı çalışma sağlar.
    *   **Değişken Filtreleme (Volatile Filtering)**: Giriş alanları (Input, Edit, Text) için metin içeriği algılandığında, bu metni selector'a dahil edip etmeyeceğinizi sorar. Böylece dinamik metinlerden kaynaklı hatalar önlenir.


### 🏷️ v68.2 - İsim Değişikliği (Görsel Depo):
1.  **Daha Anlaşılır İsim**: "Nesne Deposu" ismi, kullanıcılar için daha anlaşılır olması amacıyla **"Görsel Depo"** olarak güncellendi.

### ⚡ v68.1 - Arayüz Temizliği:
1.  **Sadeleşme**: "Işınlanma" özelliği geldiği için gereksiz kalan Yukarı/Aşağı taşıma okları kaldırıldı. Arayüz ferahladı.

### 🚀 v68 - Işınlanma (Hızlı Sıralama):
1.  **Hızlı Taşıma**: Adım numaraları tıklanabilir hale geldi. Örneğin 50. adıma tıklayıp "2" yazıp Enter'a basarsanız, o adım anında 2. sıraya taşınır.

### 🛡️ v67.1 - Snip Fix (Sessiz Hata Çözümü):
1.  **Kritik Düzeltme**: `assets` klasörü silindikten sonra Snip aracının çökmesi (sessizce kapanması) sorunu, geçici kayıt yerinin `data` klasörüne alınmasıyla çözüldü.

### 🚨 v67 - Popup Giderici (Restore):
1.  **Akıllı Kapatıcı**: "Popup Yakala" özelliği modernize edilerek geri getirildi.
2.  **Smart Handling**: Ekranda popup varsa kapatır, yoksa hata vermeden yoluna devam eder.
3.  **Esneklik**: Tek bir görsele bağımlı değildir, tanımladığınız tüm uyarıları yönetebilir.

### 📦 v66.2 - Tam Taşınabilirlik (Portable):
1.  **Klasör Yapısı**: `dist` klasörü standart hale getirildi. Artık Flash belleğe atıp herhangi bir PC'de tak-çalıştır kullanılabilir.
2.  **Veri Kopyalama**: Mevcut `data` klasörü otomatik olarak derleme içine kopyalanarak veri kaybı önlendi.

### 🧹 v66.1 - Veritabanı Optimizasyonu:
1.  **Dosya Temizliği**: Projedeki tüm `assets` klasörleri fiziksel olarak silindi.
2.  **Schema Update**: Veritabanındaki gereksiz `file_path` kolonu kaldırıldı. Sistem %100 binary veriyle çalışıyor.

### 💾 v66 - Veritabanı Odaklı Mimari (Pure DB):
1.  **Gölge Dosyalar**: Ekran görüntüleri diskte tutulmaz, doğrudan veritabanına (BLOB) gömülür.
2.  **Repo Modları**:
    *   **Görüntüleme Modu**: Ana menüden sadece izleme/silme yapılabilir.
    *   **Seçim Modu**: Bir adımı düzenlerken resim seçimi yapılabilir.
3.  **Hayalet Sürücü**: Robot, görselleri diske yazmadan RAM üzerinden okur.

### 🚀 v65.2 - Rebranding (AutomateX):
1.  **Yeni İsim**: Uygulama artık **AutomateX** olarak anılacak!
2.  **Yenilenen Arayüz Başlıkları**: Tüm pencereler ve karşılama ekranı yeni kimliğe uygun güncellendi.

### 🚑 v65.1 - Başlangıç Hatası Giderildi:
1.  **Açılış Hatası**: Uygulama açılırken oluşan "APP_VERSION not defined" hatası giderildi.

### 🧭 v65 - Navigasyon ve Karşılama Ekranı:
1.  **Karşılama Ekranı**: Uygulama artık doğrudan karışık bir editörle açılmıyor. Sizi "Yeni Senaryo" veya "Senaryo Yükle" seçenekleriyle modern bir giriş ekranı karşılıyor.
2.  **Akış Yönetimi**: Editörden çıkıp ana menüye dönmek için "Ana Menü" butonu eklendi (Kaydetme uyarısı ile birlikte).
3.  **Temiz Başlangıç**: Her yeni senaryo veya yükleme işlemi, temiz bir sayfa ve odaklanmış bir arayüz sunuyor.

### 🚑 v64.3 - Kritik Bug Fix:
1.  **Gelişmiş Tıklama Hatası**: F3 veya indeksli tıklama sırasında alınan kod hatası (Argument Error) giderildi. Sürücü katmanı artık yeni parametreleri (index, offset) tam olarak destekliyor.

### 🧹 v64.2 - F3 Akış Düzeltmesi:
1.  **Akıcı F3**: F3 ile alan seçtikten sonra, tıklama noktasını seçerken yanlışlıkla eliniz kayıp sürükleme yapsanız bile, uygulama bunu "yeni alan seçimi" sanmayıp, "tıklama noktası" olarak kabul edecek. İkinci defa alan seçtirme karışıklığı giderildi.

### 🎨 v64.1 - Görsel Kalitesi & Kararlılık:
1.  **Kristal Netliğinde Görüntü**: Snip (Görsel Alma) işlemi sırasında oluşan gri/soluk renk sorunu giderildi. Artık ekran görüntüsü alınmadan önce seçim penceresi tamamen gizleniyor.
2.  **Kararlılık**: Snip aracı sonrası uygulama donması tamamen çözüldü.

### 🛠️ v64 - Vision & UI Rafinasyon:
1.  **F3 Kısıtlaması**: Rölatif tıklama artık sadece seçilen alanın dışına taşmayı engeller (Clamp). 
2.  **Otomatik Kapanma**: F3 seçiminden sonra SnipTool'un açık kalma hatası düzeltildi.
3.  **Görsel Değiştirme**: Her adımın yanına eklenen 🖼️ butonu ile adımdaki resmi kütüphaneden saniyeler içinde değiştirebilirsiniz.
4.  **Pencere Yönetimi**: Kütüphane ve senaryo pencerelerinin birden fazla açılması engellendi (Singleton).
5.  **Modal Fix**: Pencerelerin arka planda kalma sorunu minimize edildi.

### 💎 v63 - Professional Data Overhaul (Veri ve Görüş Devrimi):
1.  **Merkezi Nesne Deposu (BLOB)**: Tüm görseller artık veritabanında binary (BLOB) olarak saklanıyor. Dosya silinse bile otomasyon çalışmaya devam eder.
2.  **JSON Senaryo Mimarisi**: Senaryolar hem adım bazlı hem de bütünsel JSON olarak kaydedilir.
3.  **Çoklu Eşleşme (Multi-Match)**: Aynı butondan birden fazla varsa, kaçıncıya tıklanacağı (Index) seçilebilir.
4.  **Rölatif Tıklama (F3 - Offset)**: Bir görseli referans alıp, onun merkezinden belirli bir uzaklığa (X, Y) tıklama desteği eklendi.
5.  **Dışa/İçe Aktar (Import/Export)**: Senaryolar ve tüm bağlı görsel varlıkları tek bir paket olarak taşınabilir hale getirildi.
6.  **Gelişmiş Nesne Tarayıcı**: Nesne deposunda görsellerin önizlemeleri (Preview) doğrudan veritabanından çekilerek gösterilir.

### 🚀 v62 - Nihai Sadeleştirme:
1.  **Tam Temizlik**: Uygulama arayüzündeki tüm yazılı logolar ve başlıklar ("MASAÜSTÜ OTOMASYON" dahil) tamamen kaldırıldı. Sidebar artık direkt aksiyonlarla başlıyor.

### 📝 v61 - Kayıt Sistemi:
1.  **Marka Kaldırıldı**: "Vakıf Katılım" ibareleri tamamen silindi.
2.  **Kalıcı Geçmiş**: Uygulama klasörüne `HISTORY.md` dosyası eklendi.

### 🚨 v60 - Görsel Geri Bildirim (Red Border):
1.  **Kırmızı Çerçeve**: Senaryo çalışırken ekranın etrafında beliren, otomasyonu engellemeyen şeffaf kırmızı çerçeve eklendi.
2.  **Hayalet Pencere**: Windows API kullanılarak hazırlanan bu çerçeve, tıklamaları arkaya geçirir.

### 👁️ v59 - Akıllı Bekleme (Check State Unified):
1.  **Tam Entegrasyon**: "Görseli Bekle" (Check State) özelliği de artık ana görme motorunu kullanıyor.
2.  **Renk/Şekil Yeteneği**: Artık beklediğiniz görselin rengi değişse bile (Hover/Seçili) robot onu tanıyabiliyor.

### 🧠 v58 - Birleşik Görme Motoru (Unified Logic):
1.  **Tek Beyin**: Click, Scroll ve Wait motorları tek bir merkezde birleşti. Tıklarken bulduğu bir şeyi kaydırırken kaçırması imkansız hale getirildi.

### 🟢 v57.1 - Renk Bağımsız Arama (Shape Match):
1.  **Tam Şekil Eşleşmesi**: Renk tutmasa bile şekil tutuyorsa (hover durumları gibi) robotun doğru yeri bulması sağlandı.

### ⚙️ v57 - Sorun Giderici Güncelleme (Diagnostics):
1.  **Fare Odaklama**: Kaydırma sırasında farenin ortaya çekilmesiyle hover efektleri engellendi.
2.  **Siyah-Beyaz Arama (Grayscale)**: Renkli eşleşme başarısız olursa şekil tabanlı gri tonlamalı arama fall-back olarak eklenmişti.

### 🦅 v56.2 - Şahin Gözü Kaydırma (High-Intensity):
1.  **Dinamik Tarama**: Kaydırma adımlarında kademeli hassasiyet (0.9 -> 0.6) ile derinlemesine arama eklendi.

### ⚡ v56.1 - Akıllı Kaydırma İyileştirmesi:
1.  **Hız Dengesi**: Bekleme süresi 0.8 saniyeye düşürülerek performans optimize edildi.

### ↕️ v55 - Gelişmiş Kaydırma (Advanced Scroll):
1.  **Çift Mod (Manuel/Smart)**: Hedefe kadar kaydır veya birim bazlı kaydır sekmeleri eklendi.

### 📐 v50 - Pencere Yönetimi:
1.  **Otomatik Tam Ekran**: Uygulama açıldığında veya siteye gidildiğinde hedef pencereyi otomatik büyütme (Maximize) eklendi.

### ✏️ v46 - Adım Düzenleme (Editable Steps):
1.  **Kalem İkonu**: Mevcut adımları (URL, süre, hassasiyet) silmeden güncelleme imkanı sağlandı.

### 📦 v40 - Nesne Deposu (Object Repository):
1.  **Görsel Kütüphanesi**: RPA standartlarına uygun nesne deposu yapısına geçildi.

### 🛡️ v35 - Yerel Veri & Güvenlik:
1.  **Taşınabilirlik**: Verilerin `data` klasöründe saklanması ve hassas veri maskeleme (Bankacılık standartları) sağlandı.

---
*Not: Bu dosya uygulama ile birlikte dağıtılan resmi versiyon günlüğüdür.*
