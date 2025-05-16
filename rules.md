# Goal
This is a back end API for a recipe app.
It is a REST API that allows users to create, read, update, and delete recipes.
The recipes will be obtained from url of sites holding one or several recipes.

The first Endpoint will be to get a recipe from a url. So the user will send a url to the API and the API will return a recipe.

we will have endpoints for getting all the recipes, getting a recipe by id, updating a recipe and deleting a recipe.

The recipe will be stored in a database.
A llm agent will be used to extract the recipe from the url.
The recipe will have ingredients, instructions,  a name and a main image

# Tech stack
- Python
- FastAPI
- SQLAlchemy
- Sqlite3
- PydanticAI

# Indications
Use clean code
Don't add comments unless is very necessary