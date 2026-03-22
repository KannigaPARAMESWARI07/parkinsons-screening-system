import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib, os

DATA_PATH  = r'data\voice\parkinsons\parkinsons.data'
MODEL_DIR  = 'models'
os.makedirs(MODEL_DIR, exist_ok=True)

def train():
    df = pd.read_csv(DATA_PATH)
    feature_cols = [c for c in df.columns if c not in ['name', 'status']]
    X = df[feature_cols].values
    y = df['status'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=200, max_depth=10,
        min_samples_split=5, random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train_s, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_s))
    print(f"\nVoice model accuracy: {acc:.3f}")
    print(classification_report(y_test, model.predict(X_test_s)))

    joblib.dump(model,        os.path.join(MODEL_DIR, 'voice_model.pkl'))
    joblib.dump(scaler,       os.path.join(MODEL_DIR, 'voice_scaler.pkl'))
    joblib.dump(feature_cols, os.path.join(MODEL_DIR, 'voice_features.pkl'))
    print("Voice model saved to models/")

if __name__ == '__main__':
    train()