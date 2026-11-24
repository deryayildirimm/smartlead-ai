# İlk backend doğrulaması

## Sonuç

- Python **3.12.14**, Django **5.2.18**, PostgreSQL **16.15** ile çalıştırıldı.
- Temiz PostgreSQL veritabanına bütün migration'lar uygulandı; ilk beş tür oluşturuldu.
- `python manage.py check`: sorun yok.
- `python manage.py makemigrations --check --dry-run`: model/migration farkı yok.
- `ruff check .` ve `ruff format --check .`: geçti.
- `pytest -q`: **47 test geçti**. Bu sayı yalnızca yeni `backend/tests/` testlerine aittir.
- Yerel ayar oluşturma betiğinin rastgele anahtar üretmesi, dosyayı yalnızca sahibine açması ve mevcut dosyayı koruması doğrulandı.

## Testlerin kapsadığı davranışlar

- Okuyucuya kullanılabilir yerel parola atanmaması; e-posta normalizasyonu ve veritabanı düzeyinde büyük/küçük harf duyarsız benzersizlik.
- Dış kimliklerin sağlayıcı/site/üye bileşiminde benzersizliği; personel girişi ve yönetim ekranları.
- Oturumsuz isteklerin reddedilmesi, kapalı hesabın oturum erişiminin engellenmesi, kendi profilini görme.
- Bir okuyucunun diğerinin tercihlerini okuyamaması veya üzerine yazamaması.
- Sahiplik, yönetici rolü, doğrulama ve plan durumu gibi istemcinin belirleyemeyeceği alanların reddedilmesi.
- Çoklu tür/gün kaydı, “Benim için seç” modu, geçersiz gün/süre/saat/saat dilimi/tür doğrulaması.
- GET'in kayıt oluşturmaması; aynı ayarların tekrar kaydında sürüm ve kayıt sayısının değişmemesi.
- Hata durumunda tercih, tür ve plan değişikliklerinin birlikte geri alınması.
- Aynı kullanıcı için iki ayrı PostgreSQL bağlantısından eşzamanlı ilk kayıtta tek ve eksiksiz sürüm oluşturulması.
- Ayar kaydının izin üretmemesi ve gönderimi başlatmaması; oturum yazmalarında CSRF kontrolü.
- Veritabanı gün/bileşim/süre kısıtları; sağlık uç noktalarının davranışı.

## Henüz doğrulanamayan entegrasyonlar

Wix oturum köprüsü, Wix okuyucu sayfaları, e-posta sağlayıcısı ve gerçek gönderim bu sürümün parçası değildir.
Docker Compose tarifi hazırlanmıştır; bu çalışma ortamında Docker bulunmadığı için test veritabanı geçici bir PostgreSQL süreciyle çalıştırıldı.
GitHub Actions tarifi hazırdır; depoya gönderildikten sonra GitHub üzerinde ayrıca çalışacaktır.
Üretim dağıtımı yapılmadı; bu belge canlı ürün onayı değildir.
