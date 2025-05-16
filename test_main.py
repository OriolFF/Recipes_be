from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_obtain_recipe_success():
    test_url = "https://www.hellofresh.es/recipes/hamburguesa-de-carne-vegana-y-patata-66e1441e323c9f705cd02eae"
    response = client.post("/obtainrecipe", json={"url": test_url})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Basic check to see if it looks like HTML content
    print(response.text)
    assert "<html" in response.text.lower()
    assert "</html>" in response.text.lower()

def test_obtain_recipe_invalid_url_format():
    """Test with a string that is not a valid URL format."""
    response = client.post("/obtainrecipe", json={"url": "not_a_valid_url_at_all"})
    # FastAPI/Pydantic should return a 422 Unprocessable Entity for validation errors
    assert response.status_code == 422 

def test_obtain_recipe_non_existent_domain():
    """Test with a validly formatted URL that likely doesn't exist or won't resolve."""
    response = client.post("/obtainrecipe", json={"url": "http://thissitedefinitelyshouldnotexist12345.com"})
    # Expecting a 500 or specific error code based on main.py's httpx.RequestError handling
    assert response.status_code == 500 
    assert "An error occurred while requesting" in response.text

def test_obtain_recipe_http_error_page():
    """Test with a URL that returns an HTTP error (e.g., 404 Not Found)."""
    # This URL should reliably give a 404
    response = client.post("/obtainrecipe", json={"url": "https://jsonplaceholder.typicode.com/nonexistentpath"})
    assert response.status_code == 404
    assert "Error response 404 while requesting" in response.text
