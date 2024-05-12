# DentalStall scraping

- Settings can be changed for the app in the `.env` file of root directory of this project.
  - number of pages to parse
  - providing the proxy
- For easier setup, I have provided docker compose file. Check section 'How to Setup & Run'.
  - Download docker from [here](https://www.docker.com/)
- Scraped information of the products will get stored in JSON file at `resources/products.json`.
- Redis is being used as in-memory database for caching. It will auto start in the docker container from provided docker compose file.

## How to Setup & Run

To start the server

```bash
docker-compose up
```

Curl for the endpoint of fastapi server to start the scraping in the background:

```bash
curl --location 'http://localhost:8123/scrap' \
--header 'Authorization: Token 82b1fdedf74cc3a8bee3634baf664914cf856ff7'
```
