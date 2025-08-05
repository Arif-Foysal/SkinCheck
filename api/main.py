from fastapi import FastAPI
from .routers import auth, upload, predict, signup
from .routers import supabase_test
app = FastAPI()

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(predict.router)
app.include_router(signup.router)
app.include_router(supabase_test.router)

