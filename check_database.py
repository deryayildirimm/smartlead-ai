from flask import Flask

from config import DevelopmentConfig
from app.database import init_db, lead_ekle, tum_leadler


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

# Her çalıştırmada sıfırdan oluşturulan geçici test veritabanı.
app.config["DATABASE_URL"] = ":memory:"


with app.app_context():
    init_db(app)

    kayit_id = lead_ekle(
        isim="Demo Kullanıcı",
        telefon="0000000000",
        mesaj="Kısa ve mizahi okumalar istiyorum.",
        email="demo@example.com",
        seri="ince_bir_mizah",
    )

    kayitlar = tum_leadler()

    assert len(kayitlar) == 1
    assert kayitlar[0]["id"] == kayit_id
    assert kayitlar[0]["email"] == "demo@example.com"

    print("Test başarılı: kayıt eklendi ve listelendi.")
    print(kayitlar[0])