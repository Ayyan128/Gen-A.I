import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import joblib

df = pd.read_csv('data/tools_training_data.csv')
x = df['text']
y = df['tool_id']
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
print('data loaded')
print('rows loaded')
model = Pipeline([
    ('tfidf', TfidfVectorizer(
        lowercase=True,
        ngram_range=(1,2),
        max_features=3000
    )),
    (
        'rf', RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            random_state=42
        )
    )
])

model.fit(x_train,y_train)
print('model trained succesfully')
accuracy_score = accuracy_score(y_test, model.predict(x_test))
print(f'Model accuracy: {accuracy_score:.2f}')
if accuracy_score > 0.85:
    try:
        joblib.dump(model, 'models/tool_model.joblib', compress=1)
    except FileNotFoundError:
        with open('data/tool_model.joblib', 'w') as f:
            f.write()
        joblib.dump(model, 'models/tool_model.joblib', compress=1)