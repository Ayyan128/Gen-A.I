import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib

df = pd.read_csv('data/tools_training_data.csv')
x = df['text']
y = df['tool_id']
print('rows loaded')
model = Pipeline([
    ('tfidf', TfidfVectorizer(
        lowercase=True,
        ngram_range=(1,2),
        max_features=3000
    )),
    ('nb', MultinomialNB(alpha=0.1))
])

model.fit(x,y)
print('model trained succesfully')

try:
    joblib.dump(model, 'models/tool_model.joblib', compress=1)
except FileNotFoundError:
    with open('data/tool_model.joblib', 'w') as f:
        f.write()
    joblib.dump(model, 'models/tool_model.joblib', compress=1)