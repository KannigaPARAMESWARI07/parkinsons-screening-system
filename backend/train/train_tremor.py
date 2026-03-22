import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib, os

DATA_DIR  = r'data\tremor\daphnet+freezing+of+gait (1)\dataset_fog_release\dataset'
MODEL_DIR = 'models'
os.makedirs(MODEL_DIR, exist_ok=True)

def extract_features(window):
    features = []
    for col in range(window.shape[1]):
        sig = window[:, col]
        features += [
            np.mean(sig),
            np.std(sig),
            np.min(sig),
            np.max(sig),
            np.max(sig) - np.min(sig),
            np.sqrt(np.mean(sig**2)),
            np.sum(np.abs(np.diff(sig))),
            np.mean(np.abs(sig - np.mean(sig))),
        ]
    return np.array(features)

def load_data():
    X, y = [], []
    window_size = 192
    stride = 64

    for fname in os.listdir(DATA_DIR):
        if not fname.endswith('.txt'):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        try:
            df = pd.read_csv(fpath, sep=' ', header=None,
                names=['time','ankle_h','ankle_v','ankle_ml',
                       'upper_h','upper_v','upper_ml',
                       'trunk_h','trunk_v','trunk_ml','label'])
            df = df[df['label'] != 0]
            accel = df[['ankle_h','ankle_v','ankle_ml',
                        'trunk_h','trunk_v','trunk_ml']].values
            labels = df['label'].values

            for start in range(0, len(accel) - window_size, stride):
                window = accel[start:start + window_size]
                lw = labels[start:start + window_size]
                dominant = 2 if np.sum(lw == 2) > window_size * 0.5 else 1
                X.append(extract_features(window))
                y.append(1 if dominant == 2 else 0)
        except Exception as e:
            print(f"Skipping {fname}: {e}")

    return np.array(X), np.array(y)

def train():
    print("Loading Daphnet tremor data...")
    X, y = load_data()
    print(f"Total samples: {len(X)}, Freeze events: {np.sum(y)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=150, max_depth=8,
        random_state=42, class_weight='balanced'
    )
    model.fit(X_train_s, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_s))
    print(f"\nTremor model accuracy: {acc:.3f}")
    print(classification_report(y_test, model.predict(X_test_s)))

    cv = cross_val_score(model, X_train_s, y_train, cv=5)
    print(f"CV: {cv.mean():.3f} +/- {cv.std():.3f}")

    joblib.dump(model,  os.path.join(MODEL_DIR, 'tremor_model.pkl'))
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'tremor_scaler.pkl'))
    print("Tremor model saved to models/")

if __name__ == '__main__':
    train()