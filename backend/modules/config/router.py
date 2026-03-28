"""modules/config/router.py — Endpoints REST per a la configuració."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.config import service
from modules.config.schemas import (
    AssetConfigCreate,
    AssetConfigOut,
    AssetConfigPatch,
    ContributionCreate,
    ContributionOut,
    ContributionPatch,
    ObjectiveOut,
    ObjectivePatch,
    ParameterOut,
    ParameterPatch,
    ScenarioPatch,
    ScenarioRow,
    WeightValidationWarning,
)

router = APIRouter(prefix="/api/v1/config", tags=["config"])

_VALID_SCENARIO_TYPES = {"adverse", "base", "optimistic"}


# ─── Assets ──────────────────────────────────────────────────────────────────

@router.get("/assets", response_model=list[AssetConfigOut])
async def list_assets(db: AsyncSession = Depends(get_db)):
    """Llista tots els assets (actius i inactius) amb la seva configuració completa."""
    return await service.list_assets(db)


@router.post("/assets", response_model=AssetConfigOut, status_code=201)
async def create_asset(data: AssetConfigCreate, db: AsyncSession = Depends(get_db)):
    """Crea un nou asset."""
    return await service.create_asset(db, data)


@router.patch("/assets/{asset_id}", response_model=AssetConfigOut)
async def patch_asset(asset_id: int, data: AssetConfigPatch, db: AsyncSession = Depends(get_db)):
    """
    Actualitza parcialment un asset.
    Camps editables: display_name, ticker_yf, ticker_mw, isin, color_hex,
                     target_weight, is_active, sort_order.
    """
    result = await service.patch_asset(db, asset_id, data)
    if result is None:
        raise HTTPException(404, f"Asset {asset_id} no trobat")
    return result


@router.get("/assets/weight-check")
async def check_weights(db: AsyncSession = Depends(get_db)):
    """Comprova si la suma dels target_weight dels assets actius és 100%."""
    total = await service.get_total_target_weight(db)
    return {
        "total_weight": total,
        "is_valid": total == 100,
        "message": (
            "Els pesos sumen exactament 100%" if total == 100
            else f"Els pesos sumen {total}% (diferència: {100 - total:+}%)"
        ),
    }


# ─── Contributions ────────────────────────────────────────────────────────────

@router.get("/contributions", response_model=list[ContributionOut])
async def list_contributions(db: AsyncSession = Depends(get_db)):
    """Llista totes les contribucions mensuals amb informació de l'asset associat."""
    return await service.list_contributions(db)


@router.post("/contributions", response_model=ContributionOut, status_code=201)
async def create_contribution(data: ContributionCreate, db: AsyncSession = Depends(get_db)):
    """Crea una nova contribució mensual."""
    return await service.create_contribution(db, data)


@router.patch("/contributions/{contrib_id}", response_model=ContributionOut)
async def patch_contribution(contrib_id: int, data: ContributionPatch, db: AsyncSession = Depends(get_db)):
    """Actualitza parcialment una contribució (amount, day_of_month, is_active)."""
    result = await service.patch_contribution(db, contrib_id, data)
    if result is None:
        raise HTTPException(404, f"Contribució {contrib_id} no trobada")
    return result


@router.delete("/contributions/{contrib_id}", status_code=204)
async def delete_contribution(contrib_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina una contribució mensual."""
    deleted = await service.delete_contribution(db, contrib_id)
    if not deleted:
        raise HTTPException(404, f"Contribució {contrib_id} no trobada")


# ─── Scenarios ────────────────────────────────────────────────────────────────

@router.get("/scenarios", response_model=list[ScenarioRow])
async def list_scenarios(db: AsyncSession = Depends(get_db)):
    """Retorna la matriu de retorns esperats (assets × escenaris)."""
    return await service.list_scenarios(db)


@router.patch("/scenarios/{asset_id}/{scenario_type}", response_model=ScenarioRow)
async def patch_scenario(
    asset_id: int,
    scenario_type: str,
    data: ScenarioPatch,
    db: AsyncSession = Depends(get_db),
):
    """
    Actualitza el retorn esperat d'un asset per a un escenari concret.
    scenario_type: adverse | base | optimistic
    annual_return: en % (e.g., 7.0 per a un 7% anual)
    """
    if scenario_type not in _VALID_SCENARIO_TYPES:
        raise HTTPException(422, f"scenario_type ha de ser un de: {', '.join(_VALID_SCENARIO_TYPES)}")
    result = await service.patch_scenario(db, asset_id, scenario_type, data)
    if result is None:
        raise HTTPException(404, f"Asset {asset_id} no trobat")
    return result


# ─── Objectives ──────────────────────────────────────────────────────────────

@router.get("/objectives", response_model=list[ObjectiveOut])
async def list_objectives(db: AsyncSession = Depends(get_db)):
    """Llista els objectius financers (habitatge, fons d'emergència, etc.)."""
    return await service.list_objectives(db)


@router.patch("/objectives/{obj_id}", response_model=ObjectiveOut)
async def patch_objective(obj_id: int, data: ObjectivePatch, db: AsyncSession = Depends(get_db)):
    """Actualitza un objectiu financer (target_amount, target_date, etc.)."""
    result = await service.patch_objective(db, obj_id, data)
    if result is None:
        raise HTTPException(404, f"Objectiu {obj_id} no trobat")
    return result


# ─── Parameters ──────────────────────────────────────────────────────────────

@router.get("/parameters", response_model=list[ParameterOut])
async def list_parameters(
    category: Optional[str] = Query(default=None, description="Filtra per categoria"),
    db: AsyncSession = Depends(get_db),
):
    """Llista els paràmetres de configuració editables."""
    return await service.list_parameters(db, category=category)


@router.patch("/parameters/{key}", response_model=ParameterOut)
async def patch_parameter(key: str, data: ParameterPatch, db: AsyncSession = Depends(get_db)):
    """Actualitza el valor d'un paràmetre de configuració."""
    result = await service.patch_parameter(db, key, data)
    if result is None:
        raise HTTPException(404, f"Paràmetre '{key}' no trobat o no és editable")
    return result


# ─── Reset ────────────────────────────────────────────────────────────────────

@router.post("/reset", status_code=200)
async def reset_defaults(db: AsyncSession = Depends(get_db)):
    """
    Restaura assets target_weight, escenaris, contribucions i objectius
    als valors originals del seed. Útil per a tests i recuperació.
    """
    changes = await service.reset_to_defaults(db)
    return {"ok": True, "changes": changes}
