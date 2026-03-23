import os
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Paths
MODEL_DIR = "model"
DATASET_PATH = os.path.join(MODEL_DIR, "updated_medical_lab_dataset.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "disease_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

# Ensure the model directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

# Load dataset
df = pd.read_csv(DATASET_PATH)

# Feature columns (lab test values)
feature_cols = ["TSH", "T3", "T4", "Glucose","HbA1c", "Hemoglobin","RBC", "Creatinine", "Urea"]
X = df[feature_cols]
y = df["Disease_Label"]

# Encode disease labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Standardize lab values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42)

# Train RandomForestClassifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
# print(f"Model Accuracy: {accuracy * 88:.2f}%")

# Save model and utilities
with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

with open(ENCODER_PATH, "wb") as f:
    pickle.dump(label_encoder, f)

with open(SCALER_PATH, "wb") as f:
    pickle.dump(scaler, f)

print("Model, Label Encoder, and Scaler saved successfully.")
