document.addEventListener('DOMContentLoaded', () => {
    const recipesContainer = document.getElementById('recipes-container');
    const loadingIndicator = document.getElementById('loading');
    const BASE_API_URL = 'http://127.0.0.1:8000'; // Backend API base URL

    // Auth Section Elements
    const authSection = document.getElementById('auth-section');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const loginEmailInput = document.getElementById('loginEmail');
    const loginPasswordInput = document.getElementById('loginPassword');
    const registerEmailInput = document.getElementById('registerEmail');
    const registerPasswordInput = document.getElementById('registerPassword');
    const authStatus = document.getElementById('authStatus');
    const showRegisterFormLink = document.getElementById('showRegisterFormLink');
    const showLoginFormLink = document.getElementById('showLoginFormLink');

    // User Controls & App Content
    const userControls = document.getElementById('user-controls');
    const userInfoDisplay = document.getElementById('userInfo');
    const logoutButton = document.getElementById('logoutButton');
    const appContent = document.getElementById('app-content');

    // 'Add Recipe from URL' Form Elements
    const addRecipeForm = document.getElementById('addRecipeForm');
    const newRecipeUrlInput = document.getElementById('newRecipeUrlInput');
    const addRecipeFromUrlBtn = document.getElementById('addRecipeFromUrlBtn'); // Though submit is handled by form, might be useful
    const addRecipeStatus = document.getElementById('addRecipeStatus');

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

    // --- Token Management ---
    function saveToken(token) {
        localStorage.setItem('recipe_app_token', token);
    }

    function getToken() {
        return localStorage.getItem('recipe_app_token');
    }

    function removeToken() {
        localStorage.removeItem('recipe_app_token');
    }

    function getEmailFromToken(token) {
        if (!token) return null;
        try {
            // Basic JWT decode (payload is the middle part, base64 decoded)
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.sub; // 'sub' usually holds the username/email
        } catch (e) {
            console.error('Error decoding token:', e);
            return null;
        }
    }

    // --- UI State Management ---
    function updateUIBasedOnAuthState() {
        const token = getToken();
        if (token) {
            authSection.style.display = 'none';
            appContent.style.display = 'block';
            userControls.style.display = 'flex'; // Or 'block' depending on your CSS
            const email = getEmailFromToken(token);
            userInfoDisplay.textContent = email ? `Logged in as: ${email}` : 'Logged in';
            fetchRecipes(); // Fetch recipes when logged in
        } else {
            authSection.style.display = 'block';
            appContent.style.display = 'none';
            userControls.style.display = 'none';
            userInfoDisplay.textContent = '';
            recipesContainer.innerHTML = '<p class="loading-spinner">Please log in to see recipes.</p>';
            if (loadingIndicator) loadingIndicator.style.display = 'none';
        }
    }

    // --- Event Handlers for Auth ---
    if (showRegisterFormLink) {
        showRegisterFormLink.addEventListener('click', (e) => {
            e.preventDefault();
            loginForm.style.display = 'none';
            registerForm.style.display = 'block';
            authStatus.textContent = '';
        });
    }

    if (showLoginFormLink) {
        showLoginFormLink.addEventListener('click', (e) => {
            e.preventDefault();
            registerForm.style.display = 'none';
            loginForm.style.display = 'block';
            authStatus.textContent = '';
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const email = registerEmailInput.value.trim();
            const password = registerPasswordInput.value.trim();
            authStatus.textContent = 'Registering...';
            authStatus.style.color = 'inherit';

            try {
                const response = await fetch(`${BASE_API_URL}/users/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password }),
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Registration failed');
                }
                authStatus.textContent = 'Registration successful! Please login.';
                authStatus.style.color = 'green';
                registerForm.reset();
                // Switch to login form
                registerForm.style.display = 'none';
                loginForm.style.display = 'block';
            } catch (error) {
                authStatus.textContent = `Registration error: ${error.message}`;
                authStatus.style.color = 'red';
                console.error('Registration error:', error);
            }
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const email = loginEmailInput.value.trim();
            const password = loginPasswordInput.value.trim();
            authStatus.textContent = 'Logging in...';
            authStatus.style.color = 'inherit';

            // FastAPI's OAuth2PasswordRequestForm expects form data, not JSON
            const formData = new FormData();
            formData.append('username', email); // 'username' is the field for email
            formData.append('password', password);

            try {
                const response = await fetch(`${BASE_API_URL}/token`, {
                    method: 'POST',
                    body: formData, // Send as form data
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || 'Login failed');
                }
                saveToken(data.access_token);
                authStatus.textContent = 'Login successful!';
                authStatus.style.color = 'green';
                loginForm.reset();
                updateUIBasedOnAuthState();
            } catch (error) {
                authStatus.textContent = `Login error: ${error.message}`;
                authStatus.style.color = 'red';
                console.error('Login error:', error);
            }
        });
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            removeToken();
            updateUIBasedOnAuthState();
            authStatus.textContent = 'You have been logged out.';
            authStatus.style.color = 'green';
            // Ensure login form is shown by default on logout
            loginForm.style.display = 'block'; 
            registerForm.style.display = 'none';
        });
    }

    async function fetchRecipes() {
        const token = getToken();
        if (!token) {
            updateUIBasedOnAuthState(); // Should ensure user is prompted to login
            return;
        }
        if (loadingIndicator) loadingIndicator.style.display = 'block';

        try {
            const response = await fetch(`${BASE_API_URL}/getallrecipes`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (!response.ok) {
                if (response.status === 401) {
                    console.warn('Unauthorized. Token might be invalid or expired.');
                    removeToken();
                    updateUIBasedOnAuthState();
                    authStatus.textContent = 'Session expired. Please login again.';
                    authStatus.style.color = 'red';
                    return;
                }
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

            const editButton = document.createElement('button');
            editButton.classList.add('button', 'edit-btn'); 
            editButton.textContent = 'Edit';
            editButton.addEventListener('click', () => openEditModal(recipe));
            actionsDiv.appendChild(editButton);

            const deleteButton = document.createElement('button');
            deleteButton.classList.add('button', 'delete-btn'); 
            deleteButton.textContent = 'Delete';
            deleteButton.dataset.id = recipe.id;
            deleteButton.dataset.name = encodeURIComponent(recipe.name);
            deleteButton.addEventListener('click', async () => {
                if (confirm(`Are you sure you want to delete the recipe "${recipe.name}"?`)) {
                    await deleteRecipeOnServer(recipe.id);
                }
            });
            actionsDiv.appendChild(deleteButton);

            // Add Source Link/Button if source_url exists
            if (recipe.source_url) {
                const sourceLink = document.createElement('a');
                sourceLink.href = recipe.source_url;
                sourceLink.textContent = 'Source';
                sourceLink.target = '_blank'; // Open in new tab
                sourceLink.rel = 'noopener noreferrer'; // Security best practice for target="_blank"
                sourceLink.classList.add('button', 'source-btn'); // Style as a button
                actionsDiv.appendChild(sourceLink);
            }

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

    function createRecipeCard(recipe) {
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

        const editButton = document.createElement('button');
        editButton.classList.add('button', 'edit-btn'); 
        editButton.textContent = 'Edit';
        editButton.addEventListener('click', () => openEditModal(recipe));
        actionsDiv.appendChild(editButton);

        const deleteButton = document.createElement('button');
        deleteButton.classList.add('button', 'delete-btn'); 
        deleteButton.textContent = 'Delete';
        deleteButton.dataset.id = recipe.id;
        deleteButton.dataset.name = encodeURIComponent(recipe.name);
        deleteButton.addEventListener('click', async () => {
            if (confirm(`Are you sure you want to delete the recipe "${recipe.name}"?`)) {
                await deleteRecipeOnServer(recipe.id);
            }
        });
        actionsDiv.appendChild(deleteButton);

        // Add Source Link/Button if source_url exists
        if (recipe.source_url) {
            const sourceLink = document.createElement('a');
            sourceLink.href = recipe.source_url;
            sourceLink.textContent = 'Source';
            sourceLink.target = '_blank'; // Open in new tab
            sourceLink.rel = 'noopener noreferrer'; // Security best practice for target="_blank"
            sourceLink.classList.add('button', 'source-btn'); // Style as a button
            actionsDiv.appendChild(sourceLink);
        }

        card.innerHTML = `
            ${imageHtml}
            <div class="recipe-card-content">
                <h2>${recipe.name}</h2>
                ${ingredientsHtml}
                ${instructionsHtml}
            </div>
        `;
        card.appendChild(actionsDiv); // Append the actions div to the card content or card itself
        return card;
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
                        'Authorization': `Bearer ${getToken()}`,
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
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                },
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

    // Event listener for the 'Add Recipe from URL' form
    if (addRecipeForm) {
        addRecipeForm.addEventListener('submit', async function(event) {
            event.preventDefault(); // Prevent default form submission
            const recipeUrl = newRecipeUrlInput.value.trim();

            if (!recipeUrl) {
                if (addRecipeStatus) addRecipeStatus.textContent = 'Please enter a valid URL.';
                if (addRecipeStatus) addRecipeStatus.className = 'status-message error';
                return;
            }

            if (addRecipeStatus) addRecipeStatus.textContent = 'Processing URL...';
            if (addRecipeStatus) addRecipeStatus.className = 'status-message info';
            if (addRecipeFromUrlBtn) addRecipeFromUrlBtn.disabled = true; // Disable button during processing

            try {
                const response = await fetch(`${BASE_API_URL}/obtainrecipe`, { // Changed URL here
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getToken()}`,
                        'Accept': 'application/json' // Expect a JSON response
                    },
                    body: JSON.stringify({ url: recipeUrl })
                });

                const responseData = await response.json(); // Try to parse JSON regardless of status for error messages

                console.log('Received responseData:', JSON.stringify(responseData, null, 2));

                if (response.ok) {
                    // Check if responseData itself is not null and has an id
                    if (responseData && typeof responseData.id !== 'undefined' && responseData.id !== null) { 
                        if (addRecipeStatus) addRecipeStatus.textContent = 'Recipe added successfully!';
                        if (addRecipeStatus) addRecipeStatus.className = 'status-message success';
                        if (newRecipeUrlInput) newRecipeUrlInput.value = ''; // Clear input
                        
                        // Create and prepend the new recipe card
                        // The backend should return the full recipe object, including its new ID
                        if (responseData && responseData.id) { // Ensure we have valid recipe data with an ID
                            const newCard = createRecipeCard(responseData);
                            recipesContainer.prepend(newCard); // Add to the top
                        } else {
                            // This case might mean the response was OK but data was not as expected.
                            // Or if the server returns 200 but an existing recipe (already displayed), 
                            // we might not need to re-add it, or we could highlight it.
                            // For now, let's assume new/updated recipe is returned with full data.
                            console.warn('Recipe added, but response data was not in expected format or missing ID.', responseData);
                            if (addRecipeStatus) addRecipeStatus.textContent = 'Recipe processed, but response data was unexpected.';
                            if (addRecipeStatus) addRecipeStatus.className = 'status-message warning'; 
                            // Optionally fetch all recipes again if unsure about the state
                            // fetchRecipes(); 
                        }

                    } else {
                        console.error('Recipe added, but response data was not in expected format or missing ID.', responseData);
                        if (addRecipeStatus) addRecipeStatus.textContent = 'Recipe processed, but response data was unexpected.';
                        if (addRecipeStatus) addRecipeStatus.className = 'status-message warning'; 
                        // Optionally fetch all recipes again if unsure about the state
                        // fetchRecipes(); 
                    }

                } else {
                    // Handle HTTP errors (e.g., 400, 404, 422, 500)
                    let errorMessage = `Error: ${response.status} ${response.statusText}`;
                    if (responseData && responseData.detail) {
                        // FastAPI often returns errors in { detail: "message" } or { detail: [{...}] }
                        if (Array.isArray(responseData.detail)) {
                            errorMessage += " - " + responseData.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
                        } else if (typeof responseData.detail === 'string'){
                            errorMessage += " - " + responseData.detail;
                        }
                    } else if (responseData && responseData.message) { // General message field
                        errorMessage += " - " + responseData.message;
                    }
                    if (addRecipeStatus) addRecipeStatus.textContent = errorMessage;
                    if (addRecipeStatus) addRecipeStatus.className = 'status-message error';
                    console.error('Failed to add recipe:', responseData);
                }
            } catch (error) {
                // Handle network errors or issues with the fetch call itself
                console.error('Error submitting URL:', error);
                if (addRecipeStatus) addRecipeStatus.textContent = 'Network error or cannot connect to server.';
                if (addRecipeStatus) addRecipeStatus.className = 'status-message error';
            } finally {
                if (addRecipeFromUrlBtn) addRecipeFromUrlBtn.disabled = false; // Re-enable button
            }
        });
    }

    // Initial UI setup based on auth state
    updateUIBasedOnAuthState();

    // Initial fetch of recipes is now handled by updateUIBasedOnAuthState if logged in
    // fetchRecipes(); // Remove this direct call
});
