"""Project-level display formatting.

Lives beside json_log for the same reason: it is infrastructure every app may
need, not the property of any one of them.
"""
import datetime

from django.utils import formats


def br_date(value: datetime.date) -> str:
    """Render a date the way Brazilians write it: "26 de agosto de 2026".

    Django's pt-BR DATE_FORMAT is already right ("j \\d\\e F \\d\\e Y"), but its
    pt-BR catalogue capitalises month names -- "26 de Agosto de 2026" -- which
    Portuguese orthography does not. Everything else the format emits is digits
    and the connective "de", so lowercasing the rendered string corrects the
    month without hardcoding a second date format here and letting the two
    drift.
    """
    return formats.date_format(value).lower()
