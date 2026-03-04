"""
You are GitHub Copilot helping me create a small Python CLI tool called "What's in My Fridge".

I want a SINGLE Python script that does the following:

- Reads a CSV file called 'fridge_items.csv' in the same directory, with columns: ingredient, quantity, notes.
- Asks the user two questions in the terminal:
  1) "How many minutes do you have to cook?" and parse it as an integer.
  2) "What kind of meal are you in the mood for? (e.g., comfort, healthy, quick, cheap)" and read it as a string.

- Builds a prompt string for an LLM with:
  - A formatted list of available ingredients (name, quantity, notes).
  - The time_available and mood.
  - Clear instructions to propose 2-3 recipes, and to return ONLY a JSON object with this structure:

    {
      "recipes": [
        {
          "name": "string",
          "description": "string",
          "estimated_time_minutes": int,
          "uses_ingredients": ["ingredient name", ...],
          "missing_ingredients": [
            {"name": "string", "quantity": "string", "section": "produce|dairy|pantry|frozen"}
          ],
          "steps": ["step 1", "step 2", ...]
        }
      ],
      "top_up_grocery_list": [
        {"name": "string", "quantity": "string", "section": "produce|dairy|pantry|frozen"}
      ]
    }

- Uses the OpenAI Python client (from openai import OpenAI) and an environment variable OPENAI_API_KEY to call a modern model.
- Parses the JSON safely (using json.loads, with basic error-handling).
- Prints to the terminal:
  - Each recipe: name, estimated time, description, list of ingredients used, and steps.
  - A consolidated top-up grocery list grouped by section (produce, dairy, pantry, frozen), with ingredients alphabetically sorted within each section.

Implementation details:
- Organize the code into small functions: load_fridge_items, build_prompt, call_llm, print_recipes, print_top_up_list, main.
- Include a 'if __name__ == "__main__": main()' block.
- Add minimal but clear error handling (e.g., handle missing CSV file, JSON parsing issues).
- Use type hints where obvious.

Now generate the full Python script that satisfies these requirements.
"""


from openai import OpenAI
import csv
import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

def load_fridge_items(filename: str) -> List[Dict[str, str]]:
    try:
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return []
def build_prompt(ingredients: List[Dict[str, str]], time_available: int, mood: str) -> str:
    ingredient_list = "\n".join([f"- {item['ingredient']} (quantity: {item['quantity']}, notes: {item['notes']})" for item in ingredients])
    prompt = f"""You are a helpful cooking assistant. Based on the following available ingredients in the fridge:
{ingredient_list}
The user has {time_available} minutes to cook and is in the mood for a {mood} meal.
Please propose 2-3 recipes that can be made with the available ingredients. For each recipe, provide the name, a brief description, estimated cooking time in minutes, a list of ingredients used, a list of any missing ingredients (with name, quantity, and section), and step-by-step instructions.
Return ONLY a JSON object with the following structure:
{{
  "recipes": [
    {{
      "name": "string",
      "description": "string",
      "estimated_time_minutes": int,
      "uses_ingredients": ["ingredient name", ...],
      "missing_ingredients": [
        {{"name": "string", "quantity": "string", "section": "produce|dairy|pantry|frozen"}}
      ],
      "steps": ["step 1", "step 2", ...]
    }}
  ],
  "top_up_grocery_list": [
    {{"name": "string", "quantity": "string", "section": "produce|dairy|pantry|frozen"}}
  ]
}}"""
    return prompt
def call_llm(prompt: str) -> Dict[str, Any]:
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON response from the LLM.")
        return {}
def print_recipes(recipes: List[Dict[str, Any]]) -> None:
    for recipe in recipes:
        print(f"Recipe: {recipe['name']}")
        print(f"Estimated Time: {recipe['estimated_time_minutes']} minutes")
        print(f"Description: {recipe['description']}")
        print("Ingredients Used:")
        for ingredient in recipe['uses_ingredients']:
            print(f"  - {ingredient}")
        print("Steps:")
        for idx, step in enumerate(recipe['steps'], 1):
            print(f"  Step {idx}: {step}")
        print("\n")
def print_top_up_list(top_up_list: List[Dict[str, str]]) -> None:
    sections = {"produce": [], "dairy": [], "pantry": [], "frozen": []}
    for item in top_up_list:
        sections[item['section']].append(item)
    for section in sections:
        print(f"{section.capitalize()}:")
        for item in sorted(sections[section], key=lambda x: x['name']):
            print(f"  - {item['name']} (quantity: {item['quantity']})")
def main() -> None:
    fridge_items = load_fridge_items('fridge-items.csv')
    if not fridge_items:
        return
    try:
        time_available = int(input("How many minutes do you have to cook? "))
    except ValueError:
        print("Error: Please enter a valid integer for time.")
        return
    mood = input("What kind of meal are you in the mood for? (e.g., comfort, healthy, quick, cheap) ")
    prompt = build_prompt(fridge_items, time_available, mood)
    llm_response = call_llm(prompt)
    if not llm_response:
        return
    print_recipes(llm_response.get('recipes', []))
    print_top_up_list(llm_response.get('top_up_grocery_list', []))
if __name__ == "__main__":
    main()