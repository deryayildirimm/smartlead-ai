class AIConstants:
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    MAX_COMPLETION_TOKENS = 1500
    TEMPERATURE = 0.5
    REASONING_EFFORT = "low"

    CONNECT_TIMEOUT = 5
    READ_TIMEOUT = 30

    DEMO_REPLY = (
        "Demo modu: Yapay zekâ bağlantısı henüz etkin değil. "
        "Platform, ilgi alanına uygun kısa okumalar keşfetmene "
        "yardımcı olmayı amaçlıyor. Örnek serileri inceleyebilirsin."
    )


class ValidationRules:
    MAX_MESSAGE_LENGTH = 2000
    MAX_HISTORY_COUNT = 20
    MAX_HISTORY_MESSAGE_LENGTH = 4000

    FIELD_LIMITS = {
        "isim": 100,
        "telefon": 30,
        "email": 254,
        "mesaj": 2000,
        "seri": 50,
    }

    DEFAULT_SERIES = "karisik"

    ALLOWED_SERIES = frozenset({
        "karisik",
        "sehrin_icinde",
        "ince_bir_mizah",
        "yeni_baslangiclar",
    })


class ErrorMessages:
    INVALID_JSON_OBJECT = (
        "Geçerli bir JSON nesnesi gönderilmelidir."
    )

    EMPTY_MESSAGE = "Mesaj boş olamaz."
    MESSAGE_TOO_LONG = "Mesaj en fazla {limit} karakter olabilir."

    HISTORY_MUST_BE_LIST = "Sohbet geçmişi liste olmalıdır."
    HISTORY_TOO_LONG = "En fazla son {limit} mesaj gönderilebilir."
    INVALID_HISTORY_ITEM = "Geçmiş mesaj biçimi geçersiz."
    INVALID_HISTORY_ROLE = "Geçmiş mesaj rolü geçersiz."
    INVALID_HISTORY_CONTENT = "Geçmiş mesaj içeriği geçersiz."

    FIELD_MUST_BE_TEXT = "{field} alanı metin olmalıdır."
    FIELD_TOO_LONG = "{field} alanı en fazla {limit} karakter olabilir."
    FIELD_REQUIRED = "{field} alanı zorunludur."

    INVALID_EMAIL = "E-posta biçimi geçersiz."
    INVALID_PHONE = "Telefon biçimi geçersiz."
    INVALID_PHONE_LENGTH = (
        "Telefon 7 ile 15 arasında rakam içermelidir."
    )
    INVALID_SERIES = "Geçerli bir seri seçilmelidir."

    DB_CONNECTION = "Veritabanına erişilemiyor."
    DB_INITIALIZATION = "Veritabanı hazırlanamadı."
    DB_INSERT = "Kaydınız şu anda oluşturulamıyor."
    DB_LIST = "Kayıtlar şu anda getirilemiyor."

    AI_PROVIDER = "Yapay zekâ sağlayıcısı desteklenmiyor."
    AI_TIMEOUT = "Yanıt almak uzun sürdü. Lütfen tekrar deneyin."
    AI_UNAVAILABLE = (
        "Asistana şu anda ulaşılamıyor. Lütfen sonra tekrar deneyin."
    )
    AI_INVALID_RESPONSE = "Asistandan geçerli bir yanıt alınamadı."

    UNEXPECTED = (
        "Beklenmeyen bir hata oluştu. Lütfen daha sonra deneyin."
    )
    REQUEST_FAILED = "İstek tamamlanamadı."

    HTTP_ERRORS = {
        400: "İstek biçimi geçersiz.",
        404: "İstenen API adresi bulunamadı.",
        405: "Bu adres için HTTP metodu desteklenmiyor.",
        413: "Gönderilen veri çok büyük.",
        415: "İstek JSON biçiminde gönderilmelidir.",
    }


class LogMessages:
    DB_CONNECTION = "Veritabanı bağlantısı açılamadı."
    DB_INITIALIZATION = "Kayıt tablosu oluşturulamadı."
    DB_INSERT = "Yeni kayıt eklenemedi."
    DB_LIST = "Kayıtlar listelenemedi."

    AI_TIMEOUT = "Groq isteği zaman aşımına uğradı."
    AI_REQUEST_FAILED = "Groq isteği başarısız. HTTP durumu: %s"
    AI_INVALID_RESPONSE = "Groq yanıtının biçimi geçersiz."

    UNEXPECTED = "Beklenmeyen uygulama hatası."


class ResponseMessages:
    LEAD_CREATED = "İlgi talebiniz alındı."


class ConfigMessages:
    INVALID_ENVIRONMENT = (
        "APP_ENV değeri development veya production olmalıdır."
    )
    MISSING_SECRET_KEY = (
        ".env dosyasında SECRET_KEY tanımlanmalıdır."
    )
    PROMPT_FILE_ERROR = (
        "Chatbot talimat dosyası okunamadı: {path}"
    )
    EMPTY_PROMPT = "Chatbot talimatı boş olamaz."