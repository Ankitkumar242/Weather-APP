"""Script to build and enrich app/data/regions/in.json with Indian states, UTs, and major cities."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any
import httpx

SEED_STATES = [
    # States
    ("Andhra Pradesh", "Amaravati", 16.5730, 80.3575, "state", ["Visakhapatnam", "Vijayawada", "Guntur", "Tirupati"]),
    ("Arunachal Pradesh", "Itanagar", 27.0844, 93.6053, "state", ["Naharlagun", "Pasighat", "Tawang", "Ziro"]),
    ("Assam", "Dispur", 26.1433, 91.7898, "state", ["Guwahati", "Silchar", "Dibrugarh", "Jorhat"]),
    ("Bihar", "Patna", 25.5941, 85.1376, "state", ["Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga"]),
    ("Chhattisgarh", "Raipur", 21.2514, 81.6296, "state", ["Bhilai", "Bilaspur", "Korba", "Durg"]),
    ("Goa", "Panaji", 15.4909, 73.8278, "state", ["Margao", "Vasco da Gama", "Mapusa", "Ponda"]),
    ("Gujarat", "Gandhinagar", 23.2156, 72.6369, "state", ["Ahmedabad", "Surat", "Vadodara", "Rajkot"]),
    ("Haryana", "Chandigarh", 30.7333, 76.7794, "state", ["Faridabad", "Gurugram", "Panipat", "Ambala"]),
    ("Himachal Pradesh", "Shimla", 31.1048, 77.1734, "state", ["Dharamshala", "Mandi", "Solan", "Kullu"]),
    ("Jharkhand", "Ranchi", 23.3441, 85.3096, "state", ["Jamshedpur", "Dhanbad", "Bokaro", "Deoghar"]),
    ("Karnataka", "Bengaluru", 12.9716, 77.5946, "state", ["Mysuru", "Hubballi", "Mangaluru", "Belagavi"]),
    ("Kerala", "Thiruvananthapuram", 8.5241, 76.9366, "state", ["Kochi", "Kozhikode", "Kollam", "Thrissur"]),
    ("Madhya Pradesh", "Bhopal", 23.2599, 77.4126, "state", ["Indore", "Jabalpur", "Gwalior", "Ujjain"]),
    ("Maharashtra", "Mumbai", 19.0760, 72.8777, "state", ["Pune", "Nagpur", "Nashik", "Aurangabad"]),
    ("Manipur", "Imphal", 24.8170, 93.9368, "state", ["Thoubal", "Bishnupur", "Churachandpur", "Ukhrul"]),
    ("Meghalaya", "Shillong", 25.5788, 91.8933, "state", ["Tura", "Jowai", "Nongpoh", "Cherrapunji"]),
    ("Mizoram", "Aizawl", 23.7271, 92.7176, "state", ["Lunglei", "Champhai", "Serchhip", "Kolasib"]),
    ("Nagaland", "Kohima", 25.6751, 94.1086, "state", ["Dimapur", "Mokokchung", "Tuensang", "Wokha"]),
    ("Odisha", "Bhubaneswar", 20.2961, 85.8245, "state", ["Cuttack", "Rourkela", "Puri", "Sambalpur"]),
    ("Punjab", "Chandigarh", 30.7333, 76.7794, "state", ["Ludhiana", "Amritsar", "Jalandhar", "Patiala"]),
    ("Rajasthan", "Jaipur", 26.9124, 75.7873, "state", ["Jodhpur", "Kota", "Bikaner", "Udaipur"]),
    ("Sikkim", "Gangtok", 27.3389, 88.6065, "state", ["Namchi", "Gyalshing", "Mangan", "Rangpo"]),
    ("Tamil Nadu", "Chennai", 13.0827, 80.2707, "state", ["Coimbatore", "Madurai", "Tiruchirappalli", "Salem"]),
    ("Telangana", "Hyderabad", 17.3850, 78.4867, "state", ["Warangal", "Nizamabad", "Karimnagar", "Khammam"]),
    ("Tripura", "Agartala", 23.8315, 91.2868, "state", ["Dharmanagar", "Udaipur", "Kailashahar", "Belonia"]),
    ("Uttar Pradesh", "Lucknow", 26.8467, 80.9462, "state", ["Kanpur", "Varanasi", "Agra", "Prayagraj"]),
    ("Uttarakhand", "Dehradun", 30.3165, 78.0322, "state", ["Haridwar", "Roorkee", "Haldwani", "Nainital"]),
    ("West Bengal", "Kolkata", 22.5726, 88.3639, "state", ["Siliguri", "Asansol", "Durgapur", "Howrah"]),
    # Union Territories
    ("Andaman & Nicobar Islands", "Port Blair", 11.6234, 92.7265, "ut", ["Diglipur", "Mayabunder"]),
    ("Chandigarh", "Chandigarh", 30.7333, 76.7794, "ut", []),
    ("Dadra & Nagar Haveli and Daman & Diu", "Daman", 20.3974, 72.8328, "ut", ["Diu", "Silvassa"]),
    ("Delhi", "New Delhi", 28.6139, 77.2090, "ut", ["North Delhi", "South Delhi"]),
    ("Jammu & Kashmir", "Srinagar", 34.0837, 74.7973, "ut", ["Jammu", "Anantnag", "Baramulla", "Udhampur"]),
    ("Ladakh", "Leh", 34.1526, 77.5771, "ut", ["Kargil", "Diskit"]),
    ("Lakshadweep", "Kavaratti", 10.5667, 72.6417, "ut", ["Agatti", "Andrott"]),
    ("Puducherry", "Puducherry", 11.9416, 79.8083, "ut", ["Karaikal", "Mahe", "Yanam"]),
]

STATE_NORMALIZE = {
    "orissa": "odisha",
    "uttaranchal": "uttarakhand",
    "pondicherry": "puducherry",
    "national capital territory of delhi": "delhi",
    "nct of delhi": "delhi",
    "andaman and nicobar islands": "andaman & nicobar islands",
    "jammu and kashmir": "jammu & kashmir",
    "dadra and nagar haveli and daman and diu": "dadra & nagar haveli and daman & diu",
}


def to_slug(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[-\s]+", "-", cleaned).strip("-")


def norm_state_str(s: str) -> str:
    low = s.strip().lower()
    return STATE_NORMALIZE.get(low, low)


def build_dataset() -> None:
    client = httpx.Client(timeout=10.0)
    data: list[dict[str, Any]] = []

    print(f"Building dataset for {len(SEED_STATES)} Indian States and UTs...")

    for state_name, capital, cap_lat, cap_lon, state_type, extra_cities in SEED_STATES:
        slug = to_slug(state_name)
        cities_list: list[dict[str, Any]] = [
            {
                "name": capital,
                "lat": round(cap_lat, 4),
                "lon": round(cap_lon, 4),
                "population": None,
                "is_capital": True,
            }
        ]

        print(f"Processing {state_name} ({state_type}). Capital: {capital}...")

        norm_state = norm_state_str(state_name)

        for c_name in extra_cities:
            if c_name.lower() == capital.lower():
                continue
            try:
                r = client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": c_name, "count": 10, "language": "en", "countryCode": "IN"},
                )
                if r.status_code == 200:
                    results = r.json().get("results", [])
                    matched = []
                    for item in results:
                        adm1 = norm_state_str(item.get("admin1", ""))
                        if adm1 and (adm1 == norm_state or norm_state in adm1 or adm1 in norm_state):
                            matched.append(item)

                    if matched:
                        # Highest population wins
                        best = max(matched, key=lambda x: x.get("population") or 0)
                        cities_list.append({
                            "name": best["name"],
                            "lat": round(float(best["latitude"]), 4),
                            "lon": round(float(best["longitude"]), 4),
                            "population": best.get("population"),
                            "is_capital": False,
                        })
                    else:
                        print(f"  [Notice] Ambiguous/unmatched admin1 for {c_name} in {state_name}. Using first Indian match if available.")
                        if results:
                            best = results[0]
                            cities_list.append({
                                "name": c_name,
                                "lat": round(float(best["latitude"]), 4),
                                "lon": round(float(best["longitude"]), 4),
                                "population": best.get("population"),
                                "is_capital": False,
                            })
                time.sleep(0.1)
            except Exception as e:
                print(f"  [Error resolving {c_name}]: {e}")

        data.append({
            "name": state_name,
            "slug": slug,
            "type": state_type,
            "capital": capital,
            "lat": round(cap_lat, 4),
            "lon": round(cap_lon, 4),
            "cities": cities_list,
        })

    os.makedirs("app/data/regions", exist_ok=True)
    out_path = "app/data/regions/in.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {out_path} with {len(data)} entries!")


if __name__ == "__main__":
    build_dataset()
