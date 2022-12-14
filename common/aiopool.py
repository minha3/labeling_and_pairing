import asyncio
from typing import Optional, Coroutine, Callable
import time


class AioTaskPool:
    def __init__(self, tasks: Optional[int] = None):
        """
        Control the maximum number of tasks can be submitted.
        :param tasks: Number of tasks. It must be at least 1. Default is 1.
        """
        if tasks is None:
            tasks = 1
        if tasks < 1:
            raise ValueError("Number of futures must be at least 1")
        self._coro_queue = asyncio.Queue()
        self._tasks = tasks
        self._stop_event = asyncio.Event()
        self._current_tasks = 0
        self._consumer = asyncio.create_task(self._consume())
        self._futures = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.wait()

    def apply(self, coro: Coroutine, callback: Optional[Callable] = None):
        if self._stop_event.is_set():
            raise RuntimeError('Pool is stopped')
        self._coro_queue.put_nowait((coro, self._done_callback(callback)))

    async def wait(self):
        try:
            self._stop_event.set()
            await self._consumer
            while self._current_tasks > 0:
                await asyncio.sleep(0.01)
            return self._futures
        finally:
            self._futures = []

    def _done_callback(self, callback: Optional[Callable]):
        def __done_callback(fut):
            self._current_tasks -= 1
            if callback is not None:
                callback(fut)
            else:
                try:
                    self._futures.append(fut.result())
                except Exception as e:
                    self._futures.append(e)
        return __done_callback

    async def _consume(self):
        while not self._stop_event.is_set() or not self._coro_queue.empty():
            if self._current_tasks >= self._tasks:
                await asyncio.sleep(0.01)
                continue
            self._current_tasks += 1
            coro, callback = await self._coro_queue.get()
            task = asyncio.create_task(coro)
            task.add_done_callback(callback)


if __name__ == '__main__':
    async def example():
        async def coro1():
            print('go sleep 1')
            await asyncio.sleep(2)
            print('awake 1')
            return 1

        async def coro2():
            print('go sleep 2')
            await asyncio.sleep(1)
            print('awake 2')
            return 2

        def done_callback(fut):
            print('done', fut.result())

        t = time.time()
        async with AioTaskPool(tasks=3) as pool:
            for i in range(10):
                pool.apply(coro1(), callback=done_callback)
                pool.apply(coro2(), callback=done_callback)
        print('Elapsed time', time.time() - t)
    asyncio.run(example())
