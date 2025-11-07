# database/connection.py
"""
Database connectie en initialisatie voor Planning Tool
UPDATED: v0.6.4+ structuur met werkposten en simpele planning tabel
"""

import sqlite3
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


def get_db_version():
    """
    Haal database versie op uit db_metadata tabel.
    Returns: versie string (bijv. "0.6.12") of None als niet gevonden
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check of db_metadata tabel bestaat
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='db_metadata'
        """)

        if not cursor.fetchone():
            conn.close()
            return None  # Oude database zonder versie tracking

        # Haal laatste versie op
        cursor.execute("""
            SELECT version_number FROM db_metadata
            ORDER BY id DESC LIMIT 1
        """)

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    except sqlite3.Error:
        return None


def check_db_compatibility():
    """
    Controleer of database versie compatibel is met applicatie.
    Returns: (is_compatible: bool, db_version: str|None, error_msg: str|None)
    """
    from config import MIN_DB_VERSION, APP_VERSION

    db_version = get_db_version()

    # Geen versie gevonden = oude database
    if db_version is None:
        return (False, None,
                f"Database heeft geen versie informatie.\n\n"
                f"De applicatie vereist database versie {MIN_DB_VERSION} of hoger.\n"
                f"Neem contact op met de beheerder voor een database upgrade.")

    # Versie vergelijken (simpele string vergelijking werkt voor X.Y.Z formaat)
    if db_version < MIN_DB_VERSION:
        return (False, db_version,
                f"Database versie {db_version} is te oud.\n\n"
                f"De applicatie vereist database versie {MIN_DB_VERSION} of hoger.\n"
                f"Neem contact op met de beheerder voor een database upgrade.")

    # Database is nieuwer dan app (zou niet moeten gebeuren)
    if db_version > APP_VERSION:
        return (False, db_version,
                f"Database versie {db_version} is nieuwer dan de applicatie.\n\n"
                f"Applicatie versie: {APP_VERSION}\n"
                f"Upgrade de applicatie naar de nieuwste versie.")

    # Alles OK
    return (True, db_version, None)


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

    # Database metadata tabel (v0.6.13 - NIEUW: versie tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS db_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_number TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            migration_description TEXT
        )
    """)

    # Gebruikers tabel (UPDATED met UUID, shift_voorkeuren v0.6.11, theme_voorkeur v0.6.12)
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
            shift_voorkeuren TEXT,
            theme_voorkeur TEXT DEFAULT 'light',
            is_actief BOOLEAN DEFAULT 1,
            aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            gedeactiveerd_op TIMESTAMP,
            laatste_login TIMESTAMP
        )
    """)

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_gebruikersnaam ON gebruikers(gebruikersnaam)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_gebruiker_uuid ON gebruikers(gebruiker_uuid)")

    # Werkposten tabel (v0.6.4 - NIEUW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS werkposten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT UNIQUE NOT NULL,
            beschrijving TEXT,
            telt_als_werkdag BOOLEAN DEFAULT 1,
            reset_12u_rust BOOLEAN DEFAULT 1,
            breekt_werk_reeks BOOLEAN DEFAULT 0,
            is_actief BOOLEAN DEFAULT 1,
            aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            gedeactiveerd_op TIMESTAMP
        )
    """)

    # Shift codes tabel (v0.6.4 - UPDATED structuur, v0.6.21 + is_kritisch)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shift_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            werkpost_id INTEGER NOT NULL,
            dag_type TEXT NOT NULL CHECK(dag_type IN ('weekdag', 'zaterdag', 'zondag')),
            shift_type TEXT NOT NULL CHECK(shift_type IN ('vroeg', 'laat', 'nacht', 'dag')),
            code TEXT NOT NULL,
            start_uur TEXT NOT NULL,
            eind_uur TEXT NOT NULL,
            is_kritisch BOOLEAN DEFAULT 0,
            FOREIGN KEY (werkpost_id) REFERENCES werkposten(id),
            UNIQUE(werkpost_id, dag_type, shift_type)
        )
    """)

    # Gebruiker Werkposten koppeling tabel (v0.6.14 - NIEUW: many-to-many relatie)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gebruiker_werkposten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_id INTEGER NOT NULL,
            werkpost_id INTEGER NOT NULL,
            prioriteit INTEGER DEFAULT 1,
            aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(gebruiker_id, werkpost_id),
            FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id) ON DELETE CASCADE,
            FOREIGN KEY (werkpost_id) REFERENCES werkposten(id) ON DELETE CASCADE
        )
    """)

    # Index voor gebruiker_werkposten performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_gebruiker_werkposten_gebruiker
        ON gebruiker_werkposten(gebruiker_id, prioriteit)
    """)

    # Speciale codes tabel (v0.6.4, updated v0.6.7 met term kolom)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS speciale_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            naam TEXT NOT NULL,
            term TEXT UNIQUE,
            telt_als_werkdag BOOLEAN DEFAULT 1,
            reset_12u_rust BOOLEAN DEFAULT 1,
            breekt_werk_reeks BOOLEAN DEFAULT 0
        )
    """)

    # Planning tabel (v0.6.4 - SIMPELE versie)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_id INTEGER NOT NULL,
            datum TEXT NOT NULL,
            shift_code TEXT,
            notitie TEXT,
            status TEXT DEFAULT 'concept' CHECK(status IN ('concept', 'gepubliceerd')),
            aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id),
            UNIQUE(gebruiker_id, datum)
        )
    """)

    # HR regels tabel (updated: versioning support)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hr_regels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            waarde REAL NOT NULL,
            eenheid TEXT NOT NULL,
            beschrijving TEXT,
            actief_vanaf TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actief_tot TIMESTAMP,
            is_actief BOOLEAN DEFAULT 1
        )
    """)

    # Index voor actieve regels query performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_hr_regels_actief
        ON hr_regels(naam, is_actief)
    """)

    # Rode lijnen configuratie tabel (versioning support)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rode_lijnen_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_datum DATE NOT NULL,
            interval_dagen INTEGER NOT NULL,
            actief_vanaf TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actief_tot TIMESTAMP,
            is_actief BOOLEAN DEFAULT 1
        )
    """)

    # Index voor actieve config
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rode_lijnen_config_actief
        ON rode_lijnen_config(is_actief)
    """)

    # Typetabel versies (v0.6.6)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS typetabel_versies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                versie_naam TEXT NOT NULL,
                aantal_weken INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('actief', 'concept', 'archief')),
                actief_vanaf DATE,
                actief_tot DATE,
                aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                laatste_wijziging TIMESTAMP,
                opmerking TEXT
            )
    """)

    # Typetabel data (v0.6.6)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS typetabel_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                versie_id INTEGER NOT NULL,
                week_nummer INTEGER NOT NULL,
                dag_nummer INTEGER NOT NULL,
                shift_type TEXT,
                UNIQUE(versie_id, week_nummer, dag_nummer),
                FOREIGN KEY (versie_id) REFERENCES typetabel_versies(id) ON DELETE CASCADE
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

    # Feestdagen tabel (met is_variabel)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feestdagen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum DATE NOT NULL UNIQUE,
            naam TEXT NOT NULL,
            is_zondagsrust BOOLEAN DEFAULT 1,
            is_variabel BOOLEAN DEFAULT 0
        )
    """)

    # Verlof aanvragen tabel (v0.6.10: toegekende_code_term toegevoegd)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verlof_aanvragen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_id INTEGER NOT NULL,
            start_datum DATE NOT NULL,
            eind_datum DATE NOT NULL,
            aantal_dagen INTEGER NOT NULL,
            status TEXT DEFAULT 'pending'
                   CHECK(status IN ('pending', 'goedgekeurd', 'geweigerd')),
            toegekende_code_term TEXT,
            opmerking TEXT,
            aangevraagd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            behandeld_door INTEGER,
            behandeld_op TIMESTAMP,
            reden_weigering TEXT,
            FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id),
            FOREIGN KEY (behandeld_door) REFERENCES gebruikers(id)
        )
    """)

    # Verlof saldo tabel (v0.6.10: NIEUW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verlof_saldo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gebruiker_id INTEGER NOT NULL,
            jaar INTEGER NOT NULL,
            verlof_totaal INTEGER DEFAULT 0,
            verlof_overgedragen INTEGER DEFAULT 0,
            verlof_opgenomen INTEGER DEFAULT 0,
            kd_totaal INTEGER DEFAULT 0,
            kd_overgedragen INTEGER DEFAULT 0,
            kd_opgenomen INTEGER DEFAULT 0,
            opmerking TEXT,
            aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            gewijzigd_op TIMESTAMP,
            FOREIGN KEY (gebruiker_id) REFERENCES gebruikers(id) ON DELETE CASCADE,
            UNIQUE(gebruiker_id, jaar)
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
    print("\nSeeding data...")
    seed_db_version(cursor)
    seed_admin_user(cursor)
    seed_interventie_werkpost(cursor)
    seed_speciale_codes(cursor)
    seed_hr_regels(cursor)
    seed_rode_lijnen_config(cursor)
    seed_typetabel(cursor)
    seed_rode_lijnen(cursor)
    conn.commit()
    print("[OK] Seed data compleet\n")


def seed_db_version(cursor):
    """Seed database versie (v0.6.13)"""
    from config import MIN_DB_VERSION

    cursor.execute("SELECT COUNT(*) FROM db_metadata")
    if cursor.fetchone()[0] > 0:
        print("  ↳ Database versie al aanwezig")
        return

    cursor.execute("""
        INSERT INTO db_metadata (version_number, migration_description)
        VALUES (?, ?)
    """, (MIN_DB_VERSION, f"Database schema versie {MIN_DB_VERSION}"))

    print(f"  [OK] Database versie ingesteld op {MIN_DB_VERSION}")


def seed_admin_user(cursor):
    """Seed admin gebruiker"""
    cursor.execute("SELECT COUNT(*) FROM gebruikers WHERE gebruikersnaam = 'admin'")
    if cursor.fetchone()[0] > 0:
        print("  ↳ Admin user al aanwezig")
        return

    # Hash wachtwoord 'admin'
    wachtwoord_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
    admin_uuid = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO gebruikers 
        (gebruiker_uuid, gebruikersnaam, wachtwoord_hash, volledige_naam, rol, 
         is_reserve, startweek_typedienst, is_actief, aangemaakt_op)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        admin_uuid,
        'admin',
        wachtwoord_hash,
        'Administrator',
        'planner',
        0,
        None,
        1
    ))

    print("  [OK] Admin user aangemaakt (gebruikersnaam: 'admin', wachtwoord: 'admin')")


def seed_interventie_werkpost(cursor):
    """Maak interventie werkpost aan met alle shift codes (v0.6.4 structuur)"""

    # Maak werkpost
    cursor.execute("""
        INSERT INTO werkposten (naam, beschrijving, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks, is_actief)
        VALUES ('Interventie', 'Interventie post', 1, 0, 0, 1)
    """)

    werkpost_id = cursor.lastrowid

    # Shift codes met nieuwe structuur (dag_type, shift_type, code)
    shifts = [
        # Weekdag shifts
        (werkpost_id, 'weekdag', 'vroeg', '7101', '06:00', '14:00'),
        (werkpost_id, 'weekdag', 'laat', '7201', '14:00', '22:00'),
        (werkpost_id, 'weekdag', 'nacht', '7301', '22:00', '06:00'),
        # Zaterdag shifts
        (werkpost_id, 'zaterdag', 'vroeg', '7401', '06:00', '14:00'),
        (werkpost_id, 'zaterdag', 'laat', '7501', '14:00', '22:00'),
        (werkpost_id, 'zaterdag', 'nacht', '7601', '22:00', '06:00'),
        # Zondag shifts
        (werkpost_id, 'zondag', 'vroeg', '7701', '06:00', '14:00'),
        (werkpost_id, 'zondag', 'laat', '7801', '14:00', '22:00'),
        (werkpost_id, 'zondag', 'nacht', '7901', '22:00', '06:00'),
    ]

    cursor.executemany("""
        INSERT INTO shift_codes 
        (werkpost_id, dag_type, shift_type, code, start_uur, eind_uur)
        VALUES (?, ?, ?, ?, ?, ?)
    """, shifts)

    print(f"  [OK] Werkpost 'Interventie' aangemaakt met {len(shifts)} shift codes")


def seed_speciale_codes(cursor):
    """Maak speciale codes aan (v0.6.4 structuur, v0.6.7 met termen, v0.6.10 + KD)"""
    codes = [
        # Code, Naam, Term, Telt_werkdag, Reset_12u, Breekt_reeks
        ('VV', 'Verlof', 'verlof', 1, 1, 0),
        ('KD', 'Kompensatiedag', 'kompensatiedag', 1, 1, 0),
        ('RX', 'Zondagsrust', 'zondagrust', 0, 0, 1),
        ('CX', 'Zaterdagsrust', 'zaterdagrust', 0, 0, 1),
        ('Z', 'Ziek', 'ziek', 0, 1, 1),
        ('DA', 'Arbeidsduurverkorting', 'arbeidsduurverkorting', 1, 1, 0),
        # Vrije codes (zonder term)
        ('VD', 'Vrij van dienst', None, 1, 1, 0),
        ('RDS', 'Roadshow/Meeting', None, 1, 0, 0),
        ('TCR', 'Postkennis opleiding', None, 1, 0, 0),
        ('SCR', 'Servicecentrum opleiding', None, 1, 0, 0),
        ('T', 'Reserve/Thuis', None, 0, 0, 0),
    ]

    cursor.executemany("""
        INSERT INTO speciale_codes
        (code, naam, term, telt_als_werkdag, reset_12u_rust, breekt_werk_reeks)
        VALUES (?, ?, ?, ?, ?, ?)
    """, codes)

    print(f"  [OK] {len(codes)} speciale codes aangemaakt (6 met systeem-termen)")


def seed_hr_regels(cursor):
    """
    Maak voorbeeld HR regels aan
    BELANGRIJK: Dit zijn VOORBEELDEN - controleer met HR!
    """
    regels = [
        ('min_rust_uren', 12.0, 'uur', 'VOORBEELD - Minimale rusttijd tussen shifts'),
        ('max_uren_week', 50.0, 'uur', 'VOORBEELD - Maximum aantal uren per week'),
        ('max_werkdagen_cyclus', 19.0, 'dagen', 'VOORBEELD - Maximum gewerkte dagen tussen rode lijnen'),
        ('max_dagen_tussen_rx', 7.0, 'dagen', 'VOORBEELD - Maximum dagen tussen RX/CX'),
        ('max_werkdagen_reeks', 7.0, 'dagen', 'VOORBEELD - Maximum werkdagen achter elkaar'),
        ('Vervaldatum overgedragen verlof', '01-05', 'datum', 'Datum waarop overgedragen verlof vervalt (DD-MM format, default: 1 mei)'),
        ('Max overdracht KD naar volgend jaar', 35.0, 'dagen', 'Maximum aantal KD dagen overdraagbaar naar volgend jaar'),
        ('week_definitie', 'ma-00:00|zo-23:59', 'periode', 'Definitie wanneer werkweek start en eindigt (voor 50-uur regel)'),
        ('weekend_definitie', 'vr-22:00|ma-06:00', 'periode', 'Definitie wanneer weekend start en eindigt (exclusieve grenzen: shift moet BINNEN periode vallen, niet OP de grens)'),
        ('max_weekends_achter_elkaar', 6.0, 'weekends', 'VOORBEELD - Maximum aantal weekends achter elkaar werken'),
    ]

    cursor.executemany("""
        INSERT INTO hr_regels (naam, waarde, eenheid, beschrijving, is_actief)
        VALUES (?, ?, ?, ?, 1)
    """, regels)

    print(f"  [OK] {len(regels)} HR regels aangemaakt (VOORBEELDEN - controleer met HR!)")


def seed_typetabel(cursor):
    """Maak initiele typetabel versie aan (v0.6.6)"""

    # Check of er al een typetabel versie bestaat
    cursor.execute("SELECT COUNT(*) FROM typetabel_versies")
    if cursor.fetchone()[0] > 0:
        print("  ↳ Typetabel versie al aanwezig")
        return

    # Maak actieve typetabel versie
    cursor.execute("""
        INSERT INTO typetabel_versies 
        (versie_naam, aantal_weken, status, actief_vanaf, opmerking, laatste_wijziging)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Interventie 6 weken",
        6,
        "actief",
        "2024-01-01",
        "Standaard 6-weken interventie patroon",
        datetime.now().isoformat()
    ))

    versie_id = cursor.lastrowid

    # Week 1
    week1 = [
        (versie_id, 1, 1, 'V'), (versie_id, 1, 2, 'V'), (versie_id, 1, 3, 'RX'),
        (versie_id, 1, 4, 'L'), (versie_id, 1, 5, 'L'), (versie_id, 1, 6, 'CX'),
        (versie_id, 1, 7, 'RX')
    ]
    # Week 2
    week2 = [
        (versie_id, 2, 1, 'L'), (versie_id, 2, 2, 'L'), (versie_id, 2, 3, 'RX'),
        (versie_id, 2, 4, 'N'), (versie_id, 2, 5, 'N'), (versie_id, 2, 6, 'CX'),
        (versie_id, 2, 7, 'RX')
    ]
    # Week 3
    week3 = [
        (versie_id, 3, 1, 'N'), (versie_id, 3, 2, 'N'), (versie_id, 3, 3, 'RX'),
        (versie_id, 3, 4, 'T'), (versie_id, 3, 5, 'T'), (versie_id, 3, 6, 'CX'),
        (versie_id, 3, 7, 'RX')
    ]
    # Week 4
    week4 = [
        (versie_id, 4, 1, 'T'), (versie_id, 4, 2, 'T'), (versie_id, 4, 3, 'RX'),
        (versie_id, 4, 4, 'V'), (versie_id, 4, 5, 'V'), (versie_id, 4, 6, 'CX'),
        (versie_id, 4, 7, 'RX')
    ]
    # Week 5
    week5 = [
        (versie_id, 5, 1, 'V'), (versie_id, 5, 2, 'V'), (versie_id, 5, 3, 'RX'),
        (versie_id, 5, 4, 'L'), (versie_id, 5, 5, 'L'), (versie_id, 5, 6, 'CX'),
        (versie_id, 5, 7, 'RX')
    ]
    # Week 6
    week6 = [
        (versie_id, 6, 1, 'L'), (versie_id, 6, 2, 'L'), (versie_id, 6, 3, 'RX'),
        (versie_id, 6, 4, 'N'), (versie_id, 6, 5, 'N'), (versie_id, 6, 6, 'CX'),
        (versie_id, 6, 7, 'RX')
    ]

    alle_weken = week1 + week2 + week3 + week4 + week5 + week6

    cursor.executemany("""
        INSERT INTO typetabel_data (versie_id, week_nummer, dag_nummer, shift_type)
        VALUES (?, ?, ?, ?)
    """, alle_weken)

    print(f"  [OK] Typetabel versie '{versie_id}' aangemaakt (42 entries - 6 weken, status: actief)")


def seed_rode_lijnen(cursor):
    """
    Seed minimale rode lijnen (12 maanden vooruit)
    Verdere periodes worden on-demand gegenereerd via ensure_jaar_data()
    """
    # Check of er al rode lijnen zijn
    cursor.execute("SELECT COUNT(*) FROM rode_lijnen")
    if cursor.fetchone()[0] > 0:
        print("  ↳ Rode lijnen al aanwezig")
        return

    # Start datum: 29 juli 2024 (periode 1, uitkomend op periode 17 = 20 oktober 2025)
    start = datetime(2024, 7, 29)

    # Genereer 12 maanden (≈13 periodes van 28 dagen)
    aantal_periodes = 13

    for i in range(aantal_periodes):
        start_datum = start + timedelta(days=28 * i)
        eind_datum = start_datum + timedelta(days=27)  # 28 dagen cyclus (dag 1 t/m dag 28)
        periode_nummer = i + 1  # Start bij 1

        cursor.execute("""
            INSERT INTO rode_lijnen (periode_nummer, start_datum, eind_datum)
            VALUES (?, ?, ?)
        """, (periode_nummer, start_datum.isoformat(), eind_datum.isoformat()))

    print(f"  [OK] {aantal_periodes} rode lijnen periodes aangemaakt (12 maanden)")
    print(f"    Vanaf: {start.strftime('%d-%m-%Y')}")
    print(f"    Tot: {(start + timedelta(days=28 * aantal_periodes)).strftime('%d-%m-%Y')}")
    print("    Verdere periodes worden on-demand gegenereerd")


def seed_rode_lijnen_config(cursor):
    """Seed initiele rode lijnen configuratie (defaults)"""
    # Check of er al config is
    cursor.execute("SELECT COUNT(*) FROM rode_lijnen_config")
    if cursor.fetchone()[0] > 0:
        print("  ↳ Rode lijnen config al aanwezig")
        return

    # Default configuratie (periode 1 start, uitkomend op periode 17 = 20 oktober 2025)
    start_datum = datetime(2024, 7, 29)
    interval_dagen = 28

    cursor.execute("""
        INSERT INTO rode_lijnen_config
        (start_datum, interval_dagen, is_actief)
        VALUES (?, ?, 1)
    """, (start_datum.date().isoformat(), interval_dagen))

    print("  [OK] Rode lijnen config aangemaakt")
    print(f"    Start: {start_datum.strftime('%d-%m-%Y')}")
    print(f"    Interval: {interval_dagen} dagen")