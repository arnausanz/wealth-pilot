"""
modules/simulation/engine.py — Motor de projecció financera.

Fórmula de valor futur amb contribucions mensuals regulars:
  FV(n) = PV × (1 + r_m)^n  +  PMT × [(1 + r_m)^n − 1] / r_m

On:
  PV   = valor actual de la cartera d'inversió
  r_m  = retorn mensual = (1 + r_anual)^(1/12) − 1
  n    = nombre de mesos
  PMT  = contribució mensual total (suma de totes les contribucions actives)

El motor és una funció pura sense efectes secundaris: no llegeix la BD,
rep tots els inputs i retorna la sèrie temporal. Facilita tests unitaris.
"""

from decimal import Decimal


def monthly_rate(annual_return_pct: Decimal) -> Decimal:
    """Converteix retorn anual en % a taxa mensual equivalent."""
    annual = annual_return_pct / Decimal("100")
    return (1 + annual) ** (Decimal("1") / Decimal("12")) - 1


def project(
    start_value: Decimal,
    monthly_contribution: Decimal,
    annual_return_pct: Decimal,
    months: int,
) -> list[Decimal]:
    """
    Retorna la sèrie de valors mensuals de la cartera (n+1 punts, incloent el mes 0).

    Args:
      start_value:          valor inicial de la cartera (€)
      monthly_contribution: contribució mensual regular (€)
      annual_return_pct:    retorn anual esperat (%)
      months:               horitzó temporal en mesos

    Returns:
      Llista de longitud (months + 1), on l'element i és el valor al mes i.
    """
    r = monthly_rate(annual_return_pct)
    values: list[Decimal] = [start_value.quantize(Decimal("0.01"))]
    current = start_value

    for _ in range(months):
        # Creixement del valor existent + nova aportació al final del mes
        current = current * (1 + r) + monthly_contribution
        values.append(current.quantize(Decimal("0.01")))

    return values


def cagr(start_value: Decimal, end_value: Decimal, years: int) -> Decimal | None:
    """Retorna el CAGR (%) donat un valor inicial, final i nombre d'anys."""
    if start_value <= 0 or years <= 0:
        return None
    ratio = end_value / start_value
    cagr_decimal = ratio ** (Decimal("1") / Decimal(str(years))) - 1
    return (cagr_decimal * 100).quantize(Decimal("0.01"))
