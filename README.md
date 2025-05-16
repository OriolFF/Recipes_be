# Recipe Backend API

This is a backend REST API for a recipe application. It allows users to manage recipes, primarily by extracting them from URLs.

## Tech Stack

- Python
- FastAPI
- SQLAlchemy (for database interaction - planned)
- SQLite (as the database - planned)
- Pydantic-ai (for LLM-based recipe extraction - planned)
- httpx (for making HTTP requests)

## Setup and Installation

1.  **Create Conda Environment**:
    A Conda environment named `backend` with Python 3.12.7 is used for this project.
    ```bash
    conda create --name backend python=3.12.7 -y
    ```

2.  **Activate Conda Environment**:
    ```bash
    conda activate backend
    ```

3.  **Install Dependencies**:
    Navigate to the project root directory (`recipes_be`) and install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

To run the FastAPI application locally, use Uvicorn:

```bash
conda run -n backend uvicorn main:app --reload
```

The API will typically be available at `http://127.0.0.1:8000`.

## API Endpoints

### 1. Obtain Recipe from URL

This endpoint fetches the HTML content from a given URL.

-   **HTTP Method**: `POST`
-   **Path**: `/obtainrecipe`
-   **Request Body**:
    -   **Content-Type**: `application/json`
    -   **Schema**:
        ```json
        {
          "url": "string (HttpUrl)"
        }
        ```
    -   **Example**:
        ```json
        {
          "url": "https://www.example.com/your-recipe-page"
        }
        ```
-   **Success Response**:
    -   **Status Code**: `200 OK`
    -   **Content-Type**: `text/html; charset=utf-8`
    -   **Body**: The raw HTML content of the page at the provided URL.
-   **Error Responses**:
    -   **Status Code**: `422 Unprocessable Entity`
        -   **Cause**: The request body is invalid (e.g., `url` field is missing or not a valid URL format).
        -   **Body Example** (details may vary based on Pydantic's validation):
            ```json
            {
              "detail": [
                {
                  "loc": ["body", "url"],
                  "msg": "invalid or missing URL scheme",
                  "type": "value_error.url.scheme"
                }
              ]
            }
            ```
    -   **Status Code**: `500 Internal Server Error`
        -   **Cause**: An error occurred while trying to fetch the URL (e.g., network error, DNS failure, the server at the URL is down).
        -   **Content-Type**: `text/html; charset=utf-8`
        -   **Body Example**:
            ```html
            An error occurred while requesting http://thissitedefinitelyshouldnotexist12345.com: ... (specific error message)
            ```
    -   **Status Code**: Varies (e.g., `404 Not Found`, `503 Service Unavailable` - reflects the status from the target URL if an HTTP error occurs)
        -   **Cause**: The target URL returned an HTTP error (e.g., 4xx or 5xx status code).
        -   **Content-Type**: `text/html; charset=utf-8`
        -   **Body Example** (for a 404 from the target URL):
            ```html
            Error response 404 while requesting 'https://jsonplaceholder.typicode.com/nonexistentpath': ... (HTML or text from the target error page)
            ```

## Future Endpoints (Planned)

-   Endpoint to use an LLM agent to extract recipe details (ingredients, instructions, name, main image) from the fetched HTML.
-   Endpoints for CRUD operations on recipes stored in a database:
    -   `GET /recipes` - Get all recipes.
    -   `GET /recipes/{recipe_id}` - Get a specific recipe by ID.
    -   `PUT /recipes/{recipe_id}` - Update a recipe.
    -   `DELETE /recipes/{recipe_id}` - Delete a recipe.
