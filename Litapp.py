# Streamlit interface
st.title("Kategorien Klassifikator")

# Divide the page into 3 columns
col1, col2, col3 = st.columns(3)

# Codes input
col1.subheader("Codes:")
category_numbers = col1.text_area("", "1\n2\n3")

# Category names input
col2.subheader("Kategorien:")
category_names = col2.text_area("", 'Kategorie für Code 1\nKategorie für Code 2\nKategorie für Code 3')

# Search words input
col3.subheader("Suchwörter:")
search_words = col3.text_area("", 'Offene Nennungen untereinander einfügen\n...\n...\n...')

# Question template input
st.subheader("Aufgabe für die KI (Wichtig: Nur bei Bedarf verändern! {word} muss im Satz bleiben):")
question_template = st.text_area("", 'Zu welcher Kategorie oder welchen Kategorien gehören die Suchwörter? Antworte nur in Zahlen. {word}')

if st.button("Los gehts"):
    categories = [f"{num.strip()}: {name.strip()}" for num, name in zip(category_numbers.splitlines(), category_names.splitlines())]
    results = categorize_words(categories, search_words.splitlines(), question_template)
    
    # Display results
    st.subheader("Ergebnisse:")
    for word, category in results.items():
        st.write(f"{word}: {category}")
