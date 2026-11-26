import os
import random
import logging

from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from recipes import recipes

# Load token
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Save user ingredients
user_ingredients = {}

# Ingredient matching
INGREDIENT_SYNONYMS = {
    "egg": "eggs",
    "eggs": "eggs",
    "tomato": "tomato sauce",
    "tomato_sauce": "tomato sauce",
    "tomato sauce": "tomato sauce",
}


def normalize_ingredient(name):
    name = name.lower().strip().replace("_", " ")
    return INGREDIENT_SYNONYMS.get(name, name)


# Main menu
def main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🍳 Breakfast", callback_data="cat_breakfast"),
            InlineKeyboardButton("🍝 Lunch", callback_data="cat_lunch"),
        ],
        [
            InlineKeyboardButton("🍰 Desserts", callback_data="cat_dessert"),
            InlineKeyboardButton("🥤 Drinks", callback_data="cat_drinks"),
        ],
        [
            InlineKeyboardButton("🥗 Healthy", callback_data="cat_healthy"),
            InlineKeyboardButton("🍪 Snacks", callback_data="cat_snack"),
        ],
        [
            InlineKeyboardButton(
                "🥕 I Have Ingredients",
                callback_data="menu_ingredients",
            )
        ],
        [
            InlineKeyboardButton(
                "🎲 Surprise Me",
                callback_data="random",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
🌸 Welcome to Remy 🍳

Your cozy cooking assistant ✨

What are we making today?
        """,
        reply_markup=main_keyboard(),
    )


# Ingredient keyboard
def ingredient_keyboard(user):
    selected = user_ingredients.get(user, [])

    ingredients = [
        ("🥚 Eggs", "eggs"),
        ("🍞 Bread", "bread"),
        ("🧀 Cheese", "cheese"),
        ("🥛 Milk", "milk"),
        ("🍗 Chicken", "chicken"),
        ("🍚 Rice", "rice"),
        ("🍝 Pasta", "pasta"),
        ("🍅 Tomato", "tomato sauce"),
    ]

    keyboard = []
    row = []

    for name, value in ingredients:
        if value in selected:
            name = "✅ " + name

        row.append(
            InlineKeyboardButton(
                name,
                callback_data="ing_" + value,
            )
        )

        if len(row) == 2:
            keyboard.append(row)
            row = []

    keyboard.append(
        [
            InlineKeyboardButton(
                "🔍 Find Recipes",
                callback_data="find",
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🏠 Home",
                callback_data="main_menu",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


# Buttons
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user.id

    # Home
    if data == "main_menu":
        await query.edit_message_text(
            "🌸 Welcome back to Remy 🍳",
            reply_markup=main_keyboard(),
        )

    # Categories
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        keyboard = []

        for i, recipe in enumerate(recipes):
            if recipe["category"] == category:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            recipe["name"],
                            callback_data=f"rec_{i}",
                        )
                    ]
                )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🏠 Home",
                    callback_data="main_menu",
                )
            ]
        )

        await query.edit_message_text(
            "🍽️ Choose your recipe:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # Ingredients menu
    elif data == "menu_ingredients":
        if user not in user_ingredients:
            user_ingredients[user] = []

        await query.edit_message_text(
            "🥕 Choose your ingredients:",
            reply_markup=ingredient_keyboard(user),
        )

    # Add ingredients
    elif data.startswith("ing_"):
        ingredient = data.replace("ing_", "")

        if ingredient in user_ingredients[user]:
            user_ingredients[user].remove(ingredient)
        else:
            user_ingredients[user].append(ingredient)

        await query.edit_message_reply_markup(
            reply_markup=ingredient_keyboard(user)
        )

    # Find recipes
    elif data == "find":
        selected = user_ingredients.get(user, [])
        matches = []

        for i, recipe in enumerate(recipes):
            for ingredient in recipe["ingredients"]:
                if normalize_ingredient(ingredient) in selected:
                    matches.append((i, recipe))
                    break

        keyboard = []

        for i, recipe in matches:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        recipe["name"],
                        callback_data=f"rec_{i}",
                    )
                ]
            )

        if keyboard:
            await query.edit_message_text(
                "✨ I found these recipes:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await query.edit_message_text(
                "😢 No matches yet. Try more ingredients!"
            )

    # Recipe page
    elif data.startswith("rec_"):
        index = int(data.replace("rec_", ""))
        recipe = recipes[index]

        text = f"""
✨ {recipe['name']}

⏱️ Time:
{recipe['time']}

🛒 Ingredients:
"""

        for item in recipe["ingredients"]:
            text += f"• {item}\n"

        text += f"""

👩‍🍳 Steps:
{recipe['steps']}

💡 Tip:
{recipe['tip']}
"""

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="main_menu",
                        )
                    ]
                ]
            ),
        )

    # Surprise
    elif data == "random":
        recipe = random.choice(recipes)

        text = f"""
🎲 Surprise Recipe ✨

🍽️ {recipe['name']}

⏱️ {recipe['time']}

🛒 Ingredients:
"""

        for item in recipe["ingredients"]:
            text += f"• {item}\n"

        text += f"""

👩‍🍳 Steps:
{recipe['steps']}

💡 Tip:
{recipe['tip']}
"""

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏠 Home",
                            callback_data="main_menu",
                        )
                    ]
                ]
            ),
        )


# Run
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))

print("🌸 Remy is running!")

app.run_polling()
