import functools
from fastapi import HTTPException

from common.exceptions import ParameterError
from sqlalchemy.exc import IntegrityError


def exception_handler(function):
    @functools.wraps(function)
    async def wrapper_function(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except ParameterError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except IntegrityError as e:
            raise HTTPException(status_code=400, detail=str(e.orig.args[1]))

    return wrapper_function
