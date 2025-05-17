document.addEventListener('DOMContentLoaded', () => {
    const recipesContainer = document.getElementById('recipes-container');
    const loadingIndicator = document.getElementById('loading');
    const API_URL = 'http://127.0.0.1:8000/getallrecipes'; // Your FastAPI backend URL

    async function fetchRecipes() {
        try {
            const response = await fetch(API_URL);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const recipes = await response.json();
            displayRecipes(recipes);
        } catch (error) {
            console.error('Error fetching recipes:', error);
            recipesContainer.innerHTML = '<p class="loading-spinner" style="color: red;">Failed to load recipes. Check console for details.</p>';
        } finally {
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
        }
    }

    function displayRecipes(recipes) {
        if (!recipes || recipes.length === 0) {
            recipesContainer.innerHTML = '<p class="loading-spinner">No recipes found.</p>';
            return;
        }

        // Clear previous content (like the loading spinner if it wasn't removed)
        recipesContainer.innerHTML = ''; 

        recipes.forEach(recipe => {
            const card = document.createElement('div');
            card.classList.add('recipe-card');
            card.dataset.recipeId = recipe.id; // Store recipe ID on the card element

            let imageHtml = '';
            if (recipe.image_url && recipe.image_url !== 'None' && recipe.image_url.toLowerCase() !== 'null') { 
                imageHtml = `<img src="${recipe.image_url}" alt="${recipe.name}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">`;
                // Add a placeholder div that will be shown if image fails to load
                imageHtml += '<div class="placeholder-image" style="height: 200px; background: #eee; display:none; align-items:center; justify-content:center; color:#aaa;">Image not available</div>';
            } else {
                imageHtml = '<div class="placeholder-image" style="height: 200px; background: #eee; display:flex; align-items:center; justify-content:center; color:#aaa;">No Image Provided</div>';
            }

            const ingredientsHtml = recipe.ingredients && recipe.ingredients.length > 0
                ? `<h3>Ingredients</h3><ul>${recipe.ingredients.map(ing => `<li>${marked.parse(ing || '')}</li>`).join('')}</ul>`
                : '<h3>Ingredients</h3><p>Not specified.</p>';

            const instructionsHtml = recipe.instructions && recipe.instructions.length > 0
                ? `<h3>Instructions</h3><ol>${recipe.instructions.map(inst => `<li>${marked.parse(inst || '')}</li>`).join('')}</ol>`
                : '<h3>Instructions</h3><p>Not specified.</p>';

            card.innerHTML = `
                ${imageHtml}
                <div class="recipe-card-content">
                    <h2>${recipe.name}</h2>
                    ${ingredientsHtml}
                    ${instructionsHtml}
                    <div class="recipe-card-actions">
                        <button class="delete-btn" data-id="${recipe.id}" data-name="${encodeURIComponent(recipe.name)}">Delete</button>
                    </div>
                </div>
            `;
            recipesContainer.appendChild(card);
        });

        // Add event listeners for delete buttons after they are created
        addDeleteButtonListeners();
    }

    function addDeleteButtonListeners() {
        const deleteButtons = document.querySelectorAll('.delete-btn');
        deleteButtons.forEach(button => {
            button.addEventListener('click', async (event) => {
                const recipeId = event.target.dataset.id;
                const recipeName = decodeURIComponent(event.target.dataset.name);
                if (confirm(`Are you sure you want to delete the recipe "${recipeName}"?`)) {
                    await deleteRecipeOnServer(recipeId);
                }
            });
        });
    }

    async function deleteRecipeOnServer(recipeId) {
        try {
            const response = await fetch(`${API_URL.replace('/getallrecipes', '/deleterecipe')}/${recipeId}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status}, Message: ${errorData.detail || 'Failed to delete'}`);
            }

            // If successful, remove the recipe card from the UI
            const cardToRemove = document.querySelector(`.recipe-card[data-recipe-id="${recipeId}"]`);
            if (cardToRemove) {
                cardToRemove.remove();
                console.log(`Recipe ID ${recipeId} deleted successfully from UI.`);
            } else {
                console.warn(`Could not find card for recipe ID ${recipeId} to remove from UI.`);
            }
            // Optionally, show a success message to the user
            // alert(`Recipe ID ${recipeId} deleted successfully.`);

        } catch (error) {
            console.error('Error deleting recipe:', error);
            alert(`Failed to delete recipe: ${error.message}`);
        }
    }

    fetchRecipes();
});
