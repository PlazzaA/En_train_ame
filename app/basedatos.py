import sqlite3
import hashlib
from pathlib import Path
import logging
from typing import Optional, Tuple, List, Dict
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path("usuarios.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        with get_db_connection() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS usuarios
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         nombre TEXT NOT NULL,
                         apellidos TEXT NOT NULL,
                         altura INTEGER NOT NULL,
                         peso REAL NOT NULL,
                         email TEXT UNIQUE NOT NULL,
                         password TEXT NOT NULL)"""
            )

            conn.execute(
                """CREATE TABLE IF NOT EXISTS ejercicios
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         usuario_id INTEGER NOT NULL,
                         nombre_ejercicio TEXT NOT NULL,
                         FOREIGN KEY (usuario_id) REFERENCES usuarios(id))"""
            )

            logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error inicializando DB: {str(e)}")
        raise


def register_user(
    nombre: str, apellidos: str, altura: int, peso: float, email: str, password: str
) -> bool:
    try:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,))
            if cursor.fetchone():
                return False

            cursor.execute(
                """INSERT INTO usuarios (nombre, apellidos, altura, peso, email, password) VALUES (?, ?, ?, ?, ?, ?)""",
                (nombre, apellidos, altura, peso, email, hashed_pw),
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error en register_user: {str(e)}")
        return False


def verify_user(email: str, password: str) -> Tuple[Optional[int], bool]:
    try:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM usuarios WHERE email = ? AND password = ?",
                (email, hashed_pw),
            )
            user = cursor.fetchone()
            if user:
                return user["id"], True
            else:
                return None, False
    except sqlite3.Error as e:
        logger.error(f"Error en verify_user: {str(e)}")
        return None, False


def create_ejercicio_table(usuario_id: int, nombre_ejercicio: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ejercicios (usuario_id, nombre_ejercicio) VALUES (?, ?)",
                (usuario_id, nombre_ejercicio),
            )
            conn.commit()

            table_name = f"ejercicio_{usuario_id}_{nombre_ejercicio.replace(' ', '_')}"
            cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS "{table_name}"
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         series INTEGER NOT NULL,
                         repeticiones INTEGER NOT NULL,
                         peso_maximo REAL NOT NULL,
                         fecha TEXT NOT NULL)"""  
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error en create_ejercicio_table: {str(e)}")
        return False


def get_ejercicios_for_user(usuario_id: int) -> List[Dict]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nombre_ejercicio FROM ejercicios WHERE usuario_id = ?",
                (usuario_id,),
            )
            rows = cursor.fetchall()
            return [{"nombre_ejercicio": row["nombre_ejercicio"]} for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error en get_ejercicios_for_user: {str(e)}")
        return []


def add_ejercicio_data(
    usuario_id: int,
    nombre_ejercicio: str,
    series: int,
    repeticiones: int,
    peso_maximo: float,
    fecha: str,
) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            table_name = f"ejercicio_{usuario_id}_{nombre_ejercicio.replace(' ', '_')}"
            cursor.execute(
                f"""INSERT INTO "{table_name}" (series, repeticiones, peso_maximo, fecha)
                         VALUES (?, ?, ?, ?)""",
                (series, repeticiones, peso_maximo, fecha),
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error en add_ejercicio_data: {str(e)}")
        return False


def get_ejercicio_data(usuario_id: int, nombre_ejercicio: str) -> List[Dict]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            table_name = f"ejercicio_{usuario_id}_{nombre_ejercicio.replace(' ', '_')}"
            cursor.execute(f'SELECT * FROM "{table_name}" ORDER BY fecha DESC')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error en get_ejercicio_data: {str(e)}")
        return []


def delete_ejercicio(usuario_id: int, nombre_ejercicio: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM ejercicios WHERE usuario_id = ? AND nombre_ejercicio = ?",
                (usuario_id, nombre_ejercicio),
            )

            table_name = f"ejercicio_{usuario_id}_{nombre_ejercicio.replace(' ', '_')}"
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')

            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error en delete_ejercicio: {str(e)}")
        return False


init_db()