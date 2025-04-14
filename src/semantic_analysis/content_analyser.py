from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize
import re
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin

class TextPreprocessor(BaseEstimator, TransformerMixin):
	def __init__(self, nlp_model, stop_words):
		self.nlp = nlp_model
		self.stop_words = stop_words
		
	def fit(self, X, y=None):
		return self
		
	def transform(self, texts):
		return [' '.join(self.preprocess_text(text)) for text in texts]
		
	def preprocess_text(self, text):
		text = text.lower()
		text = re.sub(r'[^\w\s]', ' ', text)
		tokens = word_tokenize(text, language='french', preserve_line=True)
		return [word for word in tokens if word not in self.stop_words and len(word) > 2]

class ContentAnalyzer:
	def __init__(self, nlp_model, stop_words):
		self.nlp = nlp_model
		self.stop_words = stop_words
		self.preprocessor = TextPreprocessor(nlp_model, stop_words)

	def preprocess_text(self, text):
		return self.preprocessor.preprocess_text(text)

	def extract_keywords_tfidf(self, documents, titles, max_features=100):
		if not documents:
			return []
		
		tfidf_pipeline = Pipeline([
			('preprocessor', self.preprocessor),
			('vectorizer', TfidfVectorizer(
				max_features=max_features, 
				ngram_range=(1, 2),
				preprocessor=lambda x: x,  
				tokenizer=lambda x: x.split()
			))
		])
		
		tfidf_matrix = tfidf_pipeline.fit_transform(documents)
		feature_names = tfidf_pipeline.named_steps['vectorizer'].get_feature_names_out()
		
		# Traitement des résultats
		keywords_by_doc = []
		for i, doc in enumerate(tfidf_matrix):
			tfidf_scores = zip(feature_names, doc.toarray()[0])
			sorted_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
			top_keywords = [{'keyword': kw, 'score': float(score)} for kw, score in sorted_keywords if score > 0]
			keywords_by_doc.append({
				'title': titles[i] if i < len(titles) else "Sans titre",
				'keywords': top_keywords[:30]
			})
		
		return keywords_by_doc

	def extract_entities(self, text):
		doc = self.nlp(text)
		return [{'text': ent.text, 'label': ent.label_, 'start': ent.start_char, 'end': ent.end_char}
				for ent in doc.ents]

	def extract_relations(self, doc_text):
		relations = []
		doc = self.nlp(doc_text)
		for sent in doc.sents:
			for token in sent:
				if token.pos_ == "VERB":
					subject = next((child.text for child in token.children if child.dep_ in ["nsubj", "nsubjpass"]), None)
					obj = next((child.text for child in token.children if child.dep_ in ["dobj", "pobj"]), None)
					if subject and obj:
						relations.append({
							'source': subject,
							'relation': token.text,
							'target': obj,
							'sentence': sent.text
						})
		return relations