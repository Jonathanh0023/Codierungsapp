import streamlit as st
import openai

# Set the API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

def categorize_words(categories, search_words, question_template):
    results = {}
    category_string = ", ".join(categories)

    for word in search_words:
        question = question_template.format(word=word.strip())
        prompt = f"{category_string}. {question}"

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=50
        )

        results[word.strip()] = response.choices[0].message.content.strip()

    return results
    
# Streamlit interface
st.markdown(
    """
    <style>
        body {
    background-image: url('https://images.squarespace-cdn.com/content/v1/5daeb8b9ae72575df5d84597/1593174331745-NCCUQI5W4ODARN50SR7N/shutterstock_1511716475_freigestellt.jpg?format=2500w');
    background-position: center;
    font-family: 'Ucity', sans-serif;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    /* border: 1px solid #ccc; */
    border-radius: 25px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    background-color: rgba(255, 255, 255, 0.75);
    border-radius: 12px;
    border: 1px solid rgba(209, 213, 219, 0.3);
}

h1 {
    text-align: center;
    color: #e5007f;
    font-size: 24px;
    padding: 20px 0;
    border-bottom: 2px solid #ccc;
    margin-bottom: 20px;
}

.file-upload {
    margin-bottom: 20px;
}

label {
    display: block;
    text-align: center;
    /* margin-bottom: 0px; */
}

.codes-container {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
    /* height: 440px; */
}

.codes-input {
    width: 5%;  /* Slim width for category numbers */
    padding: 0 1%;  /* Small padding for spacing between boxes */
}

.category-names-input {  /* Separate class for category names */
    width: 40%;  /* Adjusted width for category names */
    padding: 0 1%;  /* Small padding for spacing between boxes */
}

.meanings-input {
    width: 48%;  /* Adjusted width for search words */
    padding: 0 1%;  /* Small padding for spacing between boxes */
}

.question-input {
    width: 100%;
    margin-bottom: 20px;
}


textarea {
    font-family: Ucity, sans-serif;
    width: 100%;
    height: 250px;
    border-radius: 8px;
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    background-color: rgb(255 255 255);
    border-radius: 12px;
    border: 1px solid rgba(209, 213, 219, 0.3);
    margin: auto;
}


.codes-input textarea {
    text-align: center; /* Zentriert den Text im codes-input */
}

.meanings-input textarea {
    padding-left: 10px; /* Verschiebt den Text im meanings-input etwas nach rechts */
    max-width: 98%;
}

.category-names-input textarea {
    padding-left: 10px; /* Verschiebt den Text im meanings-input etwas nach rechts */
    max-width: 98%;
}

.question-input textarea {
    width: 100%;
    height: 30px;
    border-radius: 8px;
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    background-color: rgba(255, 255, 255, 0.75);
    border-radius: 12px;
    border: 1px solid rgba(209, 213, 219, 0.3);
}

textarea:focus {
    border-color: #e5007f;
    outline: none; /* To remove the default browser outline, which sometimes appears alongside the border */
    box-shadow: 0 0 1px #e5007f; /* This adds a subtle glow around the textarea for better focus indication */
}

button {
    display: block;
    margin: 20px auto;
    padding: 10px 20px;
    background-color: #e5007f;
    color: #fff;
    border: none;
    cursor: pointer;
    font-size: 16px;
    border-radius: 25px;
}
button:hover {
    display: block;
    margin: 20px auto;
    padding: 10px 20px;
    background-color: #e5007fc9;
    color: #fff;
    border: none;
    cursor: pointer;
    font-size: 16px;
    border-radius: 25px;
}

#result {
    margin-top: 20px;
}

    </style>
    """,
    unsafe_allow_html=True
)

st.title("Kategorien Klassifikator")

# Input for categories
category_numbers = st.text_area("Codes:", placeholder="1\n2\n3")
category_names = st.text_area("Kategorien:", placeholder='Kategorie für Code 1\nKategorie für Code 2\nKategorie für Code 3')
search_words = st.text_area("Suchwörter:", placeholder='Offene Nennungen untereinander einfügen\n...\n...\n...')
question_template = st.text_area(
    "Aufgabe für die KI (Wichtig: Nur bei Bedarf verändern! {word} muss im Satz bleiben):", 
    placeholder='Zu welcher Kategorie oder welchen Kategorien gehören die Suchwörter? Antworte nur in Zahlen. {word}'
)

if st.button("Los gehts"):
    categories = [f"{num.strip()}: {name.strip()}" for num, name in zip(category_numbers.splitlines(), category_names.splitlines())]
    results = categorize_words(categories, search_words.splitlines(), question_template)
    
    # Display results
    st.subheader("Ergebnisse:")
    for word, category in results.items():
        st.write(f"{word}: {category}")
