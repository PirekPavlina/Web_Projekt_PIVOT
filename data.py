# --- Imports ---
import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# --- Load Environment Variables ---
load_dotenv()

# --- Database Connection ---
conn_str = os.getenv("DB_CONNECTION_STRING")
if not conn_str:
    raise ValueError("DB_CONNECTION_STRING not set in the environment")

params = urllib.parse.quote_plus(conn_str)
conn_str = f'mssql+pyodbc:///?odbc_connect={params}'
engine = create_engine(conn_str, pool_pre_ping=True)

# --- Get industries by year ---
def get_industries_by_year(year):
    query = """
        SELECT DISTINCT Industry_sector
        FROM income_age_final_Czechia_all
        WHERE Year = :year
        ORDER BY Industry_sector
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"year": year}).fetchall()
        return [row[0] for row in result]

# --- Get currently available year (min year across all datasets) ---
def get_currently_year():
    queries = [
        ("income_age_final_Czechia_all", "Year"),
        ("house_price_to_income_Czechia_final ", "Year"),
        ("Marriage_final", "Year"),
        ("Divorce_final", "Year"),
        ("Maternal_dataset_final", "Year_of_birth"),
        ("price_trends_final", "Year")
    ]
    years = []
    with engine.connect() as conn:
        for table, col in queries:
            result = conn.execute(text(f"SELECT MAX({col}) FROM {table}")).scalar()
            if result is not None:
                years.append(result)
    return min(years) if years else None

# --- Load Dimension Data ---
def load_Dim_data():
    with engine.connect() as conn:
        Year = [row[0] for row in conn.execute(text("SELECT DISTINCT Year FROM Dim_Year ORDER BY Year"))]
        Gender = [row[0] for row in conn.execute(text("SELECT DISTINCT Gender FROM Dim_Gender ORDER BY Gender"))]
        Age_category = [row[0] for row in conn.execute(text("SELECT DISTINCT Age_category FROM Dim_Age_category ORDER BY Age_category"))]
        Industry_sector = [row[0] for row in conn.execute(text("SELECT DISTINCT Industry_sector FROM Dim_Industry_sector ORDER BY Industry_sector"))]
    return Year, Gender, Age_category, Industry_sector

# --- Map age category to wide groups (for income dataset) ---
def map_to_wide_age_category(age_category):
    wide_map = {
        'Less than 30 years': ['0', '1-4', '5-9', '10-14', '15-19', '20-24', '25-29'],
        'From 30 to 49 years': ['30-34', '35-39', '40-44', '45-49'],
        '50 years or over': ['50-54', '55-59', '60-64', '65+']
    }
    for wide_cat, narrow_list in wide_map.items():
        if age_category in narrow_list:
            return wide_cat
    return "Unknown"

# --- Load data for selected parameters ---
def load_data(year, gender, age_category, industry_sector):
    with engine.connect() as conn:
        # --- Internal helper for DB queries ---
        def get_value(query, params):
            result = conn.execute(text(query), params).fetchone()
            return result[0] if result else None

        wide_age_cat = map_to_wide_age_category(age_category)

        # --- Income ---
        avg_income = get_value("""
            SELECT Value_czk FROM income_age_final_Czechia_all
            WHERE Industry_sector = :industry_sector AND Year = :year AND Gender = :gender AND Age_class = :age_category
        """, {"industry_sector": industry_sector, "year": year, "gender": gender, "age_category": wide_age_cat})

        # --- House price to income ratio ---
        house_price_ratio = get_value("""
            SELECT Numbers_of_income FROM house_price_to_income_Czechia_final 
            WHERE Year = :year 
        """, {"year": year})

        # --- Marriage & Divorce ratios ---
        married_ratio = get_value("""
            SELECT Married_to_all_ratio FROM Marital_status_ratios_final 
            WHERE Year = :year AND Gender = :gender AND Age_category = :age_category 
        """, {"year": year, "gender": gender, "age_category": age_category})

        divorced_ratio = get_value("""
            SELECT Divorced_to_all_ratio FROM Marital_status_ratios_final 
            WHERE Year = :year AND Gender = :gender AND Age_category = :age_category
        """, {"year": year, "gender": gender, "age_category": age_category})

        # --- Population count for women (needed for childbirth probability) ---
        people_count_women = get_value("""
            SELECT count_of_people FROM Marital_status_final
            WHERE Year = :year AND Age_category = :age_category AND Gender = 'Female' AND Status = 'All'
        """, {"year": year, "age_category": age_category, "gender": gender})

        # --- First and multi-child births ---
        first_births = get_value("""
            SELECT COUNT(*) FROM Maternal_dataset_final
            WHERE Year_of_birth = :year AND Age_category = :age_category AND Gender = :gender AND Parity = 'First-time mother'
        """, {"year": year, "age_category": age_category, "gender": gender})

        multi_births = get_value("""
             SELECT COUNT(*) FROM Maternal_dataset_final
             WHERE Year_of_birth = :year AND Age_category = :age_category AND Gender = :gender AND Parity = 'Mother with previous children'
        """, {"year": year, "age_category": age_category, "gender": gender})

        # --- Education data ---
        education_bachelor = get_value("""
             SELECT Population_absolvents FROM Absolventi_unpivoted
             WHERE Year = :year AND Age_category = :age_category AND Gender = :gender AND Title = 'Bachelor'
        """, {"year": year, "age_category": age_category, "gender": gender})

        education_magister_2 = get_value("""
             SELECT Population_absolvents FROM Absolventi_unpivoted
             WHERE Year = :year AND Age_category = :age_category AND Gender = :gender AND Title = 'Magister_2_years'
        """, {"year": year, "age_category": age_category, "gender": gender})

        # --- Consumer prices (wine & beer) ---
        consumer_price = get_value("""
            SELECT Wine_0_2l FROM price_trends_final
            WHERE Year = :year
        """, {"year": year})

        consumer_price_1 = get_value("""
            SELECT Beer_draught_0_5l FROM price_trends_final
            WHERE Year = :year
        """, {"year": year})

        # --- Childbirth probabilities ---
        if people_count_women and people_count_women > 0:
            prob_first = round((first_births / people_count_women) * 100, 1) if first_births else 0
            prob_multi = round((multi_births / people_count_women) * 100, 1) if multi_births else 0
        else:
            prob_first = None
            prob_multi = None

        # --- Final output dictionary ---
        data = {
            "How fat your paycheck would be": f"{format(avg_income, ',.0f').replace(',', ' ')} CZK" if avg_income else "N/A",
            "House price to income ratio": f"{round(house_price_ratio,1)}" if house_price_ratio else "N/A",
            "The chance you once said 'I do'": f"{round(married_ratio,1)} %" if married_ratio else "N/A",
            "The chance you've already signed divorce paper": f"{round(divorced_ratio,1)} %" if divorced_ratio else "N/A",
            "The chance you ever wore a Bc.graduation cap": f"{round(education_bachelor,1)} %" if education_bachelor is not None else "N/A",
            "The chance you ever wore a Mgr. graduation cap": f"{round(education_magister_2,1)} %" if education_magister_2 is not None else "N/A",
        }

        # --- Gender-specific data ---
        if gender == "female":
            data["The chance you had your first child in that year"] = f"{prob_first} %" if prob_first is not None else "N/A"
            data["The chance you had another child in that year"] = f"{prob_multi} %" if prob_multi is not None else "N/A"
            data["The price of 2 dcl wine"] = f"{round(consumer_price,1)} CZK" if consumer_price is not None else "N/A"
        else:
            data["The price of 0.5 l beer"] = f"{round(consumer_price_1,1)} CZK" if consumer_price_1 is not None else "N/A"

        return data
