class ValidationError(Exception):
    """Kullanıcıdan gelen veri geçersiz."""


class DatabaseError(Exception):
    """Veritabanı işlemi tamamlanamadı."""


class AIServiceError(Exception):
    """Yapay zekâ servisi işlemi tamamlanamadı."""