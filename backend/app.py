from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv() 


app = Flask(__name__)
CORS(app)

API_KEY = os.getenv('SPOONACULAR_API_KEY')
USE_MOCK_DATA = False

@app.route('/')
def home():
    return 'Backend is running'

def get_mock_recipes():
    return {
        "recipes": [
            {
                "title": "Oats & Egg Scramble",
                "image": "https://spoonacular.com/recipeImages/715538-312x231.jpg",
                "url": "https://spoonacular.com/recipes/oats-egg-scramble-715538"
            },
            {
                "title": "Tomato Chickpea Salad",
                "image": "https://spoonacular.com/recipeImages/716406-312x231.jpg",
                "url": "https://spoonacular.com/recipes/tomato-chickpea-salad-716406"
            },
            {
                "title": "Protein Smoothie",
                "image": "https://spoonacular.com/recipeImages/632660-312x231.jpg",
                "url": "https://spoonacular.com/recipes/protein-smoothie-632660"
            },
            {
                "title": "Avocado Toast",
                "image": "https://spoonacular.com/recipeImages/715495-312x231.jpg",
                "url": "https://spoonacular.com/recipes/avocado-toast-715495"
            },
            {
                "title": "Grilled Chicken Bowl",
                "image": "https://spoonacular.com/recipeImages/715497-312x231.jpg",
                "url": "https://spoonacular.com/recipes/grilled-chicken-bowl-715497"
            },
            {
                "title": "Vegetable Stir Fry",
                "image": "https://spoonacular.com/recipeImages/716627-312x231.jpg",
                "url": "https://spoonacular.com/recipes/vegetable-stir-fry-716627"
            }
        ]
    }

def score_for_goal(nutrients, goal):
    protein = nutrients.get("Protein", 0)
    calories = nutrients.get("Calories", 0)
    fat = nutrients.get("Fat", 0)
    fiber = nutrients.get("Fiber", 0)

    if goal == "muscle_gain":
        return protein * 2 - fat * 0.8 + fiber * 1 + calories * 0.4
    elif goal == "weight_loss":
        return fiber * 2 + protein * 1.5 - calories * 0.8 - fat * 1.2
    elif goal == "weight_gain":
        return calories * 1.2 + protein * 1 - fiber * 0.3
    else:
        return 0

def score_basic(recipe):
    """Basic score based on how many ingredients matched and how few are missing."""
    return recipe.get("usedIngredientCount", 0) * 5 - recipe.get("missedIngredientCount", 0) * 2

@app.route('/get-recipes', methods=['POST'])
def get_recipes():
    data = request.json
    ingredients = data.get('ingredients')
    goal = data.get('goal', '').strip().lower()

    if USE_MOCK_DATA:
        return jsonify(get_mock_recipes())

    try:
        url = "https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            "ingredients": ingredients,
            "number": 20,
            "ranking": 1,  # Still minimize missing ingredients
            "ignorePantry": True,
            "apiKey": API_KEY
        }

        response = requests.get(url, params=params)
        recipes_data = response.json()

        if isinstance(recipes_data, list) and recipes_data:
            recipe_ids = [str(r['id']) for r in recipes_data]
            bulk_url = "https://api.spoonacular.com/recipes/informationBulk"
            bulk_params = {
                "ids": ','.join(recipe_ids),
                "includeNutrition": True,
                "apiKey": API_KEY
            }

            bulk_response = requests.get(bulk_url, params=bulk_params)
            bulk_data = bulk_response.json()

            if goal and goal != "none":
                # Score using fitness goal
                scored = sorted(bulk_data, key=lambda r: score_for_goal(
                    {n["name"]: n["amount"] for n in r.get("nutrition", {}).get("nutrients", [])}, goal
                ), reverse=True)
            else:
                # Score based on ingredient match
                id_to_counts = {r["id"]: {"usedIngredientCount": r["usedIngredientCount"], "missedIngredientCount": r["missedIngredientCount"]} for r in recipes_data}

                scored = sorted(bulk_data, key=lambda r: score_basic({
                    "usedIngredientCount": id_to_counts.get(r["id"], {}).get("usedIngredientCount", 0),
                    "missedIngredientCount": id_to_counts.get(r["id"], {}).get("missedIngredientCount", 0)
                }), reverse=True)

            final_recipes = [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "image": r["image"],
                    "url": r.get("sourceUrl") or f"https://spoonacular.com/recipes/{r['title'].replace(' ', '-').lower()}-{r['id']}"
                }
                for r in scored[:6]
            ]

            return jsonify({"recipes": final_recipes})

        else:
            print("No results from API. Returning fallback.")
            return jsonify(get_mock_recipes())

    except Exception as e:
        print("API exception. Using fallback. Error:", e)
        return jsonify(get_mock_recipes())
    
@app.route('/recipe-details/<int:recipe_id>')
def recipe_details(recipe_id):
    try:
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        params = {
            "includeNutrition": True,
            "apiKey": API_KEY
        }
        res = requests.get(url, params=params)
        data = res.json()

        nutrition = {nutrient['name']: f"{nutrient['amount']} {nutrient['unit']}"
                     for nutrient in data['nutrition']['nutrients']
                     if nutrient['name'] in ["Calories", "Protein", "Fat", "Carbohydrates"]}

        steps = []
        for instruction in data.get('analyzedInstructions', []):
            for step in instruction.get('steps', []):
                steps.append(step.get('step'))

        missing_ingredients = [i['name'] for i in data.get('missedIngredients', [])]

        return jsonify({
            "title": data["title"],
            "image": data["image"],
            "nutrition": nutrition,
            "sourceUrl": data.get("sourceUrl"),
            "missingIngredients": missing_ingredients,
            "steps": steps
        })
    except Exception as e:
        print("Error loading recipe details:", e)
        return jsonify({"error": "Failed to fetch recipe details"}), 500


if __name__ == '__main__':
    app.run(debug=True)
