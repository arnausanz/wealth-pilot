"""modules/simulation/router.py — Endpoints REST per a la simulació."""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.simulation import service
from modules.simulation.schemas import (
    CompareResponse,
    ProjectionResponse,
    ScenariosInfoResponse,
    SimulationCreate,
    SimulationDetailOut,
    SimulationEventCreate,
    SimulationEventOut,
    SimulationOut,
)

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


class CompareRequest(BaseModel):
    sim_ids: list[int]
    horizon_years: int = 10


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


# ─── Open Simulator endpoints ─────────────────────────────────────────────────

@router.get("/saved", response_model=list[SimulationOut])
async def list_saved(db: AsyncSession = Depends(get_db)):
    """Llista les simulacions guardades."""
    return await service.list_saved_simulations(db)


@router.post("/saved", response_model=SimulationOut, status_code=201)
async def create_saved(data: SimulationCreate, db: AsyncSession = Depends(get_db)):
    """Crea una nova simulació guardada."""
    return await service.create_simulation(db, data)


@router.get("/saved/{sim_id}", response_model=SimulationDetailOut)
async def get_saved_detail(sim_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna una simulació amb els seus events."""
    detail = await service.get_simulation_detail(db, sim_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Simulació no trobada")
    return detail


@router.delete("/saved/{sim_id}", status_code=204)
async def delete_saved(sim_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina una simulació guardada."""
    deleted = await service.delete_simulation(db, sim_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Simulació no trobada")


@router.post("/saved/{sim_id}/events", response_model=SimulationEventOut, status_code=201)
async def add_event(
    sim_id: int,
    data: SimulationEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """Afegeix un event a una simulació."""
    return await service.add_event(db, sim_id, data)


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina un event d'una simulació."""
    deleted = await service.delete_event(db, event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event no trobat")


@router.post("/compare", response_model=CompareResponse)
async def compare_simulations(
    body: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """Compara N simulacions + baseline, retorna les sèries temporals."""
    return await service.compare_simulations(db, body.sim_ids, body.horizon_years)
