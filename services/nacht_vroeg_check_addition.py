"""
Nieuwe check_nacht_gevolgd_door_vroeg() method voor constraint_checker.py

Deze method moet worden toegevoegd VOOR de check_all() method (rond regel 1367)
"""

NEW_METHOD = '''
    def check_nacht_gevolgd_door_vroeg(
        self,
        planning: List[PlanningRegel],
        gebruiker_id: Optional[int] = None
    ) -> ConstraintCheckResult:
        """
        Check: Nacht shift mag niet gevolgd worden door vroeg shift

        Business Rules:
        - Nacht shift (shift_type='nacht') direct gevolgd door vroeg shift (shift_type='vroeg') = VERBODEN
        - TENZIJ er een "breek code" tussen zit (verlof, ziekte)
        - Breek codes worden geconfigureerd in HR regels (beschrijving veld: comma-separated terms)

        Args:
            planning: Lijst van planning regels
            gebruiker_id: Optioneel filter op gebruiker

        Returns:
            ConstraintCheckResult met violations
        """
        # Lees breek terms uit HR config (default: verlof,ziek)
        breek_terms_str = self.config.get('Nacht gevolgd door vroeg verboden', {}).get('beschrijving', 'verlof,ziek')
        breek_terms = {term.strip() for term in breek_terms_str.split(',')}

        # Filter planning op gebruiker
        if gebruiker_id is not None:
            planning = [p for p in planning if p.gebruiker_id == gebruiker_id]

        # Sort op datum
        planning = sorted(planning, key=lambda p: p.datum)

        violations = []

        # Loop door planning om nacht → vroeg patroon te vinden
        for i in range(len(planning) - 1):
            huidige = planning[i]
            volgende = planning[i + 1]

            # Check of volgende dag is (moet consecutive zijn)
            if (volgende.datum - huidige.datum).days != 1:
                continue  # Niet opeenvolgend

            # Check of huidige shift een nacht is
            if not huidige.shift_code:
                continue

            is_nacht = self._is_shift_type(huidige.shift_code, 'nacht')
            if not is_nacht:
                continue

            # Check of volgende shift een vroeg is
            if not volgende.shift_code:
                continue

            is_vroeg = self._is_shift_type(volgende.shift_code, 'vroeg')
            if not is_vroeg:
                continue

            # We hebben nacht → vroeg patroon gevonden
            # Check of er een breek code is (verlof/ziekte)
            heeft_breek_code = self._has_term_match(volgende.shift_code, breek_terms)

            if not heeft_breek_code:
                # VIOLATION: Nacht gevolgd door vroeg zonder breek code
                violations.append(Violation(
                    type=ViolationType.NACHT_VROEG_VERBODEN,
                    severity=ViolationSeverity.ERROR,
                    gebruiker_id=volgende.gebruiker_id,
                    datum=volgende.datum,
                    datum_range=(huidige.datum, volgende.datum),
                    beschrijving=f"Nacht shift gevolgd door vroeg shift: {huidige.shift_code} ({huidige.datum.strftime('%d %b')}) -> {volgende.shift_code} ({volgende.datum.strftime('%d %b')})",
                    details={
                        'nacht_shift': huidige.shift_code,
                        'nacht_datum': huidige.datum.isoformat(),
                        'vroeg_shift': volgende.shift_code,
                        'vroeg_datum': volgende.datum.isoformat(),
                        'breek_terms': list(breek_terms)
                    },
                    affected_shifts=[
                        (huidige.gebruiker_id, huidige.datum),
                        (volgende.gebruiker_id, volgende.datum)
                    ],
                    suggested_fixes=[
                        f"Plan verlof of ziekte tussen nacht ({huidige.datum.strftime('%d %b')}) en vroeg ({volgende.datum.strftime('%d %b')})",
                        f"Verander vroeg shift op {volgende.datum.strftime('%d %b')} naar laat of nacht",
                        f"Verander nacht shift op {huidige.datum.strftime('%d %b')} naar laat"
                    ]
                ))

        return ConstraintCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            metadata={'violations_count': len(violations)}
        )

    def _is_shift_type(self, shift_code: str, shift_type: str) -> bool:
        """
        Check of een shift code een bepaald shift type heeft

        Args:
            shift_code: Shift code (bijv. '1301', 'VV')
            shift_type: Type ('nacht', 'vroeg', 'laat', 'dag')

        Returns:
            True als shift dit type heeft
        """
        # Check in shift_times mapping
        if shift_code in self.shift_times:
            shift_info = self.shift_times[shift_code]
            return shift_info.get('shift_type') == shift_type

        return False

    def _has_term_match(self, code: str, terms: set) -> bool:
        """
        Check of een code een van de gegeven terms heeft

        Args:
            code: Shift code
            terms: Set van terms om te matchen (bijv. {'verlof', 'ziek'})

        Returns:
            True als code één van de terms heeft
        """
        # Check in shift_times mapping (speciale codes hebben 'term' veld)
        if code in self.shift_times:
            shift_info = self.shift_times[shift_code]
            code_term = shift_info.get('term')
            if code_term and code_term in terms:
                return True

        return False
'''

print("=== Code to Add ===")
print(NEW_METHOD)
print("\n=== Instructions ===")
print("1. Open services/constraint_checker.py")
print("2. Find line 1367 (before 'def check_all')")
print("3. Insert the code above")
print("4. Add 'NACHT_VROEG_VERBODEN' to ViolationType enum")
print("5. Update check_all() to call the new check")
