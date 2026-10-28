# PassagePort — Django backend

Python 3.12, Django 5.2 LTS, Django REST Framework ve PostgreSQL 16 ile ilk ürün temeli.
Kök dizindeki Flask uygulaması önceki sunum demosudur; yeni geliştirme bu klasördedir.

## Bu aşamada çalışanlar

- E-posta ile tanımlanan UUID kullanıcıları ve ayrı personel girişi.
- Wix hesabını ileride eşleştirecek dış kimlik tablosu. Parolasız oluşturulan okuyucuya Django parolası atanmaz.
- İlk beş tür: bilim kurgu, felsefe, fantastik, mizah ve polisiye.
- Birden fazla tür veya “Benim için seç”, 1–60 dakika okuma süresi, haftanın günleri, yerel saat ve IANA saat dilimi.
- Kimliği doğrulanmış kullanıcının yalnızca kendi tercihlerini okuması/değiştirmesi.
- Tek transaction içinde kayıt, tekrar kayıtta aynı sonuç, değişiklikte plan sürümünün artması.
- Ayrı hesap durumu, e-posta doğrulaması, izin geçmişi ve gönderim planı.
- Yönetim panelinde kullanıcı/tür yönetimi; tercih/plan/izin/dış kimlik kayıtlarının salt okunur incelenmesi.

**Wix oturum bağlantısı, okuyucu ekranları, gerçek pasaj havuzu ve e-posta gönderimi henüz eklenmedi.**
Şimdilik API, Django personel oturumuyla yerelde denenebilir. İnternetten erişilebilen sahte üyelik veya kullanıcı kimliği bildirme uç noktası yoktur.
Yeni planlar `DRAFT` olarak kalır; ayar kaydetmek gönderim izni oluşturmaz. İzin tablosu hazırdır, izin toplama akışı sonraki aşamadadır.

## Yerel kurulum

Depo kökünden başlayın. Python 3.12 ve PostgreSQL 16 gerekir. Docker, yalnızca yerel veritabanını kolay başlatmak için bir seçenektir.

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/init_local_env.py
```

Son komut rastgele anahtar/parola içeren `.env` dosyasını oluşturur, mevcut dosyayı değiştirmez.
`.env` Git'e eklenmez. Anahtarların örnek dosyalarda veya Wix tarayıcı kodunda tutulmaması gerekir.

**Docker ile PostgreSQL:**

```bash
docker compose up -d db
docker compose ps
```

Veritabanının durumu `healthy` olduğunda devam edin. Bağlantı yalnızca bilgisayarınızın `127.0.0.1:5433` adresine açılır.
Veriler Docker volume içinde korunur. `docker compose down` verileri korur; `down -v` veritabanını siler.

**Docker kullanmadan:** PostgreSQL 16 üzerinde `passageport` veritabanı ve parola kullanan bir veritabanı rolü oluşturun.
`.env` içindeki `DATABASE_URL` değerini bu bağlantıya göre düzenleyin. Test çalıştıracak geliştirme rolünün `CREATEDB` yetkisi gerekir;
canlı uygulamanın rolüne bu yetki verilmez. SQLite bağlantıları ayarlarda reddedilir.

Ardından:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Yönetim: <http://127.0.0.1:8000/admin/>
- Türler: <http://127.0.0.1:8000/api/v1/genres/>
- Yerel API oturumu: <http://127.0.0.1:8000/api-auth/login/>
- Profil: <http://127.0.0.1:8000/api/v1/me/>
- Okuma ayarları: <http://127.0.0.1:8000/api/v1/me/reading-settings/>

Oluşturduğunuz personel hesabıyla yerel API oturumunu açtıktan sonra okuma ayarları sayfasının
**Raw data** alanında `application/json` seçip aşağıdaki gövdeyi `PUT` ile gönderin.
Sayfayı yenileyerek kaydı kontrol edin. Bu, personelin kendi ayarlarını deneyebildiği geliştirme ekranıdır;
okuyucunun son arayüzü Wix'te hazırlanacaktır. Çıkış yaptıktan sonra özel API'ler `403` döner.

```json
{
  "selection_mode": "SELECTED",
  "target_minutes": 5,
  "genre_codes": ["fantasy", "philosophy"],
  "weekdays": [0, 2, 4],
  "local_time": "09:30",
  "timezone": "Europe/Istanbul"
}
```

`weekdays`: 0=Pazartesi, 6=Pazar. Her seçili günde aynı saat kullanılır; saniye seçilmez.
`RANDOM` modunda `genre_codes` boş liste olmalıdır. `PUT` bütün ayarları birlikte günceller;
`PATCH` henüz desteklenmez. Bilinmeyen alanlar reddedilir, sahiplik oturumdan belirlenir.
Saat dilimi yerel saatin anlamını korur; gerçek gönderim zamanları ileride UTC hesaplanacaktır.

## API

| Metot | Yol | Erişim ve işlev |
| --- | --- | --- |
| GET | `/health/` | Açık; uygulama canlılığı, veritabanı kullanmaz |
| GET | `/health/ready/` | Açık; veritabanı bağlantısı, hata ayrıntısı döndürmez |
| GET | `/api/v1/genres/` | Açık; yalnızca seçime açık türler |
| GET | `/api/v1/me/` | Oturum; kendi profil bilgileri |
| GET, PUT | `/api/v1/me/reading-settings/` | Oturum; kendi tercih ve plan ayarları |

Henüz ayar kaydetmemiş kullanıcı için `configured=false` ve varsayılanlar döner; GET kayıt oluşturmaz.
İlk başarılı kayıtta `version=1`, `schedule_status=DRAFT` olur. Değişiklikte sürüm artar;
aynı içeriğin tekrar gönderilmesi sürümü değiştirmez. Tür ve gün listeleri sıralanmış döner.
Oturumla yapılan yazma istekleri CSRF koruması ister. Wix bağlantısı hazır olana kadar CORS açılmaz.

## Kontroller

Aynı PostgreSQL servisi açıkken, `backend/` içinden:

```bash
ruff check .
ruff format --check .
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q
```

Testler PostgreSQL üzerinde ayrı `test_<veritabanı_adı>` veritabanı oluşturur ve sonunda kaldırır.
Canlı veritabanı bağlantısıyla test çalıştırmayın. Kök dizindeki eski Flask testleri ayrı demoya aittir.
GitHub Actions iş akışı PostgreSQL 16 ile bu kontrolleri çalıştıracak şekilde hazırlanmıştır.

`requirements.txt` ve `requirements-dev.txt` kesin sürümleri içerir. Bağımlılık güncellemesinde `.in` dosyaları
düzenlenip kilit dosyaları yeniden üretilir ve kontroller çalıştırılır:

```bash
uv pip compile requirements.in -o requirements.txt
uv pip compile requirements-dev.in -o requirements-dev.txt
```

## Canlıya çıkmadan önceki geliştirme sırası

1. **Wix kimlik köprüsü:** Velo backend oturumdaki üyeyi kendisi belirler. Django imzayı, süreyi, hedef siteyi
   ve tekrar kullanım koşullarını doğrular. Kimlik `provider + site_id + subject` ile eşleşir;
   e-posta benzerliğiyle hesap birleştirilmez. Mevcut personel hesabı okuyucuya otomatik bağlanmaz.
2. **Wix okuyucu paneli:** tür/süre/gün/saat formu, kaydetmeden önce özet, kayıtlı tercihleri gösterme.
3. **Pasaj yönetimi:** kitap, baskı/çeviri, kaynak ve kullanım hakkı; gerçek kitap pasajları.
4. **İzin ve gönderim:** sürümlü izin metni, e-posta doğrulaması, aç/duraklat/durdur, görev kuyruğu,
   tekrar gönderim koruması ve sağlayıcı geri bildirimleri.
5. **Pilot:** az sayıda gönüllü okuyucuyla kullanımı ölçme; ardından quiz/rozet gibi oyunlaştırma.

Eski `leads` kayıtları doğrulanmış üyelik veya yeni gönderim izni olarak otomatik aktarılmaz.
İzin geçmişi yönetim arayüzünde değiştirilemez; veritabanı düzeyinde değişmez kayıt/retansiyon politikası sonraki aşamada ele alınır.

## Üretim ayarları

Bu iskelet henüz yayına alınmış ürün değildir. Dağıtımda `DJANGO_SETTINGS_MODULE=passageport.settings.production`,
gerçek `DJANGO_SECRET_KEY`, `DATABASE_URL`, `DJANGO_ALLOWED_HOSTS` ve gerekliyse
`DJANGO_CSRF_TRUSTED_ORIGINS` tanımlanmalıdır. Başlatma örneği:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn passageport.wsgi:application
```

HTTPS ve statik dosya servisi reverse proxy/hosting katmanında hazırlanır. `DJANGO_TRUST_PROXY=true`
yalnızca istemciden gelen `X-Forwarded-Proto` başlığını temizleyen güvenilir proxy arkasında açılır.
Üretim ayarları güvenli çerezleri ve HTTPS yönlendirmesini zorunlu kılar; geliştirme API giriş sayfası kapalıdır.
Yedekleme, izleme, giriş denemesi sınırlama ve personel MFA kurulumu yayına hazırlık adımlarıdır.

```bash
DJANGO_SETTINGS_MODULE=passageport.settings.production python manage.py check --deploy
```

İş akışı ve sonraki içerik tabloları: [tasarım belgesi](../docs/passageport-user-flow-and-data-model.md).
