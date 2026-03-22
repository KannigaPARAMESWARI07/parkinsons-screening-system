import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib, os

DATA_DIR  = r'data\gait\gait-in-parkinsons-disease-1.0.0\gait-in-parkinsons-disease-1.0.0'
MODEL_DIR = 'models'
os.makedirs(MODEL_DIR, exist_ok=True)

class GaitLSTM(nn.Module):
    def __init__(self, input_size=16, hidden_size=64, num_layers=2, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size, hidden_size=hidden_size,
            num_layers=num_layers, batch_first=True, dropout=dropout
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        return self.classifier(h_n[-1])

def load_data():
    sequences, labels = [], []
    window_len = 100

    for fname in os.listdir(DATA_DIR):
        if not fname.endswith('.txt'):
            continue
        if fname in ['demographics.txt', 'format.txt', 'SHA256SUMS.txt']:
            continue

        # GaCo/SiCo/JuCo = control (0), GaPt/SiPt/JuPt = Parkinson's (1)
        is_pd = any(x in fname for x in ['GaPt','SiPt','JuPt'])

        try:
            df = pd.read_csv(
                os.path.join(DATA_DIR, fname),
                sep='\t', header=None, comment='#'
            )
            # Columns: time + 8 left + 8 right force sensors = 17 cols
            # Use columns 1 onwards (skip time column 0)
            if df.shape[1] < 5:
                continue
            data = df.iloc[:, 1:17].values.astype(np.float32)
            if data.shape[1] < 16:
                # pad if fewer columns
                pad = np.zeros((data.shape[0], 16 - data.shape[1]), dtype=np.float32)
                data = np.hstack([data, pad])

            for start in range(0, len(data) - window_len, window_len // 2):
                seg = data[start:start + window_len]
                if seg.shape[0] == window_len:
                    sequences.append(seg)
                    labels.append(1 if is_pd else 0)
        except Exception as e:
            print(f"Skipping {fname}: {e}")

    return np.array(sequences, dtype=np.float32), np.array(labels)

def train():
    print("Loading PhysioNet gait data...")
    X, y = load_data()
    print(f"Sequences: {len(X)}, Parkinson's: {int(np.sum(y))}, Control: {int(len(y)-np.sum(y))}")

    # Normalize
    X_flat = X.reshape(-1, X.shape[-1])
    scaler = StandardScaler()
    X_flat_s = scaler.fit_transform(X_flat)
    X_scaled = X_flat_s.reshape(X.shape)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    X_tr = torch.FloatTensor(X_train)
    y_tr = torch.FloatTensor(y_train).unsqueeze(1)
    X_te = torch.FloatTensor(X_test)
    y_te = torch.FloatTensor(y_test).unsqueeze(1)

    loader = DataLoader(TensorDataset(X_tr, y_tr), batch_size=32, shuffle=True)

    model = GaitLSTM(input_size=X_scaled.shape[-1])
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.BCELoss()
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)

    best_acc = 0
    for epoch in range(50):
        model.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            preds = (model(X_te) > 0.5).float()
            acc = (preds == y_te).float().mean().item()
            scheduler.step(1 - acc)

        if acc > best_acc:
            best_acc = acc
            torch.save(model.state_dict(), os.path.join(MODEL_DIR, 'gait_model.pt'))

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/50 — val acc: {acc:.3f}  best: {best_acc:.3f}")

    joblib.dump(scaler, os.path.join(MODEL_DIR, 'gait_scaler.pkl'))
    print(f"\nGait model saved. Best accuracy: {best_acc:.3f}")

if __name__ == '__main__':
    train()