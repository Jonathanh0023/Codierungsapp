import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz, process
from io import BytesIO

def fuzzy_page():
    # Create a layout with a "Back to Home" button in the top right
    col1, col2 = st.columns([8, 2])  # Adjusted column width for a wider button
    with col2:
        if st.button("🏠", key="fuzzy_back"):
            st.session_state.selected_app = None
            st.rerun()

    # Streamlit-App-Layout
    st.title("FuzzyWuzzy Markencodierung")

    # Textbereich für Benutzer zum Einfügen der Markencodes und -namen
    st.subheader("Füge hier den Codeplan ein")
    brands_and_codes = st.text_area("Code und Zuordnung entweder aus zwei Spalten in Excel reinkopieren oder hier durch Tabstop trennen", key="code_plan")  # Unique key for the text area

    # Verarbeiten des eingefügten Textes und Speichern in einem Wörterbuch
    brand_codes = {}
    if brands_and_codes:
        for line in brands_and_codes.split("\n"):
            parts = line.split("\t")  # Assumes tab-separated data from the table
            if len(parts) >= 2:
                code, brands = parts[0].strip(), parts[1].strip()
                # Add each brand to the dictionary, considering multiple names
                for brand in brands.split(','):
                    clean_brand = brand.strip()
                    if clean_brand:  # Ensure no empty strings are added
                        # Consider brands with multiple possible names
                        for name in clean_brand.split('/'):
                            brand_codes[name.strip().lower()] = code

    # Matching function
    def match_organizations(input_text, brand_codes):
        input_organizations = [org.strip() for org in input_text.split(',')]
        matches = []
        for org in input_organizations:
            if org:  # Skip empty strings
                # Match against each part of the brand codes using partial_ratio for better substring matching
                matched_code = process.extractOne(org.lower(), brand_codes.keys(), scorer=fuzz.partial_ratio, score_cutoff=75)
                if matched_code:
                    matches.append(brand_codes[matched_code[0]])
                else:
                    matches.append("Kein passender Code gefunden")
        return [input_text] + matches

    # Text area for users to paste the survey data
    st.subheader("Hier die offenen Nennungen einfügen")
    survey_input = st.text_area("", key="survey_input")  # Unique key for the text area

    # Button to find matches
    if st.button("Jetzt codieren"):
        if survey_input:
            # Initialize a list to hold all matches
            all_matches = []
            # Process each input line separately
            for line in survey_input.split("\n"):
                line = line.strip()
                if line:  # Ensure the input line is not empty
                    matched_line = match_organizations(line, brand_codes)
                    all_matches.append(matched_line)
            # Convert the list of matches to a dataframe
            df_matches = pd.DataFrame(all_matches)
            # Display the dataframe
            st.dataframe(df_matches)
            
            # Provide a download link for the dataframe as an Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_matches.to_excel(writer, index=False, sheet_name='Sheet1')
                # You do not need to call save on the writer since it is handled by the context manager
            output.seek(0)  # Go back to the beginning of the BytesIO stream
            
            st.download_button(label="Download als Excel", data=output,
                               file_name='matches.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
