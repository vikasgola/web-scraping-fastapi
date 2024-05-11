from concurrent.futures import ThreadPoolExecutor

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader

from src import config
from src.dentalstall import DentalStall
from src.storage import JsonFileStorage

storage = JsonFileStorage("resources/products.json")

app = FastAPI()
api_token = "Token 82b1fdedf74cc3a8bee3634baf664914cf856ff7"
api_auth_header = APIKeyHeader(name="Authorization")

def authenticate_token(token: str = Depends(api_auth_header)):
    if token != api_token:
        raise HTTPException(status_code=401, detail="Invalid Auth token!")
    return token


def start_scraping() -> None:
    dentalstall = DentalStall()
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(dentalstall.parse_page, list(range(1, config.N_PAGES+1)))
    print([r for r in results if r])
    dentalstall.save(storage)

    print(f"Parsed {dentalstall.scraped_with_image} products with image from {config.N_PAGES} pages!")
    print(f"Updated {dentalstall.updated_in_db} products in database!")


@app.get("/status")
def status():
    return {"status": 200, "message": "It is running!", "data": {}}


@app.get("/scrap")
def scrap(background_tasks: BackgroundTasks, token: str = Depends(authenticate_token)):
    background_tasks.add_task(start_scraping)
    return {"status": 200, "message": "started scraping in background!", "data": {}}
