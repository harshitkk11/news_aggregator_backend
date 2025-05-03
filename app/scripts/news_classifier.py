import json
from transformers import pipeline

# Load models
classifier = pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")
summarizer = pipeline("summarization")

# Load NER model
ner_model = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", aggregation_strategy="simple")

# Load dummy news
with open('../news_data.json', 'r') as file:
    news_data = json.load(file)

# Process each article
for data in news_data:
    title = data['title']
    description = data['description']

    sentiment = classifier(title)[0]

    # Summarize only if description is long enough
    if len(description.split()) < 30:
        summary = description
    else:
        # Increase max_length to be greater than min_length
        summary = summarizer(description, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
    entities = ner_model(description)

    persons = [entity['word'] for entity in entities if entity['entity_group'] == 'PER']
    organizations = [entity['word'] for entity in entities if entity['entity_group'] == 'ORG']
    locations = [entity['word'] for entity in entities if entity['entity_group'] == 'LOC']

    print("📰 Title:", title)
    print("🔍 Sentiment:", sentiment['label'], f"({round(sentiment['score'] * 100, 2)}%)")
    print("📝 Summary:", summary)
    print("👤 Persons:", ", ".join(persons) if persons else "No persons found")
    print("🏢 Organizations:", ", ".join(organizations) if organizations else "No organizations found")
    print("🌍 Locations:", ", ".join(locations) if locations else "No locations found")
    print("📅 Published:", data['published_at'])
    print("🌐 Source:", data['source'])
    print("🔗 Link:", data['link'])
    print("-" * 80)