import ipaddress
import logging
import socket
from typing import Tuple, List, Dict, Any
from urllib.parse import urlparse

from app.domain.models.job import Job
from app.domain.models.user import User
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.user_repository import UserRepository
from app.services.queue_service import QueueService

logger = logging.getLogger(__name__)

BLOCKED_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

class JobService:
    def __init__(self, job_repo: JobRepository, user_repo: UserRepository, queue_service: QueueService):
        self.job_repo = job_repo
        self.user_repo = user_repo
        self.queue_service = queue_service

    def validate_url(self, url: str) -> str:
        parsed = urlparse(str(url))

        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only HTTP and HTTPS are allowed.")

        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URL must contain a valid hostname.")

        blocked_hostnames = {"localhost", "0.0.0.0", "metadata.google.internal"}
        if hostname.lower() in blocked_hostnames:
            raise ValueError(f"URL hostname '{hostname}' is not allowed.")

        try:
            resolved_ips = socket.getaddrinfo(hostname, None)
            for _, _, _, _, sockaddr in resolved_ips:
                ip = ipaddress.ip_address(sockaddr[0])
                for blocked in BLOCKED_RANGES:
                    if ip in blocked:
                        raise ValueError("URL resolves to a blocked IP range.")
        except socket.gaierror:
            raise ValueError(f"Could not resolve hostname: {hostname}")

        if len(str(url)) > 2048:
            raise ValueError("URL is too long (max 2048 characters).")

        return str(url)

    async def create_job(self, url: str, current_user: User) -> Job:
        if current_user.credits <= 0:
            raise ValueError("INSUFFICIENT_CREDITS")

        existing = self.job_repo.get_recent_duplicate(current_user.id, str(url), minutes=10)
        if existing:
            raise ValueError(f"A job for this URL is already in progress (job {existing.id})")

        safe_url = self.validate_url(url)
        parsed = urlparse(safe_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        job = Job(
            source_url=safe_url,
            base_url=base_url,
            user_id=current_user.id
        )
        job = self.job_repo.add(job)

        current_user.credits -= 1
        self.user_repo.update(current_user)

        await self.queue_service.enqueue_job("execute_pipeline", job.id)

        return job

    def get_jobs(self, user: User, page: int, per_page: int) -> Dict[str, Any]:
        offset = (page - 1) * per_page
        jobs, total = self.job_repo.get_user_jobs_paginated(user.id, offset, per_page)
        
        return {
            "jobs": jobs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if total > 0 else 1,
        }

    def get_job(self, job_id: str, user: User) -> Job:
        job = self.job_repo.get_user_job(job_id, user.id)
        if not job:
            raise ValueError("Job not found")
        return job