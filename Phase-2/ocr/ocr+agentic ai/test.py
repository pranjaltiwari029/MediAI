import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import classification_report, ConfusionMatrixDisplay

# Models
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

# -----------------------------
# Load Dataset
# -----------------------------
df = pd.read_csv("model/realistic_medical_dataset_700_rows.csv")
print(df.shape)

# Features and target
X = df.drop(columns=["Disease_Label"])
y = df["Disease_Label"]
print("TESTING THE LABELS")
print(df.groupby("Disease_Label").mean())
# Encode labels
le = LabelEncoder()
y = le.fit_transform(y)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Feature scaling
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# -----------------------------
# Models
# -----------------------------
models = {
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "SVM": SVC(kernel="rbf"),
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Gradient Boosting": GradientBoostingClassifier()
}

results = []
trained_models = {}

# -----------------------------
# Train & Evaluate
# -----------------------------
for name, model in models.items():

    print("\n==============================")
    print(f"Training Model: {name}")
    print("==============================")

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="weighted")
    recall = recall_score(y_test, y_pred, average="weighted")
    f1 = f1_score(y_test, y_pred, average="weighted")

    results.append([name, accuracy, precision, recall, f1])
    trained_models[name] = model

    print(classification_report(y_test, y_pred))

# -----------------------------
# Comparison Table
# -----------------------------
results_df = pd.DataFrame(
    results,
    columns=["Model", "Accuracy", "Precision", "Recall", "F1 Score"]
)

print("\nModel Comparison Results\n")
print(results_df)

results_df.to_csv("model_comparison_results.csv", index=False)

# -----------------------------
# Accuracy Bar Chart
# -----------------------------
plt.figure()

plt.bar(results_df["Model"], results_df["Accuracy"])

plt.title("Model Accuracy Comparison")
plt.ylabel("Accuracy")
plt.xlabel("Models")

plt.xticks(rotation=30)

plt.tight_layout()

plt.savefig("model_accuracy_comparison.png")

print("\nSaved: model_accuracy_comparison.png")

# -----------------------------
# Confusion Matrix (Random Forest)
# -----------------------------
rf_model = trained_models["Random Forest"]

y_pred_rf = rf_model.predict(X_test)

disp = ConfusionMatrixDisplay.from_predictions(
    y_test,
    y_pred_rf
)

plt.title("Confusion Matrix - Random Forest")

plt.savefig("random_forest_confusion_matrix.png")

print("Saved: random_forest_confusion_matrix.png")