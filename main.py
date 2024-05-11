import logging
import time

from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader

from src import config
from src.dentalstall import DentalStall
from src.storage import JsonFileStorage

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
app = FastAPI()
api_token = "Token 82b1fdedf74cc3a8bee3634baf664914cf856ff7" # hard coded static token for /scrap
api_auth_header = APIKeyHeader(name="Authorization")

def authenticate_token(token: str = Depends(api_auth_header)):
    if token != api_token:
        raise HTTPException(status_code=401, detail="Invalid Auth token!")
    return token


def start_scraping() -> None:
    dentalstall = DentalStall()
    storage = JsonFileStorage("resources/products.json")

    # parse pages in multiple threads to make
    # scraping faster
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [executor.submit(dentalstall.parse_page, n+1) for n in range(config.N_PAGES)]

        retires = {}
        for n, task in enumerate(as_completed(tasks)):
            if task.exception():
                time.sleep(5)
                logging.info(f"Retrying for page {n}...")
                retires[executor.submit(dentalstall.parse_page, n+1)] = n+1

        for task in as_completed(retires):
            if task.exception():
                logging.error(f"Failed page {retires[task]}. Not trying again.")

    if dentalstall.parsed_products == 0: return

    dentalstall.save(storage)
    dentalstall.notify()


@app.get("/status")
def status():
    return {"status": 200, "message": "It is running!", "data": {}}


@app.get("/scrap")
def scrap(background_tasks: BackgroundTasks, token: str = Depends(authenticate_token)):
    background_tasks.add_task(start_scraping)
    return {"status": 200, "message": "started scraping in background!", "data": {}}
