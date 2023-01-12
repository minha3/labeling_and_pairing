import asyncio

import uvicorn
from fastapi import FastAPI, Response
from starlette.middleware.cors import CORSMiddleware

from config import CONFIG
from database.core import create_engine, create_tables, dispose_engine

from app.file.views import router as file_router
from app.image.views import router as image_router
from app.bbox.views import router as bbox_router
from app.label.views import router as label_router
from app.export.views import router as export_router
from app.label.utils import load_labels
from app.utils import create_directories

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://0.0.0.0:5001', 'http://localhost:5001'],
    # allow_origins=["*"],
    allow_methods=['*'],
    allow_headers=['*']
)


@app.on_event("startup")
async def startup_event():
    print('start')
    create_engine()
    await create_tables(drop=CONFIG.get('clear', False))
    create_directories(drop=CONFIG.get('clear', False))
    load_labels(dir_name=CONFIG['path']['label'])


@app.on_event("shutdown")
def shutdown_event():
    print('shutdown')
    asyncio.get_event_loop().create_task(dispose_engine())


@app.get('/ping')
def ping():
    return Response(status_code=204)


app.include_router(file_router, prefix='/files')
app.include_router(image_router, prefix='/images')
app.include_router(bbox_router, prefix='/bboxes')
app.include_router(label_router, prefix='/labels')
app.include_router(export_router, prefix='/exports')

if __name__ == '__main__':
    uvicorn.run("app.run:app", host=CONFIG['http']['host'], port=CONFIG['http']['port'])
