"""One-at-a-time background import jobs (in memory; a restart forgets finished jobs).

The OANDA client has no progress hook, so a job reports only running / done / refused / failed
and the elapsed time. Messages are short and never contain the token.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from sx_data.errors import OandaError
from sx_data.importer import ImportRefused

log = logging.getLogger("sx_api.jobs")


@dataclass
class Job:
    id: str
    request: dict
    state: str = "running"          # running | done | refused | failed
    message: str = ""
    started: float = field(default_factory=time.monotonic)
    finished: float | None = None
    result: dict | None = None

    def view(self) -> dict:
        end = self.finished if self.finished is not None else time.monotonic()
        return {"id": self.id, "state": self.state, "message": self.message,
                "elapsed_s": round(end - self.started, 1), "request": self.request,
                "result": self.result}


class Busy(RuntimeError):
    """An import is already running."""


class JobManager:
    def __init__(self) -> None:
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sx-import")
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def start(self, request: dict, work: Callable[[], dict]) -> Job:
        with self._lock:
            if any(j.state == "running" for j in self._jobs.values()):
                raise Busy("another import is still running")
            job = Job(uuid.uuid4().hex[:12], request)
            self._jobs[job.id] = job
        self._pool.submit(self._run, job, work)
        return job

    def _run(self, job: Job, work: Callable[[], dict]) -> None:
        try:
            job.result, job.state, job.message = work(), "done", "download finished"
        except (ImportRefused, OandaError) as e:
            job.state, job.message = "refused", str(e)
        except Exception as e:  # noqa: BLE001 - last resort; the full error goes to the log
            log.exception("import job failed")
            job.state = "failed"
            job.message = f"unexpected error ({type(e).__name__}); see the API log"
        job.finished = time.monotonic()

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)
