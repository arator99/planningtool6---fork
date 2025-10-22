#config.py

# Applicatie instellingen
APP_NAME = "Planning Tool"

# Versie Beheer (v0.6.15)
# APP_VERSION verhoogt bij elke wijziging (GUI of DB)
# MIN_DB_VERSION verhoogt alleen bij database schema wijzigingen
APP_VERSION = "0.6.15"
MIN_DB_VERSION = "0.6.14"  # Laatste DB wijziging: v0.6.14 (gebruiker_werkposten tabel)

# Window settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# Kleuren
COLORS = {
    'zondag_feestdag': '#FFE5E5',
    'zaterdag': '#E5F3FF',
    'weekdag': '#FFFFFF',
}