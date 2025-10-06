# database/connection.py

"""
Database connectie en initialisatie voor Planning Tool
UPDATED: Met UUID en timestamp ondersteuning
"""

import sqlite3
import os
from pathlib import Path
import bcrypt
from datetime import datetime, timedelta
import uuid


def get_connection():
    """Maak verbinding met database"""
    db_path = Path("data/planning.db")
    db_path.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_database():
    """Initialiseer database met alle tabellen en seed data"""
    conn = get_connection()
    cursor = conn.cursor()

    # Check of database al bestaat
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='gebruikers'
    """)

    if cursor.fetchone():
        conn.close()
        return

    # Maak tabellen aan
    create_tables(cursor)

    # Seed initiële data
    seed_data(conn, cursor)

    conn.commit()
    conn.close()

    print("Database geïnitialiseerd met seed data")


def create_tables(cursor):
    """Maak alle database tabellen aan"""

    # Gebruikers tabel (UPDATED)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gebruikers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_uuid TEXT UNIQUE NOT NULL,
            gebruikersnaam TEXT UNIQUE NOT NULL,
            wachtwoord_hash BLOB NOT NULL,
            volledige_naam TEXT NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('planner', 'teamlid')),
            is_reserve BOOLEAN DEFAULT 0,
            startweek_typedienst INTEGER CHECK(startweek_typedienst BETWEEN 1 AND 6),
            is_actief BOOLEAN DEFAULT 1,
            aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            gedeactiveerd_op TIMESTAMP,
            laatste_login TIMESTAMP
        )
    """)

    cursor.execute("CREATE UNIQUE INDEX idx_gebruikersnaam ON gebruikers(gebruikersnaam)")
    cursor.execute("CREATE UNIQUE INDEX idx_gebruiker_uuid ON gebruikers(gebruiker_uuid)")

    # Posten tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT UNIQUE NOT NULL,
            beschrijving TEXT
        )
    """)

    # Shift codes tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shift_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            naam TEXT NOT NULL,
            start_tijd TEXT NOT NULL,
            eind_tijd TEXT NOT NULL,
            duur_uren REAL NOT NULL,
            is_weekdag BOOLEAN DEFAULT 1,
            is_zaterdag BOOLEAN DEFAULT 0,
            is_zondag BOOLEAN DEFAULT 0,
            FOREIGN KEY (post_id) REFERENCES posten(id),
            UNIQUE(post_id, code)
        )
    """)

    # Speciale codes tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS speciale_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            naam TEXT NOT NULL,
            beschrijving TEXT,
            telt_als_werkdag BOOLEAN DEFAULT 1,
            reset_12u_rust BOOLEAN DEFAULT 1,
            breekt_werk_reeks BOOLEAN DEFAULT 0,
            heeft_vaste_uren BOOLEAN DEFAULT 0,
            start_tijd TEXT,
            eind_tijd TEXT,
            duur_uren REAL
        )
    """)

    # HR regels tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hr_regels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT UNIQUE NOT NULL,
            waarde REAL NOT NULL,
            eenheid TEXT NOT NULL,
            beschrijving TEXT,
            actief_vanaf TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Typediensttabel (6-weken patroon)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS typetabel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_nummer INTEGER NOT NULL CHECK(week_nummer BETWEEN 1 AND 6),
            dag_nummer INTEGER NOT NULL CHECK(dag_nummer BETWEEN 1 AND 7),
            shift_type TEXT NOT NULL,
            UNIQUE(week_nummer, dag_nummer)
        )
    """)

    # Rode lijnen tabel (28-dagen cycli)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rode_lijnen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_datum DATE NOT NULL UNIQUE,
            eind_datum DATE NOT NULL,
            periode_nummer INTEGER NOT NULL
        )
    """)

    # Feestdagen tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feestdagen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum DATE NOT NULL UNIQUE,
            naam TEXT NOT NULL,
            is_zondagsrust BOOLEAN DEFAULT 1
        )
    """)

    # Planning maanden tabel (NEW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planning_maanden (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jaar INTEGER NOT NULL,
            maand INTEGER NOT NULL,
            status TEXT DEFAULT 'concept' 
                   CHECK(status IN ('concept', 'gepubliceerd')),
            gepubliceerd_op TIMESTAMP,
            gepubliceerd_door INTEGER REFERENCES gebruikers(id),
            UNIQUE(jaar, maand)
        )
    """)

    # Planning shifts tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planning_shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_id INTEGER NOT NULL,
            datum DATE NOT NULL,
            shift_code_id INTEGER,
            speciale_code_id INTEGER,
            opmerking TEXT,
            aangemaakt_door INTEGER,
            aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            gewijzigd_door INTEGER,
            gewijzigd_op TIMESTAMP,
            FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id),
            FOREIGN KEY (shift_code_id) REFERENCES shift_codes(id),
            FOREIGN KEY (speciale_code_id) REFERENCES speciale_codes(id),
            UNIQUE(gebruiker_id, datum)
        )
    """)

    # Verlof aanvragen tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verlof_aanvragen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_id INTEGER NOT NULL,
            start_datum DATE NOT NULL,
            eind_datum DATE NOT NULL,
            aantal_dagen INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' 
                   CHECK(status IN ('pending', 'goedgekeurd', 'geweigerd')),
            opmerking TEXT,
            aangevraagd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            behandeld_door INTEGER,
            behandeld_op TIMESTAMP,
            reden_weigering TEXT,
            FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id),
            FOREIGN KEY (behandeld_door) REFERENCES gebruikers(id)
        )
    """)

    # Voorkeuren tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voorkeuren (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_id INTEGER UNIQUE NOT NULL,
            eerste_keuze TEXT,
            tweede_keuze TEXT,
            derde_keuze TEXT,
            geen_nachten BOOLEAN DEFAULT 0,
            geen_weekends BOOLEAN DEFAULT 0,
            opmerkingen TEXT,
            FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id)
        )
    """)


def seed_data(conn, cursor):
    """Seed initiële data in database"""
    seed_admin_user(cursor)
    seed_interventie_post(cursor)
    seed_speciale_codes(cursor)
    seed_hr_regels(cursor)
    seed_typetabel(cursor)
    seed_rode_lijnen(cursor)
    conn.commit()


def seed_admin_user(cursor):
    """Maak admin gebruiker aan (UPDATED met UUID)"""
    wachtwoord_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
    admin_uuid = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO gebruikers 
        (gebruiker_uuid, gebruikersnaam, wachtwoord_hash, volledige_naam, 
         rol, is_reserve, is_actief)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (admin_uuid, 'admin', wachtwoord_hash, 'Administrator',
          'planner', 0, 1))


def seed_interventie_post(cursor):
    """Maak interventie post aan met alle shift codes"""
    cursor.execute("""
        INSERT INTO posten (naam, beschrijving)
        VALUES ('Interventie', 'Interventie post')
    """)

    post_id = cursor.lastrowid

    shifts = [
        # Weekdag shifts
        (post_id, '7101', 'Vroege dienst weekdag', '06:00', '14:00', 8.0, 1, 0, 0),
        (post_id, '7201', 'Late dienst weekdag', '14:00', '22:00', 8.0, 1, 0, 0),
        (post_id, '7301', 'Nachtdienst weekdag', '22:00', '06:00', 8.0, 1, 0, 0),
        # Zaterdag shifts
        (post_id, '7401', 'Vroege dienst zaterdag', '06:00', '14:00', 8.0, 0, 1, 0),
        (post_id, '7501', 'Late dienst zaterdag', '14:00', '22:00', 8.0, 0, 1, 0),
        (post_id, '7601', 'Nachtdienst zaterdag', '22:00', '06:00', 8.0, 0, 1, 0),
        # Zondag/RX shifts
        (post_id, '7701', 'Vroege dienst zondag', '06:00', '14:00', 8.0, 0, 0, 1),
        (post_id, '7801', 'Late dienst zondag', '14:00', '22:00', 8.0, 0, 0, 1),
        (post_id, '7901', 'Nachtdienst zondag', '22:00', '06:00', 8.0, 0, 0, 1),
    ]

    cursor.executemany("""
        INSERT INTO shift_codes 
        (post_id, code, naam, start_tijd, eind_tijd, duur_uren, 
         is_weekdag, is_zaterdag, is_zondag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, shifts)


def seed_speciale_codes(cursor):
    """Maak speciale codes aan"""
    codes = [
        ('VV', 'Verlof', 'Betaald verlof', 1, 1, 0, 0, None, None, None),
        ('VD', 'Vrij van dienst', 'ADV/compensatieverlof', 1, 1, 0, 0, None, None, None),
        ('DA', 'Arbeidsduurverkorting', 'DAV dag', 1, 1, 0, 0, None, None, None),
        ('RX', 'Zondagsrust', 'Rustdag (zondag)', 0, 0, 1, 0, None, None, None),
        ('CX', 'Zaterdagsrust', 'Rustdag (zaterdag)', 0, 0, 1, 0, None, None, None),
        ('Z', 'Ziek', 'Ziekteverlof', 0, 1, 1, 0, None, None, None),
        ('RDS', 'Roadshow/Meeting', 'Vergadering of roadshow', 1, 0, 0, 1, '10:00', '18:00', 8.0),
        ('TCR', 'Postkennis opleiding', 'Training/opleiding', 1, 0, 0, 0, None, None, None),
        ('T', 'Reserve/Thuis', 'Thuisstand (vervangen bij planning)', 0, 0, 0, 0, None, None, None),
    ]

    cursor.executemany("""
        INSERT INTO speciale_codes 
        (code, naam, beschrijving, telt_als_werkdag, reset_12u_rust, 
         breekt_werk_reeks, heeft_vaste_uren, start_tijd, eind_tijd, duur_uren)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, codes)


def seed_hr_regels(cursor):
    """Maak HR regels aan"""
    regels = [
        ('min_rust_uren', 12.0, 'uur', 'Minimale rusttijd tussen shifts'),
        ('max_uren_week', 50.0, 'uur', 'Maximum aantal uren per week'),
        ('max_werkdagen_28d', 19.0, 'dagen', 'Maximum gewerkte dagen per 28-dagen cyclus'),
        ('max_dagen_tussen_rx', 7.0, 'dagen', 'Maximum dagen tussen RX/CX'),
        ('max_werkdagen_reeks', 7.0, 'dagen', 'Maximum werkdagen achter elkaar'),
    ]

    cursor.executemany("""
        INSERT INTO hr_regels (naam, waarde, eenheid, beschrijving)
        VALUES (?, ?, ?, ?)
    """, regels)


def seed_typetabel(cursor):
    """Maak 6-weken typediensttabel aan"""
    # Week 1
    week1 = [
        (1, 1, 'V'), (1, 2, 'V'), (1, 3, 'RX'), (1, 4, 'L'),
        (1, 5, 'L'), (1, 6, 'CX'), (1, 7, 'RX')
    ]
    # Week 2
    week2 = [
        (2, 1, 'L'), (2, 2, 'L'), (2, 3, 'RX'), (2, 4, 'N'),
        (2, 5, 'N'), (2, 6, 'CX'), (2, 7, 'RX')
    ]
    # Week 3
    week3 = [
        (3, 1, 'N'), (3, 2, 'N'), (3, 3, 'RX'), (3, 4, 'T'),
        (3, 5, 'T'), (3, 6, 'CX'), (3, 7, 'RX')
    ]
    # Week 4
    week4 = [
        (4, 1, 'T'), (4, 2, 'T'), (4, 3, 'RX'), (4, 4, 'V'),
        (4, 5, 'V'), (4, 6, 'CX'), (4, 7, 'RX')
    ]
    # Week 5
    week5 = [
        (5, 1, 'V'), (5, 2, 'V'), (5, 3, 'RX'), (5, 4, 'L'),
        (5, 5, 'L'), (5, 6, 'CX'), (5, 7, 'RX')
    ]
    # Week 6
    week6 = [
        (6, 1, 'L'), (6, 2, 'L'), (6, 3, 'RX'), (6, 4, 'N'),
        (6, 5, 'N'), (6, 6, 'CX'), (6, 7, 'RX')
    ]

    alle_weken = week1 + week2 + week3 + week4 + week5 + week6

    cursor.executemany("""
        INSERT INTO typetabel (week_nummer, dag_nummer, shift_type)
        VALUES (?, ?, ?)
    """, alle_weken)


def seed_rode_lijnen(cursor):
    """Genereer 100 periodes rode lijnen (28-dagen cycli)"""
    start_datum = datetime(2024, 1, 1)

    for periode in range(1, 101):
        eind_datum = start_datum + timedelta(days=27)

        cursor.execute("""
            INSERT INTO rode_lijnen (start_datum, eind_datum, periode_nummer)
            VALUES (?, ?, ?)
        """, (start_datum.strftime('%Y-%m-%d'),
              eind_datum.strftime('%Y-%m-%d'),
              periode))

        start_datum = eind_datum + timedelta(days=1)