from concurrent.futures import ThreadPoolExecutor

from fastapi import BackgroundTasks
from fastapi import FastAPI

from src import config
from src.dentalstall import DentalStall
from src.storage import JsonFileStorage


dentalstall = DentalStall()
storage = JsonFileStorage("resources/products.json")
app = FastAPI()


def start_scraping():
    with ThreadPoolExecutor(max_workers=4) as executor:
        for n in range(1, config.N_PAGES+1):
            executor.submit(dentalstall.parse_page, n,)
    dentalstall.save(storage)

    print(dentalstall.products.__len__())
    print(dentalstall.products.keys())



@app.get("/status")
def status():
    return {"status": "It is running!"}


@app.get("/scrap")
def scrap(background_tasks: BackgroundTasks):
    background_tasks.add_task(start_scraping)
    return {"status": 200, "message": "started scraping!", "data": {}}
