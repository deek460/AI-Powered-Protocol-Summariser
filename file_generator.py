from docx import Document
import re
import json
from storage import upload_file

# ✅ Load final_summaries from JSON instead of .ipynb
with open("final_summaries.json", "r") as f:
    data = json.load(f)

# Clean text function
def clean_text(text):
    text = text.replace('\xa0', ' ')
    text = text.replace('\n', ' ').replace('\r', ' ')
    return re.sub(r'\s+', ' ', text).strip().lower()

# Normalize the keys
cleaned_data = {clean_text(k): v for k, v in data.items()}

# Load document template
doc = Document("Summary.docx")

# Fill the table fields
for table in doc.tables:
    for row in table.rows:
        if len(row.cells) < 2:
            continue

        key_cell = row.cells[0]
        value_cell = row.cells[1]

        raw_key = key_cell.text
        normalized_key = clean_text(raw_key)

        for data_key, fill_value in cleaned_data.items():
            if data_key in normalized_key:
                value_cell.text = fill_value
                break

# Save output
doc.save("Filled_Summary.docx")

upload_file("Filled_Summary.docx", "OutputFile", "final-output")
print("🎉 All done! Saved as 'Filled_Summary.docx'")
