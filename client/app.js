document.addEventListener('DOMContentLoaded', () => {
    const recipesContainer = document.getElementById('recipes-container');
    const loadingIndicator = document.getElementById('loading');
    const BASE_API_URL = 'http://127.0.0.1:8000'; // Backend API base URL

    // Edit Modal Elements
    const editRecipeModal = document.getElementById('editRecipeModal');
    const editRecipeForm = document.getElementById('editRecipeForm');
    const editRecipeIdInput = document.getElementById('editRecipeId');
    const editRecipeNameInput = document.getElementById('editRecipeName');
    // Containers for dynamic fields
    const editIngredientsContainer = document.getElementById('editIngredientsContainer');
    const editInstructionsContainer = document.getElementById('editInstructionsContainer');
    // 'Add' buttons
    const addIngredientBtn = document.getElementById('addIngredientBtn');
    const addInstructionBtn = document.getElementById('addInstructionBtn');

    async function fetchRecipes() {
        try {
            const response = await fetch(`${BASE_API_URL}/getallrecipes`);
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

        recipesContainer.innerHTML = ''; 

        recipes.forEach(recipe => {
            const card = document.createElement('div');
            card.classList.add('recipe-card');
            card.dataset.recipeId = recipe.id;

            let imageHtml = '';
            if (recipe.image_url && recipe.image_url !== 'None' && recipe.image_url.toLowerCase() !== 'null') { 
                imageHtml = `<img src="${recipe.image_url}" alt="${recipe.name}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">`;
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
            
            const actionsDiv = document.createElement('div');
            actionsDiv.classList.add('recipe-card-actions');

            const deleteButton = document.createElement('button');
            deleteButton.classList.add('delete-btn');
            deleteButton.textContent = 'Delete';
            deleteButton.dataset.id = recipe.id;
            deleteButton.dataset.name = encodeURIComponent(recipe.name);
            deleteButton.addEventListener('click', async () => {
                if (confirm(`Are you sure you want to delete the recipe "${recipe.name}"?`)) {
                    await deleteRecipeOnServer(recipe.id);
                }
            });

            const editButton = document.createElement('button');
            editButton.classList.add('edit-btn'); // Add a class for styling if needed
            editButton.textContent = 'Edit';
            editButton.addEventListener('click', () => openEditModal(recipe));
            
            actionsDiv.appendChild(editButton);
            actionsDiv.appendChild(deleteButton);

            card.innerHTML = `
                ${imageHtml}
                <div class="recipe-card-content">
                    <h2>${recipe.name}</h2>
                    ${ingredientsHtml}
                    ${instructionsHtml}
                </div>
            `;
            card.appendChild(actionsDiv); // Append the actions div to the card content or card itself
            recipesContainer.appendChild(card);
        });

        // Event listeners for delete buttons are now added inline
        // addDeleteButtonListeners(); // This function can be removed or adapted if still needed elsewhere
    }

    // This function is now globally accessible for onclick attributes in HTML
    window.closeEditModal = function() {
        if (editRecipeModal) {
            editRecipeModal.style.display = 'none';
        }
        if (editRecipeForm) {
            editRecipeForm.reset(); // Resets name and hidden ID
        }
        // Clear dynamic fields
        if (editIngredientsContainer) editIngredientsContainer.innerHTML = '';
        if (editInstructionsContainer) editInstructionsContainer.innerHTML = '';
    }

    function createDynamicInput(text = '', type = 'ingredient') {
        const inputDiv = document.createElement('div');
        inputDiv.classList.add('dynamic-input-item');

        const inputField = document.createElement('input');
        inputField.type = 'text';
        inputField.value = text;
        inputField.placeholder = type === 'ingredient' ? 'Enter ingredient' : 'Enter instruction step';
        inputField.classList.add(`edit-${type}-input`); // For later collection

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button'; // Important to prevent form submission
        removeBtn.textContent = 'Remove';
        removeBtn.classList.add('remove-item-btn');
        removeBtn.onclick = () => inputDiv.remove();

        inputDiv.appendChild(inputField);
        inputDiv.appendChild(removeBtn);
        return inputDiv;
    }

    function addIngredientInput(text = '') {
        if (editIngredientsContainer) {
            editIngredientsContainer.appendChild(createDynamicInput(text, 'ingredient'));
        }
    }

    function addInstructionInput(text = '') {
        if (editInstructionsContainer) {
            editInstructionsContainer.appendChild(createDynamicInput(text, 'instruction'));
        }
    }

    if (addIngredientBtn) {
        addIngredientBtn.addEventListener('click', () => addIngredientInput());
    }

    if (addInstructionBtn) {
        addInstructionBtn.addEventListener('click', () => addInstructionInput());
    }

    function openEditModal(recipe) {
        if (!editRecipeModal || !editRecipeIdInput || !editRecipeNameInput || !editIngredientsContainer || !editInstructionsContainer) {
            console.error('Edit modal elements not found!');
            return;
        }
        // Clear previous dynamic content
        editIngredientsContainer.innerHTML = '';
        editInstructionsContainer.innerHTML = '';

        editRecipeIdInput.value = recipe.id;
        editRecipeNameInput.value = recipe.name;

        if (recipe.ingredients && recipe.ingredients.length > 0) {
            recipe.ingredients.forEach(ing => addIngredientInput(ing || ''));
        } else {
            addIngredientInput(); // Add one empty field if none exist
        }

        if (recipe.instructions && recipe.instructions.length > 0) {
            recipe.instructions.forEach(inst => addInstructionInput(inst || ''));
        } else {
            addInstructionInput(); // Add one empty field if none exist
        }
        
        editRecipeModal.style.display = 'block';
    }

    if (editRecipeForm) {
        editRecipeForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const recipeId = editRecipeIdInput.value;
            const name = editRecipeNameInput.value.trim();
            
            const ingredients = Array.from(editIngredientsContainer.querySelectorAll('.edit-ingredient-input'))
                                     .map(input => input.value.trim())
                                     .filter(item => item);

            const instructions = Array.from(editInstructionsContainer.querySelectorAll('.edit-instruction-input'))
                                     .map(input => input.value.trim())
                                     .filter(item => item);

            if (!name) {
                alert('Recipe name cannot be empty.');
                return;
            }

            const updatePayload = {
                name: name,
                ingredients: ingredients,
                instructions: instructions
                // image_url is not editable for now
            };

            try {
                const response = await fetch(`${BASE_API_URL}/recipes/${recipeId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(updatePayload),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP error! status: ${response.status}, Message: ${errorData.detail || 'Failed to update'}`);
                }
                
                const updatedRecipe = await response.json(); // Get the updated recipe
                console.log('Recipe updated successfully:', updatedRecipe);
                closeEditModal();
                fetchRecipes(); // Refresh the list to show changes
                alert('Recipe updated successfully!');

            } catch (error) {
                console.error('Error updating recipe:', error);
                alert(`Failed to update recipe: ${error.message}`);
            }
        });
    }

    async function deleteRecipeOnServer(recipeId) {
        try {
            const response = await fetch(`${BASE_API_URL}/deleterecipe/${recipeId}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const errorData = await response.json(); // Try to get error detail
                throw new Error(`HTTP error! status: ${response.status}, Message: ${errorData.detail || 'Failed to delete'}`);
            }
            
            // No need to parse JSON for a successful DELETE if it returns no body or 204
            // For 200 with message, this is fine:
            // const result = await response.json(); 
            // console.log(result.message);

            // If successful, remove the recipe card from the UI
            const cardToRemove = document.querySelector(`.recipe-card[data-recipe-id="${recipeId}"]`);
            if (cardToRemove) {
                cardToRemove.remove();
                console.log(`Recipe ID ${recipeId} deleted successfully from UI.`);
            } else {
                console.warn(`Could not find card for recipe ID ${recipeId} to remove from UI.`);
            }
        } catch (error) {
            console.error('Error deleting recipe:', error);
            alert(`Failed to delete recipe: ${error.message}`);
        }
    }

    // Initial fetch of recipes
    fetchRecipes();
});
