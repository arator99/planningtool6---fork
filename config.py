#config.py

# Applicatie instellingen
APP_NAME = "Planning Tool"

# Versie Beheer (v0.6.28)
# APP_VERSION verhoogt bij elke wijziging (GUI of DB)
# MIN_DB_VERSION verhoogt alleen bij database schema wijzigingen
APP_VERSION = "0.6.28"
MIN_DB_VERSION = "0.6.28"  # Laatste DB wijziging: v0.6.28 (voornaam/achternaam kolommen - sortering op achternaam)
# v0.6.28: ISSUE-002 fix - Gebruikers sortering op achternaam (eerst vaste, dan reserves)

# Performance settings
ENABLE_VALIDATION_CACHE = False  # Toggle ValidationCache voor performance testing (v0.6.26.2)
                                  # True = Batch preload (5 queries, sneller lokaal)
                                  # False = Direct queries (900+ queries, mogelijk sneller over netwerk)

# Window settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# Kleuren
COLORS = {
    'zondag_feestdag': '#FFE5E5',
    'zaterdag': '#E5F3FF',
    'weekdag': '#FFFFFF',
}