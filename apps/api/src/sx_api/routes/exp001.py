"""GET /lab/exp001: the stored EXP-001 results, unchanged apart from a field whitelist."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from sx_api.exp001 import load_exp001

router = APIRouter(prefix="/lab")


@router.get("/exp001")
def exp001(request: Request) -> dict:
    folder = request.app.state.data_dir.parent / "exp001"
    try:
        return load_exp001(folder)
    except ValueError as e:
        raise HTTPException(500, str(e)) from e
