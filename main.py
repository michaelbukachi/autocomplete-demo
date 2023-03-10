from faker import Faker
from fastapi import FastAPI
from redis.client import Redis
from starlette.responses import HTMLResponse, JSONResponse

app = FastAPI()
fake = Faker()
redis = Redis("localhost", 6379, decode_responses=True)

NAMES = [f"{fake.name()}-{i}" for i in range(500)]


@app.on_event("startup")
async def startup_event():
    key = "names_list"
    pipeline = redis.pipeline(True)
    pipeline.delete(key)
    pipeline.rpush(key, *NAMES)
    pipeline.execute()
    print("Names loaded into Redis.")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("index.html") as fp:
        html_content = fp.read()
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/autocomplete", response_class=JSONResponse)
async def get_names_autocomplete_list(prefix: str = ""):
    if prefix:
        key = "names_list"
        # We have to load the autocomplete list into memory
        # since there's no way, currently, to do a
        # 'startswith' check on a redis list
        # This means that the autocomplete list should be
        # reasonably sized.
        names = redis.lrange(key, 0, -1)
        matches = []
        for name in names:
            if name.lower().startswith(prefix):
                name, pk = name.split("-")
                matches.append({"name": name, "id": pk})

        return matches

    return []
