"""Lab dataset import: list files, start an OANDA practice download, poll the job."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from sx_api import dataset_admin as admin
from sx_api.datasets import (INSTRUMENTS, MAX_BARS, TIMEFRAMES, ImportRequest, list_datasets,
                             summarize)
from sx_api.jobs import Busy
from sx_data.history import fetch_history
from sx_data.importer import ImportRefused, finalize_dataset

router = APIRouter(prefix="/lab/datasets")


@router.get("")
def datasets(request: Request) -> dict:
    folder = request.app.state.data_dir
    return {"folder": str(folder),
            "items": admin.mark_in_use(list_datasets(folder), request.app.state.protect_dirs),
            "trash": admin.list_trash(folder),
            "options": {"instruments": INSTRUMENTS, "timeframes": TIMEFRAMES,
                        "max_bars": MAX_BARS},
            "token_configured": request.app.state.token_configured}


@router.post("/oanda", status_code=202)
def start_import(req: ImportRequest, request: Request) -> dict:
    app = request.app
    if not app.state.token_configured:
        raise HTTPException(400, "OANDA_TOKEN is not set in .env (or the environment)")
    path = app.state.data_dir / req.filename
    if path.exists():
        raise HTTPException(
            409, f"{req.filename} already exists; delete it first or pick another range")
    start, end = req.bounds()

    def work() -> dict:
        with app.state.client_factory() as client:
            res = fetch_history(client, req.instrument, req.tf, start, end)
        return summarize(finalize_dataset(path, res.candles, res.provenance))

    try:
        job = app.state.jobs.start({**req.model_dump(mode="json"), "file": req.filename}, work)
    except Busy as e:
        raise HTTPException(409, str(e)) from e
    return job.view()


@router.get("/jobs/{job_id}")
def job(job_id: str, request: Request) -> dict:
    found = request.app.state.jobs.get(job_id)
    if found is None:
        raise HTTPException(404, "unknown job (the API may have restarted)")
    return found.view()


def _refuse(e: admin.AdminRefused, code: int) -> HTTPException:
    return HTTPException(code, str(e))


@router.delete("/trash/{trash_id}")
def purge_trash(trash_id: str, request: Request) -> dict:
    try:
        admin.purge(request.app.state.data_dir, trash_id)
    except admin.AdminRefused as e:
        raise _refuse(e, 404) from e
    return {"purged": trash_id}


@router.post("/trash/{trash_id}/restore")
def restore_trash(trash_id: str, request: Request) -> dict:
    try:
        return {"restored": admin.restore(request.app.state.data_dir, trash_id)}
    except admin.AdminRefused as e:
        raise _refuse(e, 409) from e


@router.delete("/{file}")
def delete_dataset(file: str, request: Request) -> dict:
    folder = request.app.state.data_dir
    row = next((r for r in list_datasets(folder) if r["file"] == file), None)
    if row is None:
        raise HTTPException(404, f"{file} is not a dataset in the data folder")
    try:
        return {"trashed": admin.move_to_trash(folder, file, row, request.app.state.protect_dirs)}
    except admin.AdminRefused as e:
        raise _refuse(e, 409) from e


__all__ = ["ImportRefused", "router"]
