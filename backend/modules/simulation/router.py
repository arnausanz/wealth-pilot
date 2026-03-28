"""modules/simulation/router.py — Endpoints REST per a la simulació."""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.simulation import service
from modules.simulation.schemas import ProjectionResponse, ScenariosInfoResponse

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


@router.get("/scenarios", response_model=ScenariosInfoResponse)
async def get_scenarios_info(db: AsyncSession = Depends(get_db)):
    """
    Retorna els 3 escenaris (advers/base/optimista) amb el retorn ponderat
    de la cartera actual i el context de contribucions.
    """
    return await service.get_scenarios_info(db)


@router.get("/project", response_model=ProjectionResponse)
async def project(
    horizon_years: int = Query(default=10, ge=1, le=50, description="Horitzó en anys (1–50)"),
    monthly_contribution: Optional[Decimal] = Query(
        default=None,
        ge=0,
        description="Override de la contribució mensual (€). Si no s'especifica, usa les contribucions actives de la BD.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Calcula la projecció dels 3 escenaris (advers, base, optimista) per a l'horitzó indicat.

    Retorna sèries temporals mensuals per a cada escenari + mètriques clau:
    - end_value: valor final estimat
    - total_return_eur / total_return_pct: rendiment total sobre el capital invertit
    - cagr_pct: taxa de creixement anual composada
    - data_points: array de (horizon_years × 12 + 1) valors mensuals
    """
    return await service.project_all(
        db,
        horizon_years=horizon_years,
        monthly_contribution_override=monthly_contribution,
    )
