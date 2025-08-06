from fastapi import FastAPI
from .routers import auth, upload, predict, signup, supabase_test, user
from .middlewares.auth import auth_middleware
from .middlewares.logger import log_requests

app = FastAPI()
app.middleware("http")(auth_middleware)
app.middleware("http")(log_requests)
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(predict.router)
app.include_router(signup.router)
app.include_router(supabase_test.router)
app.include_router(user.router)
