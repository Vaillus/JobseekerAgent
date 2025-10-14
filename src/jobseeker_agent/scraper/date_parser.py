import re
from datetime import datetime, timedelta


def parse_relative_date(relative_date_str: str) -> str:
    """
    Convertit une chaîne de caractères de date relative (ex: "1 day ago", "2 weeks ago")
    en une date au format YYYY-MM-DD.
    """
    if not isinstance(relative_date_str, str):
        return "Invalid input"

    relative_date_str = relative_date_str.lower().strip()
    now = datetime.now()
    
    # Gérer les cas comme "today", "yesterday", "just now"
    if "today" in relative_date_str or "aujourd'hui" in relative_date_str or "just now" in relative_date_str:
        return now.strftime("%Y-%m-%d")
    if "yesterday" in relative_date_str or "hier" in relative_date_str:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    # Utiliser regex pour extraire le nombre et l'unité de temps
    match = re.search(r"(\d+)\s+(day|week|month|hour|minute)s?", relative_date_str)
    if not match:
        match = re.search(r"(\d+)\s+(jour|semaine|mois|heure|minute)s?", relative_date_str)

    if match:
        quantity = int(match.group(1))
        unit = match.group(2)

        if "day" in unit or "jour" in unit:
            delta = timedelta(days=quantity)
        elif "week" in unit or "semaine" in unit:
            delta = timedelta(weeks=quantity)
        elif "month" in unit or "mois" in unit:
            # Approximation simple, 30 jours par mois
            delta = timedelta(days=quantity * 30)
        elif "hour" in unit or "heure" in unit:
            delta = timedelta(hours=quantity)
        elif "minute" in unit:
            delta = timedelta(minutes=quantity)
        else:
            return "N/A"
        
        past_date = now - delta
        return past_date.strftime("%Y-%m-%d")
    
    return "N/A"
