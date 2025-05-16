from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
import httpx

app = FastAPI()

class UrlRequest(BaseModel):
    url: HttpUrl

@app.post("/obtainrecipe")
async def obtain_recipe(request: UrlRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(str(request.url))
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            return HTMLResponse(content=response.text, status_code=200)
        except httpx.RequestError as exc:
            # For network errors, DNS failures, etc.
            return HTMLResponse(content=f"An error occurred while requesting {request.url}: {exc}", status_code=500)
        except httpx.HTTPStatusError as exc:
            # For HTTP error responses (4xx, 5xx)
            return HTMLResponse(content=f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}", status_code=exc.response.status_code)
