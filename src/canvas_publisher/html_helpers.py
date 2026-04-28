"""HTML helpers for Canvas content — generates proper HTML tables for rubrics."""


def rubric_to_html(criteria: list) -> str:
    """Convert rubric criteria list to an HTML table."""
    if not criteria:
        return ""
    html = '<table style="width:100%;border-collapse:collapse;margin:1rem 0;">\n'
    html += '<thead><tr style="background:#394B58;color:white;">'
    html += '<th style="padding:8px;text-align:left;">Criterio</th>'
    html += '<th style="padding:8px;text-align:center;">Peso</th>'
    html += '<th style="padding:8px;text-align:left;background:#2F855A;">Excelente</th>'
    html += '<th style="padding:8px;text-align:left;background:#2B6CB0;">Bueno</th>'
    html += '<th style="padding:8px;text-align:left;background:#C05621;">Regular</th>'
    html += '<th style="padding:8px;text-align:left;background:#C53030;">Deficiente</th>'
    html += '</tr></thead>\n<tbody>\n'
    for cr in criteria:
        if not isinstance(cr, dict):
            continue
        html += '<tr style="border-bottom:1px solid #E2E8F0;">'
        html += f'<td style="padding:8px;font-weight:bold;">{cr.get("criterion", "")}</td>'
        html += f'<td style="padding:8px;text-align:center;">{cr.get("weight", "")}</td>'
        html += f'<td style="padding:8px;background:#F0FFF4;">{cr.get("excelente", cr.get("excellent", ""))}</td>'
        html += f'<td style="padding:8px;background:#EBF8FF;">{cr.get("bueno", cr.get("good", ""))}</td>'
        html += f'<td style="padding:8px;background:#FFFFF0;">{cr.get("regular", "")}</td>'
        html += f'<td style="padding:8px;background:#FFF5F5;">{cr.get("deficiente", cr.get("deficient", ""))}</td>'
        html += '</tr>\n'
    html += '</tbody></table>'
    return html


def schedule_to_html(sequence: list) -> str:
    """Convert session sequence to an HTML table."""
    if not sequence:
        return ""
    html = '<table style="width:100%;border-collapse:collapse;margin:0.5rem 0;">\n'
    html += '<thead><tr style="background:#EDF2F7;"><th style="padding:6px;">Tiempo</th><th style="padding:6px;">Actividad</th></tr></thead>\n<tbody>\n'
    for step in sequence:
        if isinstance(step, dict):
            html += f'<tr><td style="padding:6px;font-weight:bold;width:100px;">{step.get("time", "")}</td>'
            html += f'<td style="padding:6px;">{step.get("activity", "")}</td></tr>\n'
    html += '</tbody></table>'
    return html
