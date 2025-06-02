# --- Imports ---
from flask import Flask, render_template, request, jsonify
from data import load_Dim_data, load_data, get_currently_year, get_industries_by_year

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Fun Facts Dictionary ---
fun_facts = {
    2000: "People were afraid that computers would crash because of Y2K, but instead, The Sims and the Nokia 3310 arrived.",
    2001: "The first Shrek movie showed that even ogres have feelings—and that “All Star” by Smash Mouth will never leave your head.",
    2002: "We all thought that having a Tamagotchi was the height of adulthood.",
    2003: "“It's probably going to rain tomorrow” — the weather forecast phenomenon started on Seznam, and everyone was starting blogs on Lidé.cz.",
    2004: "Facebook was created — finally, we could snoop on classmates, and ICQ statuses were more important than homework.",
    2005: "YouTube launched, and the first video was about elephants at the zoo — this fundamentally changed the nature of the internet.",
    2006: "Everyone had Crazy Frog as their ringtone, and we all sent “chain emails” for good luck.",
    2007: "The first iPhone came out and suddenly, we could pretend to be busy just by looking at our phones.",
    2008: "We all danced to “Single Ladies” by Beyoncé, even though we didn’t know what to do with our hands.",
    2009: "FarmVille on Facebook instead of working, we were harvesting digital carrots and sending each other cows.",
    2010: "Instagram was born, and everyone started taking pictures of food, coffee, and their feet on the beach.",
    2011: "“Planking” — lying stiff as a board in the weirdest places was the sport of the year.",
    2012: "Gangnam Style — the whole world danced as if riding an invisible horse.",
    2013: "“Selfie” became the word of the year, and we all tried to find our best angle.",
    2014: "Ice Bucket Challenge — half the internet poured ice water over themselves, the other half filmed it.",
    2015: "The dress is blue and black! No, it’s white and gold!” — the internet argued about the color of a dress.",
    2016: "Pokémon GO — people left their homes and bumped into lamp posts while catching Pikachu.",
    2017: "Fidget spinners — a toy meant to help with focus, but in the end, it distracted absolutely everyone.",
    2018: "“Laurel or Yanny?” — another internet debate, this time about what we actually hear.",
    2019: "Baby Yoda (Grogu) took over the internet and became the cutest meme of the year.",
    2020: "We all baked banana bread, made sourdough, wore sweatpants, and discovered Zoom meetings and their “mute” button.",
    2021: "“Squid Game” — we were all scared of children’s games and green tracksuits.",
    2022: "People learned that “home office” means working from anywhere — including bed, the couch, or the beach (as long as the boss didn’t find out).",
    2023: "ChatGPT wrote so many essays it could earn its own diploma and still managed to reply to every message.",
    2024: "Czechs celebrated gold at the home ice hockey world championship after 14 years — people drank, hugged, and sang in the streets as if butter cost twenty crowns again.",
}

# --- Main Route: Index ---
@app.route('/', methods=['GET', 'POST'])
def index():
    Year, Gender, Age_category, Industry_sector = load_Dim_data()

    allowed_ages = ['15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64', '65+']
    Age_category = [a for a in Age_category if a in allowed_ages]

    currently = get_currently_year()
    current_year_display = "Present" if currently == 2022 else str(currently)

    allowed_ages_for_marriage = ['20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64', '65+']
    allowed_education_ages = allowed_ages_for_marriage
    allowed_child_ages = ['15-19', '20-24', '25-29', '30-34', '35-39', '40-44']

    if request.method == 'POST':
        # --- Get form data ---
        gender = request.form['gender'].lower()
        age_category = request.form['age_category']
        industry_sector = request.form['industry_sector']
        year = int(request.form['year'])

        selected_data = load_data(year, gender, age_category, industry_sector)
        current_data = load_data(currently, gender, age_category, industry_sector)

        # --- Education data fix ---
        education_keys = ["The chance you ever wore a Bc.graduation cap", "The chance you ever wore a Mgr. graduation cap"]

        if age_category not in ['15-19', '20-24', '25-29', '30-34'] and age_category in allowed_education_ages:
            selected_30_34 = load_data(year, gender, '30-34', industry_sector)
            current_30_34 = load_data(currently, gender, '30-34', industry_sector)
            for key in education_keys:
                selected_data[key] = selected_30_34.get(key, selected_data.get(key))
                current_data[key] = current_30_34.get(key, current_data.get(key))

        if age_category == '15-19':
            for key in education_keys:
                selected_data.pop(key, None)
                current_data.pop(key, None)

        # --- Children data filtering ---
        child_keys = ["The chance you had your first child in that year", "The chance you had another child in that year"]
        if gender == 'male':
            for key in child_keys:
                selected_data.pop(key, None)
                current_data.pop(key, None)
        else:
            if age_category not in allowed_child_ages:
                for key in child_keys:
                    selected_data.pop(key, None)
                    current_data.pop(key, None)

        # --- Marriage/Divorce data filtering ---
        marriage_keys = ["The chance you once said 'I do'", "The chance you've already signed divorce paper"]
        if age_category not in allowed_ages_for_marriage:
            for key in marriage_keys:
                selected_data.pop(key, None)
                current_data.pop(key, None)

        # --- Education not available before 2004 ---
        if year < 2004:
            for key in education_keys:
                selected_data.pop(key, None)
                current_data.pop(key, None)

        # --- Emoji Mapping ---
        EMOJI_MAP = {
            "How fat your paycheck would be": "💰",
            "House price to income ratio": "🏠",
            "The chance you once said 'I do'": "💍",
            "The chance you've already signed divorce paper": "💔",
            "The chance you had your first child in that year": "👶",
            "The chance you had another child in that year": "👶👶",
            "The chance you ever wore a Bc.graduation cap": "🎓Bc.",
            "The chance you ever wore a Mgr. graduation cap": "🎓Mgr.",
            "The price of 2 dcl wine": "🍷",
            "The price of 0.5 l beer": "🍺"
        }

        # --- Finance and Life Keys ---
        finance_keys = ["How fat your paycheck would be", "House price to income ratio"]
        if gender == "female":
            finance_keys.append("The price of 2 dcl wine")
        else:
            finance_keys.append("The price of 0.5 l beer")

        life_keys = [
            "The chance you ever wore a Bc.graduation cap",
            "The chance you ever wore a Mgr. graduation cap",
            "The chance you once said 'I do'",
            "The chance you've already signed divorce paper",
            "The chance you had your first child in that year",
            "The chance you had another child in that year"
        ]

        # --- Finance Data ---
        finance_data = []
        for key in finance_keys:
            finance_data.append({
                "key": key,
                "current": current_data.get(key, "N/A"),
                "selected": selected_data.get(key, "N/A"),
                "emoji": EMOJI_MAP.get(key, "❓"),
                "label": ""
            })

        # --- Life Data ---
        life_data = []
        for key in life_keys:
            if key in selected_data or key in current_data:
                life_data.append({
                    "key": key,
                    "current": current_data.get(key, "N/A"),
                    "selected": selected_data.get(key, "N/A"),
                    "emoji": EMOJI_MAP.get(key, "❓"),
                    "label": ""
                })

        fun_fact = fun_facts.get(year, "We don't have a fun fact for this year.")

        return render_template("results.html",
                               current_year=current_year_display,
                               selected_year=year,
                               life_data=life_data,
                               finance_data=finance_data,
                               fun_fact=fun_fact,
                               selected_gender=gender,
                               selected_age_category=age_category,
                               selected_industry_sector=industry_sector)

    # --- Initial GET rendering ---
    filtered_industries = get_industries_by_year(Year[0]) if Year else []
    return render_template("index.html",
                           years=Year,
                           genders=Gender,
                           ages=Age_category,
                           sectors=filtered_industries)

# --- Industries API ---
@app.route('/get-industries/<int:year>')
def get_industries(year):
    industries = get_industries_by_year(year)
    return jsonify(industries)

# --- Run App ---
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
