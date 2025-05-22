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

    // Theme Toggle Elements
    const themeToggleBtn = document.getElementById('themeToggleBtn');

    // View Toggle Elements
    const viewToggleBtn = document.getElementById('viewToggleBtn');
    const iconGrid = viewToggleBtn ? viewToggleBtn.querySelector('.icon-grid') : null;
    const iconList = viewToggleBtn ? viewToggleBtn.querySelector('.icon-list') : null;

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
                ? `<details class="collapsible-section">
                    <summary>Ingredients</summary>
                    <ul>${recipe.ingredients.map(ing => `<li>${marked.parse(ing || '')}</li>`).join('')}</ul>
                </details>`
                : '<h3>Ingredients</h3><p>Not specified.</p>';

            const instructionsHtml = recipe.instructions && recipe.instructions.length > 0
                ? `<details class="collapsible-section">
                    <summary>Instructions</summary>
                    <div class="instructions-markdown">${marked.parse(recipe.instructions.map(inst => `- ${inst || ''}`).join('\n'))}</div>
                </details>`
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
        card.className = 'recipe-card';
        card.dataset.recipeId = recipe.id;

        // Helper to escape HTML to prevent XSS
        function escapeHtml(unsafe) {
            if (typeof unsafe !== 'string') {
                if (unsafe === null || typeof unsafe === 'undefined') return '';
                unsafe = String(unsafe);
            }
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        const ingredientsList = recipe.ingredients && recipe.ingredients.length > 0
            ? `<ul>${recipe.ingredients.map(ing => `<li>${escapeHtml(ing)}</li>`).join('')}</ul>`
            : '<p>Not specified.</p>';

        const instructionsContent = recipe.instructions_markdown 
            ? marked.parse(recipe.instructions_markdown) 
            : (recipe.instructions && recipe.instructions.length > 0 
                ? `<ol>${recipe.instructions.map(inst => `<li>${escapeHtml(inst)}</li>`).join('')}</ol>` 
                : '<p>Not specified.</p>');

        card.innerHTML = `
            <img src="${recipe.image_url || 'placeholder.jpg'}" alt="${escapeHtml(recipe.name)}" onerror="this.onerror=null;this.src='placeholder.jpg';">
            <div class="recipe-card-content">
                <h2>${escapeHtml(recipe.name)}</h2>
                ${recipe.description ? `<p class="recipe-description">${escapeHtml(recipe.description)}</p>` : ''}
                <div class="recipe-meta">
                    ${recipe.prep_time ? `<span><strong>Prep:</strong> ${escapeHtml(recipe.prep_time)}</span>` : ''}
                    ${recipe.cook_time ? `<span><strong>Cook:</strong> ${escapeHtml(recipe.cook_time)}</span>` : ''}
                    ${recipe.servings ? `<span><strong>Servings:</strong> ${escapeHtml(recipe.servings.toString())}</span>` : ''}
                </div>
                
                <details class="collapsible-section">
                    <summary>Ingredients</summary>
                    ${ingredientsList}
                </details>
                
                <details class="collapsible-section">
                    <summary>Instructions</summary>
                    <div class="instructions-markdown">${instructionsContent}</div>
                </details>
                
                ${recipe.notes ? `<p class="recipe-notes"><strong>Notes:</strong> ${escapeHtml(recipe.notes)}</p>` : ''}
                ${recipe.source_url ? `<p class="recipe-source"><a href="${recipe.source_url}" target="_blank" class="source-btn">View Source</a></p>` : ''}
            </div>
            <div class="recipe-card-actions">
                <button class="edit-btn" data-id="${recipe.id}">Edit</button>
                <button class="delete-btn" data-id="${recipe.id}">Delete</button>
            </div>
        `;

        // Event listener for edit button
        const editButton = card.querySelector('.edit-btn');
        editButton.addEventListener('click', () => openEditModal(recipe));

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
        console.log(`Attempting to delete recipe ID: ${recipeId} on server.`);
        try {
            const authToken = getToken();
            if (!authToken) {
                console.error('Delete aborted: No auth token found.');
                alert('Authentication error. Please log in again.');
                return; // Prevent fetch if no token
            }

            const response = await fetch(`${BASE_API_URL}/deleterecipe/${recipeId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Accept': 'application/json' // Good practice to specify what we accept
                },
            });

            console.log(`Delete response status for recipe ID ${recipeId}: ${response.status}`);

            if (!response.ok) { // Checks if status is 200-299
                let errorDetail = 'Failed to delete recipe.';
                try {
                    // Attempt to parse error response only if there's content
                    if (response.headers.get("content-type")?.includes("application/json")) {
                        const errorData = await response.json();
                        errorDetail = errorData.detail || JSON.stringify(errorData);
                    } else {
                        errorDetail = await response.text(); // Get raw text if not JSON
                    }
                } catch (parseError) {
                    console.warn('Could not parse error response for delete:', parseError);
                    errorDetail = `Server returned status ${response.status} but error response was not parsable.`;
                }
                throw new Error(`HTTP error! status: ${response.status}, Message: ${errorDetail}`);
            }
            
            // If response.ok, and backend sends 200 with a JSON body:
            if (response.status === 200) {
                try {
                    // Ensure content type is JSON before parsing
                    if (response.headers.get("content-type")?.includes("application/json")) {
                        const result = await response.json(); 
                        console.log('Delete success response from server:', result.message);
                    } else if (response.status !== 204) { // 204 No Content shouldn't have a body
                        console.log('Delete success (status 200), but no JSON body or unexpected content type.');
                    }
                } catch (jsonParseError) {
                    // This could be a source of unhandled error if server sends 200 with malformed JSON
                    console.error('Error parsing success response JSON for delete:', jsonParseError);
                    // For now, we'll proceed with UI removal if status was OK,
                    // but this log helps diagnose if the JSON from server is the issue.
                }
            }


            // If successful, remove the recipe card from the UI
            const cardToRemove = document.querySelector(`.recipe-card[data-recipe-id="${recipeId}"]`);
            if (cardToRemove) {
                cardToRemove.remove();
                console.log(`Recipe ID ${recipeId} deleted successfully from UI.`);
            } else {
                console.warn(`Could not find card for recipe ID ${recipeId} to remove from UI.`);
            }
        } catch (error) {
            console.error('Error in deleteRecipeOnServer:', error);
            alert(`Failed to delete recipe: ${error.message}`);
        }
    }

    // Event listener for the 'Add Recipe from URL' form
    if (addRecipeForm) {
        addRecipeForm.addEventListener('submit', async function(event) {
            console.log('%%%%% ADD RECIPE FORM SUBMITTED - FRONTEND INITIATION %%%%%');
            event.preventDefault(); // Prevent default form submission
            const recipeUrl = newRecipeUrlInput.value.trim();

            if (!recipeUrl) {
                addRecipeStatus.textContent = 'Please enter a URL.';
                addRecipeStatus.style.color = 'red';
                return;
            }

            // Disable button and set processing message
            const submitButton = addRecipeForm.querySelector('button[type="submit"]'); // More robust way to get the button
            if (submitButton) {
                submitButton.disabled = true;
            }
            addRecipeStatus.textContent = 'Processing recipe... This may take a moment.';
            addRecipeStatus.style.color = 'inherit'; // Use default text color

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
                        addRecipeStatus.textContent = 'Recipe processed successfully!';
                        addRecipeStatus.style.color = 'green';
                        newRecipeUrlInput.value = ''; // Clear input field on success
                        fetchRecipes(); // Refresh the recipe list
                    } else {
                        console.error('Recipe added, but response data was not in expected format or missing ID.', responseData);
                        addRecipeStatus.textContent = 'Recipe processed, but response data was unexpected.';
                        addRecipeStatus.style.color = 'red';
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
                    addRecipeStatus.textContent = errorMessage;
                    addRecipeStatus.style.color = 'red';
                    console.error('Failed to add recipe:', responseData);
                }
            } catch (error) {
                // Handle network errors or issues with the fetch call itself
                console.error('Error submitting URL:', error);
                addRecipeStatus.textContent = 'Network error or cannot connect to server.';
                addRecipeStatus.style.color = 'red';
            } finally {
                // Re-enable button
                if (submitButton) {
                    submitButton.disabled = false;
                }
                // Optionally clear status after a delay or keep it until next action
                // setTimeout(() => { addRecipeStatus.textContent = ''; }, 5000); 
            }
        });
    }

    // Theme Switching Functions
    function applyTheme(theme) {
        if (theme === 'dark') {
            document.body.setAttribute('data-theme', 'dark');
            themeToggleBtn.textContent = '☀️'; // Sun icon for light mode
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.removeAttribute('data-theme');
            themeToggleBtn.textContent = '🌙'; // Moon icon for dark mode
            localStorage.setItem('theme', 'light');
        }
    }

    function toggleTheme() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        if (currentTheme === 'light') {
            applyTheme('dark');
        } else {
            applyTheme('light');
        }
    }

    function applyInitialTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light'; // Default to light
        applyTheme(savedTheme);
    }

    // View Switching Functions
    function applyView(view) {
        if (!recipesContainer || !iconGrid || !iconList) return;

        if (view === 'list') {
            recipesContainer.classList.add('recipes-list-view');
            iconGrid.style.display = 'none';
            iconList.style.display = 'inline-block';
            localStorage.setItem('view_mode', 'list');
        } else { // Grid view
            recipesContainer.classList.remove('recipes-list-view');
            iconGrid.style.display = 'inline-block';
            iconList.style.display = 'none';
            localStorage.setItem('view_mode', 'grid');
        }
    }

    function toggleView() {
        const currentView = localStorage.getItem('view_mode') || 'grid';
        if (currentView === 'grid') {
            applyView('list');
        } else {
            applyView('grid');
        }
    }

    function applyInitialView() {
        const savedView = localStorage.getItem('view_mode') || 'grid'; // Default to grid
        applyView(savedView);
    }

    // Event Listeners Setup
    function setupEventListeners() {
        // Authentication Forms
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

        // Theme Toggle Button
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', toggleTheme);
        }

        // View Toggle Button
        if (viewToggleBtn) {
            viewToggleBtn.addEventListener('click', toggleView);
        }
    }

    // Initial Setup
    applyInitialTheme();
    applyInitialView();
    setupEventListeners();
    updateUIBasedOnAuthState();

    // Initial fetch of recipes is now handled by updateUIBasedOnAuthState if logged in
    // fetchRecipes(); // Remove this direct call
});
