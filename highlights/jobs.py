# In-memory store (OK for demo / single instance)
JOBS = {}

def create_job(job_id):
    JOBS[job_id] = {
        "status": "queued",
        "progress": 0,
        "error": None,
        "result": None,
    }

def update_job(job_id, status=None, progress=None, error=None, result=None):
    job = JOBS[job_id]
    if status: job["status"] = status
    if progress is not None: job["progress"] = progress
    if error: job["error"] = error
    if result: job["result"] = result

def get_job(job_id):
    return JOBS.get(job_id)
