from flask import Flask, request, jsonify, render_template
from SPARQLWrapper import SPARQLWrapper, JSON
import spacy

# Initialisation de Flask
app = Flask(__name__)

# Charger le modèle NLP de spaCy
nlp = spacy.load("en_core_web_sm")


# Fonction pour exécuter une requête SPARQL avec DBpedia
def execute_sparql_query(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        bindings = results.get("results", {}).get("bindings", [])
        response = []
        for result in bindings:
            concept_uri = result.get("Concept", {}).get("value", "No URI available")
            label = result.get("label", {}).get("value", "No label available")
            comment = result.get("comment", {}).get("value", "No comment available")

            # Analyse NLP des labels et commentaires
            label_entities = []
            if label:
                label_doc = nlp(label)
                label_entities = [{"text": ent.text, "label": ent.label_} for ent in label_doc.ents]

            comment_entities = []
            if comment:
                comment_doc = nlp(comment)
                comment_entities = [{"text": ent.text, "label": ent.label_} for ent in comment_doc.ents]

            # Préparer les données pour la réponse
            response.append({
                "uri": concept_uri,
                "label": label,
                "label_entities": label_entities,
                "comment": comment[:100] + "..." if len(comment) > 100 else comment,
                "comment_entities": comment_entities
            })
        return response
    except Exception as e:
        raise e

# Route pour l'interface utilisateur
@app.route('/')
def index():
    return render_template('index.html')

# Route pour traiter les requêtes SPARQL
@app.route('/sparql', methods=['POST'])
def sparql_query():
    query = request.json.get('query')
    if not query:
        return jsonify({"error": "Requête SPARQL manquante"}), 400
    try:
        results = execute_sparql_query(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
