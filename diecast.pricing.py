
import pandas as pd
import sys
import os

def score_nascar_diecast(row):
    product_id = str(row.get("id", "")).strip().lower()
    description = str(row.get("description", "")).strip()
    edition = str(row.get("edition", "")).strip().lower()
    try:
        max_qty = int(float(row.get("max", 0)))
    except:
        max_qty = sys.maxsize
    driver = str(row.get("driver", "")).strip().lower()
    special = not pd.isna(row.get("special"))
    autograph_flag = str(row.get("autographed", "false")).strip().lower() == "true"
    issue = not pd.isna(row.get("issue"))

    if max_qty < 500:
        rarity = 1.0
    elif max_qty < 1000:
        rarity = 0.8
    elif max_qty < 5000:
        rarity = 0.6
    elif max_qty < 10000:
        rarity = 0.3
    else:
        rarity = 0.0

    if "elite" in edition:
        build = 1.0
    elif "limited" in edition:
        build = 0.3
    elif "preview" in edition:
        build = 0.3
    elif "platinum" in edition:
        build = 0.3
    elif "preferred" in edition:
        build = 0.3
    elif "galaxy" in edition:
        build = 0.3
    else:
        build = 0.0

    autograph = 1.0 if autograph_flag else 0.0

    driver_scores = {
        "dale earnhardt": 1.00,
        "jeff gordon": 1.00,
        "jimmie johnson": 1.00,
        "richard petty": 1.00,
        "bobby allison": 0.95,
        "david pearson": 0.95,
        "dale earnhardt jr.": 0.95,
        "aj foyt": 0.95,
        "mark martin": 0.90,
        "tony stewart": 0.90,
        "junior johnson": 0.90,
        "bill elliott": 0.85,
        "brad keselowski": 0.85,
        "joey logano": 0.85,
        "kyle busch": 0.85,
        "darrell waltrip": 0.80,
        "terry labonte": 0.80,
        "ernie irvan": 0.75,
        "kasey kahne": 0.75,
        "ricky rudd": 0.75,
        "alex bowman": 0.70,
        "william byron": 0.70,
        "austin dillon": 0.65,
        "daniel suarez": 0.65,
        "juan pablo montoya": 0.65,
        "jeb burton": 0.60,
        "casey mears": 0.60,
        "kenny irwin": 0.60,
        "trevor bayne": 0.60,
        "ward burton": 0.60,
        "brian vickers": 0.55,
        "marcos ambrose": 0.55
    }

    driver_key = driver.lower()
    driver_relevance = 0.0  # default score
    for name, score in driver_scores.items():
        if name in driver_key:
            driver_relevance = score
            break

    special_features = 1.0 if special else 0.0
    authenticity = 1.0
    packaging = 1.0

    score = (
        rarity * 0.30 +
        build * 0.20 +
        autograph * 0.15 +
        special_features * 0.10 +
        authenticity * 0.10 +
        driver_relevance * 0.10 +
        packaging * 0.05
    )

    if issue: score = score * 0.85

    if score > 0.95:
        price = 199.99
    elif score > 0.90:
        price = 179.99
    elif score > 0.85:
        price = 159.99
    elif score > 0.80:
        price = 139.99
    elif score > 0.75:
        price = 119.99
    elif score > 0.70:
        price = 99.99
    elif score > 0.65:
        price = 89.99
    elif score > 0.60:
        price = 74.99
    elif score > 0.55:
        price = 64.99
    elif score > 0.50:
        price = 54.99
    elif score > 0.45:
        price = 49.99
    elif score > 0.40:
        price = 44.99
    elif score > 0.35:
        price = 39.99
    elif score > 0.30:
        price = 34.99
    elif score > 0.25:
        price = 29.99
    else:
        price = 24.99

    return pd.Series({
        "product_id": product_id,
        "description": description,
        "rarity": rarity,
        "build": build,
        "autograph": autograph,
        "relevance": driver_relevance,
        "special": special_features,
        "authenticity": authenticity,
        "packaging": packaging,
        "reduce": issue,
        "score": round(score, 2),
        "price": price
    })

def main():
    if len(sys.argv) != 3:
        script_name = os.path.basename(__file__)
        print(f"Usage: python {script_name} <input.xlsx> <output.xlsx>")
        sys.exit(1)

    input_spreadsheet = sys.argv[1]
    output_spreadsheet = sys.argv[2]

    df = pd.read_excel(input_spreadsheet, dtype={"id": str})
    # scored_df = df.join(df.apply(score_nascar_diecast, axis=1))
    scored_df = df.apply(score_nascar_diecast, axis=1)
    scored_df.to_excel(output_spreadsheet, index=False)
    print(f"Pricing data saved to: {output_spreadsheet}")

if __name__ == "__main__":
    main()
