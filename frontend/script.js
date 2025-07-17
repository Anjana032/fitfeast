document.getElementById('recipeForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const ingredients = document.getElementById('ingredients').value.trim();
  const goal = document.getElementById('goal').value;

  const resultDiv = document.getElementById('result');
  resultDiv.innerHTML = '';

  const loadingMsg = document.createElement('p');
  loadingMsg.textContent = "Fetching recipes...";
  loadingMsg.style.textAlign = "center";
  resultDiv.appendChild(loadingMsg);

  try {
    const response = await fetch('http://127.0.0.1:5000/get-recipes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ingredients, goal })
    });

    const data = await response.json();
    resultDiv.innerHTML = '';

    // Apply shift-left only if screen is wide enough
    if (window.innerWidth > 768) {
      document.querySelector('.container').classList.add('shift-left');
    } else {
      document.querySelector('.container').classList.remove('shift-left');
    }

    resultDiv.classList.add('visible');

    const heading = document.createElement('h3');
    heading.textContent = "Recommended Recipes:";
    heading.style.marginBottom = "15px";
    heading.style.textAlign = "center";
    heading.style.gridColumn = "1 / -1";
    resultDiv.appendChild(heading);

    const uniqueRecipes = [];
    const seenTitles = new Set();

    for (const recipe of data.recipes) {
      if (!seenTitles.has(recipe.title)) {
        seenTitles.add(recipe.title);
        uniqueRecipes.push(recipe);
      }
      if (uniqueRecipes.length === 6) break;
    }

    uniqueRecipes.forEach(recipe => {
      const card = document.createElement('div');
      card.className = "recipe-card";
      card.innerHTML = `
        <img src="${recipe.image}" alt="${recipe.title}" />
        <p><strong>${recipe.title}</strong></p>
        <a href="recipe.html?id=${recipe.id}">View Recipe</a>
      `;
      resultDiv.appendChild(card);
    });

  } catch (error) {
    resultDiv.innerHTML = '';
    const errorMsg = document.createElement('p');
    errorMsg.textContent = "Something went wrong. Please try again later.";
    errorMsg.style.color = "red";
    errorMsg.style.textAlign = "center";
    resultDiv.appendChild(errorMsg);
    console.error("Error fetching recipes:", error);
  }
});

