import json
import pandas as pd

with open("matches_details.json") as file:
    data = json.load(file)
print(len(data))

output = []
for entry in data:
    lines = entry.split("\n")

    # Remove "Recently Active" if present
    if lines[0] == "Recently Active":
        lines.pop(0)

    # Extract name and age
    name = lines[0]
    age = lines[1]

    # Extract hobbies if "Open Profile" is present
    hobbies = []
    if "Open Profile" in lines:
        open_profile_index = lines.index("Open Profile")
        hobbies = lines[open_profile_index + 1:]

    # Format the output
    output.append({
        "name": name,
        "age": age,
        "hobbies": ', '.join(hobbies)
    })


df = pd.DataFrame(output)
df.to_csv("output.csv", index=False, encoding='utf-16')
