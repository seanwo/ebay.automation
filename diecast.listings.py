import pandas as pd
import sys
import os
import re

def load_template(template_path):
    with open(template_path, 'r', encoding='utf-8') as file:
        return file.read()

def save_output(content, output_prefix, row_id):
    filename = f"{output_prefix}{str(row_id).zfill(3)}.html"
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"✅ Generated: {filename}")

def replace_tokens(template, row):
    output = template
    for col in row.index:
        token = r"\{\{\s*" + re.escape(col) + r"\s*\}\}"

        value = ''
        if pd.notna(row[col]):
            val = row[col]
            if isinstance(val, float) and val.is_integer():
                value = str(int(val))
            else:
                value = str(val)

        output = re.sub(token, value, output)
    return output

def main():
    if len(sys.argv) != 4:
        script_name = os.path.basename(__file__)
        print(f"Usage: python {script_name} <spreadsheet.xlsx> <template.html> <product-id>")
        sys.exit(1)

    spreadsheet_file = sys.argv[1]
    template_file = sys.argv[2]
    product_id = sys.argv[3].zfill(3)
    output_prefix = "diecast.listing."

    try:
        df = pd.read_excel(spreadsheet_file)
        df['id'] = df['id'].astype(str).str.zfill(3)
        template = load_template(template_file)
    except Exception as e:
        print(f"❌ Error reading input files: {e}")
        sys.exit(1)

    row = df[df['id'] == product_id]
    if row.empty:
        print(f"❌ Product ID {product_id} not found in spreadsheet.")
        sys.exit(1)

    content = replace_tokens(template, row.iloc[0])
    save_output(content, output_prefix, product_id)

if __name__ == "__main__":
    main()