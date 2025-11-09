pip install google-genai

# +

import os
import json
import time
import pandas as pd
from pathlib import Path
from google import genai
from google.genai.types import GenerateContentConfig
from tqdm import tqdm
import jsonschema
# -

# -- Gemini API Config --
api_key = "AIzaSyBI2BQ8mmPBBZCTcz4IQv1qTYXQYCJ-LWQ"  # Replace with your actual key
client = genai.Client(api_key=api_key)
model_id = "gemini-2.5-flash-preview-05-20"

# --- JSON Schema for validation ---
schema = {
    "type": "object",
    "properties": {
        "product_name": {"type": "string"},
        "total_carbon_footprint": {"type": "string"},
        "emissions": {
            "type": "object",
            "properties": {
                "manufacturing_emission": {"type": "string"},
                "usage_emission": {"type": "string"},
                "transportation_emission": {"type": "string"},
                "end_of_life_emission": {"type": "string"}
            }
        },
        "assumptions": {"type": "object"}
    },
    "required": ["product_name", "total_carbon_footprint", "emissions", "assumptions"]
}

# --- Set Folder Path Containing PDFs ---
pdf_folder = "C://Users//shaha//Downloads//New product emission"
pdf_paths = [Path(pdf_folder) / f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
print(f"Found {len(pdf_paths)} PDF files to process.\n")

# -- Store results --
all_extracted_data = []

# --- Process each PDF with progress bar ---
for idx, pdf_path in enumerate(tqdm(pdf_paths, desc="Processing PDFs"), 1):
    # File size check (skip >50MB for Gemini)
    if pdf_path.stat().st_size > 50 * 1024 * 1024:
        print(f"[⚠] Skipping {pdf_path.name} (too large for Gemini)")
        continue

    if idx % 10 == 0:
        print("⏸ Taking a 5-second break after 10 files...")
        time.sleep(5)

    print(f" File Name: {pdf_path.name}")
    try:
        # Upload to Gemini
        sample_pdf = client.files.upload(file=pdf_path)

        # Prompt
        full_prompt = [
            """You are a sustainability analyst.
            From this Product Carbon Footprint (PCF) PDF report, extract and return the following in pure valid JSON format:
            {
              "product_name": "",
              "total_carbon_footprint": "",
              "emissions": {
                "manufacturing_emission": "",
                "usage_emission": "",
                "transportation_emission": "",
                "end_of_life_emission": "",
              },
              "assumptions": {
                "product_weight": "",
                "product_lifetime": "",
                "manufacturing_location": "",
                "use_location": "",
                "energy_demand_per_year": "",
                "display_size": "",
                "processor": "",
                "memory": "",
                "ssd": "",
                "other_breakdowns": ""
              }
            }
            If any field is not mentioned, return "Not mentioned". No explanation. Return ONLY the JSON object.
            """,
            sample_pdf
        ]

        # Generate content
        response = client.models.generate_content(
            model=model_id,
            contents=full_prompt,
            config=GenerateContentConfig(response_modalities=["TEXT"])
        )

        output_text = response.text.strip()
        if output_text.startswith("```json"):
            output_text = output_text[7:].rstrip("```").strip()

        # Parse JSON
        parsed = json.loads(output_text)
        parsed['pdf_name'] = pdf_path.name

        # Validate JSON schema
        jsonschema.validate(instance=parsed, schema=schema)

        all_extracted_data.append(parsed)
        

    except json.JSONDecodeError as je:
        print(f"[⚠] Failed to parse JSON from {pdf_path.name}: {je}")
        with open(f"error_{pdf_path.stem}.txt", "w") as f:
            f.write(output_text)
    except jsonschema.ValidationError as ve:
        print(f"[⚠] Schema validation failed for {pdf_path.name}: {ve}")
    except Exception as e:
        print(f"[✘] Failed to process {pdf_path.name}: {e}")
print("Finished!!!")


# --- Save results ---
if all_extracted_data:
    print("\n✅ All files processed. Saving results...")

    flattened_data = []
    for data in all_extracted_data:
        flat_record = {
            'PDF Name': data['pdf_name'],
            'Product Name': data['product_name'],
            'Total Carbon Footprint': data['total_carbon_footprint'],
            'Manufacturing Emission': data['emissions']['manufacturing_emission'],
            'Usage Emission': data['emissions']['usage_emission'],
            'Transportation Emission': data['emissions']['transportation_emission'],
            'End of Life Emission': data['emissions']['end_of_life_emission'],
            'Product Weight': data['assumptions']['product_weight'],
            'Product Lifetime': data['assumptions']['product_lifetime'],
            'Manufacturing Location': data['assumptions']['manufacturing_location'],
            'Use Location': data['assumptions']['use_location'],
            'Energy Demand Per Year': data['assumptions']['energy_demand_per_year'],
            'Display Size': data['assumptions']['display_size'],
            'Processor': data['assumptions']['processor'],
            'Memory': data['assumptions']['memory'],
            'SSD': data['assumptions']['ssd'],
            'Other Breakdowns': data['assumptions']['other_breakdowns']
        }
        flattened_data.append(flat_record)

    df = pd.DataFrame(flattened_data)
    excel_path = "pcf_extracted_data.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"📂 Excel saved to: {excel_path}")

    json_path = "pcf_extracted_data.json"
    with open(json_path, "w") as jf:
        json.dump(all_extracted_data, jf, indent=2)
    print(f"📂 JSON saved to: {json_path}")
else:
    print("⚠ No data extracted.")




