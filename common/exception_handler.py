import functools
from fastapi import HTTPException

from common.exceptions import ParameterError, ParameterNotFoundError


def exception_handler(function):
    @functools.wraps(function)
    async def wrapper_function(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except ParameterNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ParameterError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return wrapper_function
