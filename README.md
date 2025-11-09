Setup & Configuration

Imports necessary libraries (os, pandas, jsonschema, google.genai, etc.).

Sets the Gemini API key and model ID (gemini-2.5-flash-preview-05-20).

Defines a JSON schema that specifies required fields like product name, total carbon footprint, emissions, and assumptions.

Loading PDFs

Scans a local folder for all .pdf files.

Skips any file larger than 50 MB (Gemini limit).

Processing PDFs

Uploads each PDF to the Gemini API.

Prompts Gemini to extract specific fields such as:

product_name

total_carbon_footprint

emissions (manufacturing, usage, transport, end-of-life)

assumptions (weight, lifetime, energy demand, etc.)

Ensures the response is valid JSON, parses it, and validates it against the schema.

Error Handling

Handles failed uploads, invalid JSON, or schema mismatches.

Logs issues into text files if errors occur.

Saving Results

Converts all extracted data into a structured pandas DataFrame.

Exports results to:

pcf_extracted_data.xlsx (Excel format)

pcf_extracted_data.json (JSON format)
