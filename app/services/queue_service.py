class QueueService:
    def __init__(self, redis_pool):
        """
        redis_pool is the arq Redis pool instance injected from FastAPI state.
        """
        self.redis = redis_pool

    async def enqueue_job(self, task_name: str, *args, **kwargs):
        """
        Enqueues a task into ARQ.
        """
        return await self.redis.enqueue_job(task_name, *args, **kwargs)
