# Sorun giderme

## Tepsi simgesi hiç görünmüyor

Gereken şey yalnızca AppIndicator kütüphanesi değil, bir **tepsi sunucusu**.
Oturum veriyoluna bak:

```bash
gdbus call --session --dest org.freedesktop.DBus \
  --object-path /org/freedesktop/DBus \
  --method org.freedesktop.DBus.NameHasOwner org.kde.StatusNotifierWatcher
```

`false` yazıyorsa bu masaüstünde hiçbir uygulama tepsi simgesi gösteremez.
GNOME'da *AppIndicator and KStatusNotifierItem Support* eklentisini kurup
açman gerekir; KDE ve çoğu panelde bu yerleşiktir. Böyle bir durumda
`desktop_lifecycle.tray.backend()` bilinçli olarak `none` döner.

Komut `true` diyor ama simge yine yoksa uygulama `pystray` yedeğine düşmüş
olabilir. `python -m desktop_lifecycle --json` çıktısındaki `tray_backend`
alanına bak.

## İkinci kez açınca hiçbir şey olmuyor

Çalışan kopyanın sinyali kendisi kontrol etmek zorunda. `App` ile bu, olay
döngüsünde tek satırdır:

```python
if app.poll_show_request():
    window.deiconify()
```

`SingleInstance` tek başına hiçbir şeyi kontrol etmez; sadece sinyal dosyasını
yazar ve siler.

## Otomatik açılış kaydı çalışmıyor

* Dosya var mı: Linux'ta `~/.config/autostart/<uygulama>.desktop`.
* `Exec=` satırını kopyalayıp elle çalıştır; en sık sebep yanlış yorumlayıcı
  yoludur.
* Bazı masaüstleri autostart kayıtlarını yalnızca oturum açılışında okur;
  çıkış yapıp yeniden giriş yap.

## Kilit dosyası eski görünüyor

Bu bir PID dosyası değil, `flock` kilididir. Süreç öldüğünde çekirdek kilidi
bırakır; dosya kalır ama kilit kalmaz. Dosyayı silmeye çalışma; ikinci açılış
kilidi hemen alabilmelidir.

## Loglar nerede?

Linux'ta `~/.local/state/<uygulama>/logs/`, Windows'ta
`%LOCALAPPDATA%\<uygulama>\logs\`, macOS'ta
`~/Library/Application Support/<uygulama>/logs/`.
`python -m desktop_lifecycle --json` tam yolları yazar.

## Bir yol yanlış çıkıyor

`XDG_*` değerleri yalnızca **mutlak** yollarda dikkate alınır, standardın
istediği gibi. `XDG_STATE_HOME=./state` gibi göreli bir değer bilinçli olarak
yok sayılır.
