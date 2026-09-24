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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isim TEXT NOT NULL,
                    telefon TEXT NOT NULL,
                    mesaj TEXT,
                    email TEXT NOT NULL,
                    seri TEXT NOT NULL DEFAULT 'karisik',
                    tarih TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    except sqlite3.Error as error:
        current_app.logger.exception(
            LogMessages.DB_INITIALIZATION
        )
        raise DatabaseError(
            ErrorMessages.DB_INITIALIZATION
        ) from error


def lead_ekle(isim, telefon, mesaj, email, seri="karisik"):
    try:
        connection = get_db()

        with connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    isim, telefon, mesaj, email, seri
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (isim, telefon, mesaj, email, seri),
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
    try:
        connection = get_db()

        rows = connection.execute(
            """
            SELECT id, isim, telefon, mesaj, email, seri, tarih
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