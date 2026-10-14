
import sqlite3
from pathlib import Path

from flask import current_app, g

from constants import ErrorMessages, LogMessages
from app.exceptions import DatabaseError


def get_db():
    """İstek boyunca kullanılacak veritabanı bağlantısını açar."""

    if "db" not in g:
        database_path = Path(current_app.config["DATABASE_URL"])

        if (
            str(database_path) != ":memory:"
            and not database_path.is_absolute()
        ):
            project_dir = Path(current_app.root_path).parent
            database_path = project_dir / database_path

        try:
            connection = sqlite3.connect(
                str(database_path),
                timeout=10,
            )

            connection.row_factory = sqlite3.Row
            g.db = connection

        except sqlite3.Error as error:
            current_app.logger.exception(
                LogMessages.DB_CONNECTION
            )
            raise DatabaseError(
                ErrorMessages.DB_CONNECTION
            ) from error

    return g.db


def close_db(error=None):
    connection = g.pop("db", None)

    if connection is not None:
        connection.close()


def init_db(app):
    app.teardown_appcontext(close_db)

    try:
        connection = get_db()

        with connection:

            # Yeni veritabanı için tablo oluşturma
            connection.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isim TEXT NOT NULL,
                    telefon TEXT NOT NULL DEFAULT '',
                    mesaj TEXT,
                    email TEXT NOT NULL,
                    seri TEXT NOT NULL DEFAULT 'karisik',
                    tarih TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    aktif INTEGER NOT NULL DEFAULT 0,
                    email_consent INTEGER NOT NULL DEFAULT 0,
                    consent_at TEXT
                )
            """)

            # Mevcut veritabanındaki sütunları bul
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(leads)"
                ).fetchall()
            }

            # Eksik sütunları eski kayıtları silmeden ekle
            if "aktif" not in columns:
                connection.execute(
                    "ALTER TABLE leads ADD COLUMN "
                    "aktif INTEGER NOT NULL DEFAULT 0"
                )

            if "email_consent" not in columns:
                connection.execute(
                    "ALTER TABLE leads ADD COLUMN "
                    "email_consent INTEGER NOT NULL DEFAULT 0"
                )

            if "consent_at" not in columns:
                connection.execute(
                    "ALTER TABLE leads ADD COLUMN consent_at TEXT"
                )

    except sqlite3.Error as error:
        current_app.logger.exception(
            LogMessages.DB_INITIALIZATION
        )
        raise DatabaseError(
            ErrorMessages.DB_INITIALIZATION
        ) from error


def lead_ekle(
    isim,
    telefon,
    mesaj,
    email,
    seri="karisik",
    email_consent=False
):
    """Yeni kullanıcı kaydı oluşturur."""

    try:
        connection = get_db()

        consent_value = 1 if email_consent is True else 0

        with connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    isim,
                    telefon,
                    mesaj,
                    email,
                    seri,
                    aktif,
                    email_consent,
                    consent_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    CASE WHEN ? = 1
                    THEN CURRENT_TIMESTAMP
                    ELSE NULL END
                )
                """,
                (
                    isim,
                    telefon,
                    mesaj,
                    email,
                    seri,
                    consent_value,
                    consent_value,
                    consent_value
                )
            )

        return cursor.lastrowid

    except sqlite3.Error as error:
        current_app.logger.exception(
            LogMessages.DB_INSERT
        )
        raise DatabaseError(
            ErrorMessages.DB_INSERT
        ) from error


def tum_leadler():
    """Yönetim paneli için kullanıcıları listeler."""

    try:
        connection = get_db()

        rows = connection.execute(
            """
            SELECT
                id,
                isim,
                email,
                seri,
                aktif
            FROM leads
            ORDER BY tarih DESC, id DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    except sqlite3.Error as error:
        current_app.logger.exception(
            LogMessages.DB_LIST
        )
        raise DatabaseError(
            ErrorMessages.DB_LIST
        ) from error
