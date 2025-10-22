# services/export_service.py
"""
Export Service voor Planning Tool
Genereert Excel exports van planning voor HR
"""

from pathlib import Path
from datetime import datetime, timedelta
from database.connection import get_connection
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
import calendar


# Nederlandse maandnamen
MAAND_NAMEN = {
    1: 'januari', 2: 'februari', 3: 'maart', 4: 'april',
    5: 'mei', 6: 'juni', 7: 'juli', 8: 'augustus',
    9: 'september', 10: 'oktober', 11: 'november', 12: 'december'
}


def export_maand_naar_excel(jaar: int, maand: int) -> str:
    """
    Exporteer planning van een maand naar Excel bestand

    Args:
        jaar: Jaar (bijv. 2025)
        maand: Maand nummer (1-12)

    Returns:
        str: Pad naar gegenereerd bestand
    """
    # Maak exports directory als die niet bestaat
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)

    # Bestandsnaam: maandnaam_jaartal.xlsx
    maand_naam = MAAND_NAMEN[maand]
    bestand_naam = f"{maand_naam}_{jaar}.xlsx"
    bestand_pad = export_dir / bestand_naam

    # Haal planning data op
    planning_data = haal_planning_data(jaar, maand)

    # Maak Excel bestand
    wb = Workbook()
    ws = wb.active
    ws.title = f"{maand_naam.capitalize()} {jaar}"

    # Styling definities
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    datum_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    datum_font = Font(bold=True, size=10)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')

    # Bepaal alle dagen in de maand
    dagen_in_maand = calendar.monthrange(jaar, maand)[1]
    datums = []
    for dag in range(1, dagen_in_maand + 1):
        datum = datetime(jaar, maand, dag)
        datums.append(datum)

    # Header rij 1: Titel
    ws.merge_cells('A1:B1')
    titel_cell = ws['A1']
    titel_cell.value = f"Planning {maand_naam.capitalize()} {jaar}"
    titel_cell.font = Font(bold=True, size=14, color="366092")
    titel_cell.alignment = center_alignment

    # Header rij 2: Kolom headers
    ws['A2'] = "Naam"
    ws['A2'].font = header_font
    ws['A2'].fill = header_fill
    ws['A2'].border = border
    ws['A2'].alignment = center_alignment

    # Datum kolommen
    for col_idx, datum in enumerate(datums, start=2):
        cell = ws.cell(row=2, column=col_idx)
        # Formaat: "Ma 1" of "Di 2" etc.
        dag_naam = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'][datum.weekday()]
        cell.value = f"{dag_naam}\n{datum.day}"
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    # Data rijen
    row_idx = 3
    for gebruiker_data in planning_data:
        # Naam kolom
        naam_cell = ws.cell(row=row_idx, column=1)
        naam_cell.value = gebruiker_data['naam']
        naam_cell.font = Font(size=10)
        naam_cell.border = border
        naam_cell.alignment = Alignment(vertical='center')

        # Shift codes per dag
        for col_idx, datum in enumerate(datums, start=2):
            datum_str = datum.strftime('%Y-%m-%d')
            shift_code = gebruiker_data['planning'].get(datum_str, '')

            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = shift_code
            cell.font = Font(size=10)
            cell.border = border
            cell.alignment = center_alignment

            # Achtergrondkleur voor weekend/feestdag
            if datum.weekday() >= 5:  # Zaterdag of Zondag
                cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

        row_idx += 1

    # Kolom breedtes aanpassen
    ws.column_dimensions['A'].width = 25  # Naam kolom
    for col_idx in range(2, len(datums) + 2):
        ws.column_dimensions[get_column_letter(col_idx)].width = 8  # Datum kolommen

    # Rij hoogtes
    ws.row_dimensions[1].height = 25  # Titel
    ws.row_dimensions[2].height = 30  # Header

    # Sla op
    wb.save(bestand_pad)

    return str(bestand_pad)


def haal_planning_data(jaar: int, maand: int) -> list:
    """
    Haal planning data op voor een maand
    Inclusief reserves (is_reserve=1)

    Returns:
        List van dicts met naam en planning per datum
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Haal alle gebruikers op inclusief reserves, exclusief admin
    cursor.execute("""
        SELECT id, volledige_naam, is_reserve
        FROM gebruikers
        WHERE is_actief = 1
        AND gebruikersnaam != 'admin'
        ORDER BY is_reserve ASC, volledige_naam ASC
    """)

    gebruikers = cursor.fetchall()

    # Bepaal datum range
    eerste_dag = f"{jaar:04d}-{maand:02d}-01"
    if maand == 12:
        volgende_maand = f"{jaar + 1:04d}-01-01"
    else:
        volgende_maand = f"{jaar:04d}-{maand + 1:02d}-01"

    planning_data = []

    for gebruiker in gebruikers:
        gebruiker_id = gebruiker['id']
        naam = gebruiker['volledige_naam']

        # Haal planning op voor deze gebruiker
        cursor.execute("""
            SELECT datum, shift_code
            FROM planning
            WHERE gebruiker_id = ?
            AND datum >= ?
            AND datum < ?
            ORDER BY datum
        """, (gebruiker_id, eerste_dag, volgende_maand))

        planning_records = cursor.fetchall()

        # Maak dict van datum -> shift_code
        planning_dict = {}
        for record in planning_records:
            planning_dict[record['datum']] = record['shift_code']

        planning_data.append({
            'naam': naam,
            'planning': planning_dict
        })

    conn.close()

    return planning_data
