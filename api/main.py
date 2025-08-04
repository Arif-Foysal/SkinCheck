from fastapi import FastAPI
from .routers import auth, upload, predict, signup

app = FastAPI()

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(predict.router)
app.include_router(signup.router)


