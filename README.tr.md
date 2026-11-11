# desktop-lifecycle

[![test](https://github.com/1emrecoskun/desktop-lifecycle/actions/workflows/test.yml/badge.svg)](https://github.com/1emrecoskun/desktop-lifecycle/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/desktop-lifecycle.svg)](https://pypi.org/project/desktop-lifecycle/)

**Küçük bir Python masaüstü uygulamasının sıkıcı kısımları — arayüz yazmaya
başlamadan önce.**

Tek örnek kilidi, XDG dizinleri, otomatik açılış, menü girişi, oturum tespiti,
tepsi yeteneği ve dönen log. Framework yok, bağımlılık yok, root yok.

```bash
pip install desktop-lifecycle
```

```python
from desktop_lifecycle import App

app = App("aracim").ensure_dirs()
app.setup_logging()

if not app.acquire():        # ikinci kopya başlatıldı
    raise SystemExit(0)      # çalışan kopyaya "pencereni göster" dendi
```

Fikir bu kadar: her küçük masaüstü uygulamasının yanlış yaptığı dört şey,
on dakikada okunabilecek küçük bir kütüphanede.

---

## Neden var

Tepside yaşayan her Python aracı aynı altı şeyi yeniden yazıyor — çoğu zaman
farklı ve çoğu zaman hatalı:

| İhtiyaç | Bunun yerine genelde olan |
|---|---|
| Oturum başına tek süreç | çökme sonrası yalan söyleyen PID dosyası (PID'ler yeniden kullanılır) |
| Yazacak yer | ayarlar `~/.config`, log'lar kaynak klasörü, durum dosyası kökte `/.local/state` |
| Açılışta başlat | elle yazılmış üç platforma özel dosya |
| Menü girişi | kaçışı yapılmamış, sessizce açılmayan `Exec=` satırı |
| Oturumu bilmek | `DISPLAY` var, o zaman X11 — XWayland altında değil |
| Tepsi simgesi | `pystray` X11'de çalışır, Wayland'de çalışmaz, PyGObject derlemesi ister |

Bunlar ilginç problemler değil, ama her biri bir akşam kaybettiren hata
bildirimine dönüşüyor. `desktop-lifecycle` hâlihazırda ayıklanmış sürüm.

## İçinde ne var

| Modül | Ne yapar |
|---|---|
| `App` | aşağıdakileri tek nesnede birleştirir |
| `Paths` | `~/.config`, `~/.local/state`, `~/.local/share`, `~/.cache` (Windows/macOS karşılıklarıyla), `0700` izinle oluşturur |
| `SingleInstance` | `flock` / `msvcrt` kilidi + ikinci açılışın mevcut pencereyi öne getirmesi için sinyal dosyası |
| `Autostart` | XDG autostart, kullanıcıya özel Windows `Run` kaydı, macOS LaunchAgent — hepsi geri alınabilir |
| `install_menu_entry` | standarda uygun, `Exec=` kaçışları doğru, atomik yazılan `.desktop` dosyası |
| `session_type` | `x11`, `wayland`, `windows`, `macos`, `unknown` — `DISPLAY`'e değil `XDG_SESSION_TYPE`'a bakar |
| `tray.backend` | hangi tepsi arka ucunun görüneceğini söyler: `ayatana`, `appindicator`, `pystray`, `none` |
| `setup_logging` | durum dizininde dönen log — kullanıcı bulmak zorunda kalmaz |

Daha fazlası, dağıtım başına paket adları dahil:
[docs/tray-on-wayland.md](docs/tray-on-wayland.md).

## Tam bir tepsi uygulaması

[`examples/tk_demo.py`](examples/tk_demo.py) — yaklaşık altmış satır ve ikinci
açılışı, tepsiyi, tepsiye gizlenmeyi ve log dosyasını zaten yönetiyor.
İki kez çalıştırıp devir teslimi görebilirsiniz.

## Bu ne değildir

- **Arayüz kütüphanesi değil.** Hiçbir şey çizmez. Tkinter, PyQt, GTK ve
  wxPython ile birlikte çalışır.
- **Tepsinin yerine geçmez.** Doğru arka ucu tespit eder ve küçük bir menü
  kurar; ama tepsi olmayan bir masaüstünde tepsi varmış gibi yapmaz.
- **Daemon framework'ü değil.** Kilit ve log'un nerede olduğunu söyler;
  süreç döngünüz nasıl kurulursa kurulsun.

## Platform desteği

| | Linux X11 | Linux Wayland | Windows | macOS |
|---|---|---|---|---|
| Yollar | ✅ | ✅ | ✅ | ✅ |
| Tek örnek | ✅ | ✅ | ✅ | ✅ |
| Otomatik açılış | ✅ XDG | ✅ XDG | ✅ `HKCU\...\Run` | ✅ LaunchAgent |
| Menü girişi | ✅ | ✅ | — | — |
| Oturum tespiti | ✅ | ✅ | ✅ | ✅ |
| Tepsi | ✅ AppIndicator | ✅ AppIndicator | ✅ pystray | ✅ pystray |

Wayland'de tepsi simgesi yalnızca AppIndicator / StatusNotifierItem protokolüyle
var olur. Masaüstünde ikisi de yoksa cevap `none` olur ve uygulamanız görünür
bir pencereyle çalışmaya devam etmelidir — bu kütüphane tam olarak bu durumu
düşünmeye zorlar.

## Güvenlik notları

- Her şey **kullanıcı kapsamında**. Root istemez, ev dizini dışına yazmaz,
  sistem ayarlarına dokunmaz.
- Kilit dosyaları `0600`, yapılandırma dizinleri `0700`, masaüstü girişleri
  `0644` izinle oluşturulur.
- Her dosya **atomik** yazılır (geçici dosya + `rename`), böylece çökme
  yarım kalmış bir otomatik açılış kaydı bırakamaz.
- `Exec=` değerleri standardın istediği gibi kaçırılır — `"`, `` ` ``, `$`, `\`
  ve `%` tırnaklı argümandan kaçamaz, alan koduna dönüşemez.
- Hiçbir yerde `shell=True` yok, `eval` yok, kullanıcı girdisinden dinamik
  import yok.
- Uygulama adları doğrulanır; bir ad kendi dizininden çıkamaz.
- Çalışma anında ağ erişimi yok, telemetri yok, hesap yok.

Sorun mu buldunuz? [SECURITY.md](SECURITY.md).

## Makineyi kontrol etmek

```bash
python -m desktop_lifecycle          # okunabilir
python -m desktop_lifecycle --json   # hata bildirimi için
```

Hiçbir şey yazmadan çözümlenen dizinleri, oturum tipini ve tepsi arka ucunu
yazdırır. Kullanıcılar issue'ya `ls -la ~` yerine bunu yapıştırabilir.

## Alternatiflerle karşılaştırma

| | desktop-lifecycle | pystray | elle yazılmış kod |
|---|---|---|---|
| XDG yolları | ✅ | — | genelde hatalı |
| Tek örnek kilidi | ✅ | — | PID dosyası |
| Otomatik açılış | ✅ | — | proje başına |
| Menü girişi | ✅ | — | proje başına |
| Wayland farkındalı tepsi tespiti | ✅ | kısmi | nadir |
| Arayüz kütüphanesi şart mı | hayır | hayır | hayır |
| Bağımlılık | yok | Pillow, PyGObject | — |

`pystray` kendi işinde iyi; bu kütüphane onun etrafındaki soruları yanıtlar,
"denemeli miyim" dahil.

## Gereksinimler

Python 3.9+. Üçüncü parti paket yok.

İsteğe bağlı tepsi yedeği: `pip install desktop-lifecycle[tray]`
(pystray + Pillow). Debian/Ubuntu/Mint'te yerel yol:
`gir1.2-ayatanaappindicator3-0.1`.

## Geliştirme

```bash
git clone https://github.com/1emrecoskun/desktop-lifecycle
cd desktop-lifecycle
python -m unittest discover -s tests -v
```

79 test; donanım ve ekran gerekmez.

## Lisans, isim ve veri

MIT lisansı kodu kapsar; garanti ve sorumluluk vermez. Halka açık küçük bir
kütüphane için dürüst tutum budur. Marka hakkı vermez; proje adı ve simgesi
projede kalır.

Kütüphane hiçbir veri toplamaz: telemetri yok, hesap yok, ağ isteği yok,
analitik yok. Kütüphaneyi *kullanan* uygulama kendi veri işlemesini yine de
açıklamak zorundadır, çünkü pencere ondadır.

MIT — bkz. [LICENSE](LICENSE).

English: [README.md](README.md)
