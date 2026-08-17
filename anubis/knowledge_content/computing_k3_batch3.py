"""K3 advanced content for Computing specialties - Batch 3.

Covers: AI/ML, NLP, computer_vision, data_science, data_engineering
"""

COMPUTING_K3_BATCH3: dict[str, list[dict]] = {
    "computing_artificial_intelligence_machine_learning": [
        {
            "title": "Machine Learning Algorithms Reference",
            "content": r"""# Machine Learning Algorithms Reference

## Supervised Learning

### Linear Regression
```python
from sklearn.linear_model import LinearRegression
import numpy as np

X = np.array([[1], [2], [3], [4]])
y = np.array([2, 4, 6, 8])
model = LinearRegression()
model.fit(X, y)
print(model.coef_, model.intercept_)  # [2.0] 0.0
pred = model.predict([[5]])  # [10.0]
```

### Logistic Regression
```python
from sklearn.linear_model import LogisticRegression

X = [[0], [1], [2], [3]]
y = [0, 0, 1, 1]
model = LogisticRegression()
model.fit(X, y)
print(model.predict_proba([[1.5]]))  # [[0.5 0.5]]
```

### Decision Trees
```python
from sklearn.tree import DecisionTreeClassifier

model = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5)
model.fit(X_train, y_train)
# Feature importance
print(model.feature_importances_)
```

### Random Forest
```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_leaf=5,
    n_jobs=-1,
    random_state=42,
)
model.fit(X_train, y_train)
```

### Gradient Boosting
```python
from sklearn.ensemble import GradientBoostingClassifier
import xgboost as xgb

# XGBoost (faster, more popular)
model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
)
model.fit(X_train, y_train)
```

### SVM
```python
from sklearn.svm import SVC

model = SVC(kernel='rbf', C=1.0, gamma='scale')
model.fit(X_train, y_train)
```

### k-NN
```python
from sklearn.neighbors import KNeighborsClassifier

model = KNeighborsClassifier(n_neighbors=5, weights='distance')
model.fit(X_train, y_train)
```

## Unsupervised Learning

### K-Means
```python
from sklearn.cluster import KMeans

kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
labels = kmeans.fit_predict(X)
print(kmeans.cluster_centers_)

# Elbow method
inertias = []
for k in range(1, 11):
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    km.fit(X)
    inertias.append(km.inertia_)
# Plot and find elbow
```

### DBSCAN
```python
from sklearn.cluster import DBSCAN

db = DBSCAN(eps=0.5, min_samples=5)
labels = db.fit_predict(X)
# -1 means noise
```

### PCA
```python
from sklearn.decomposition import PCA

pca = PCA(n_components=2)
X_reduced = pca.fit_transform(X)
print(pca.explained_variance_ratio_)
```

## Neural Networks

### PyTorch Basics
```python
import torch
import torch.nn as nn
import torch.optim as optim

# Simple feedforward network
class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 10)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x

model = Net()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop
for epoch in range(10):
    for batch_x, batch_y in dataloader:
        optimizer.zero_grad()
        outputs = model(batch_x)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
```

### CNN
```python
class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x
```

### Transformer
```python
class TransformerBlock(nn.Module):
    def __init__(self, dim, heads=8):
        super().__init__()
        self.attention = nn.MultiheadAttention(dim, heads, batch_first=True)
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
        self.ff = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Linear(dim * 4, dim),
        )

    def forward(self, x):
        attn_out, _ = self.attention(x, x, x)
        x = self.norm1(x + attn_out)
        ff_out = self.ff(x)
        x = self.norm2(x + ff_out)
        return x
```

## Evaluation Metrics

### Classification
```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score,
)

accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred, average='weighted')
recall = recall_score(y_true, y_pred, average='weighted')
f1 = f1_score(y_true, y_pred, average='weighted')
auc = roc_auc_score(y_true, y_prob, multi_class='ovr')
```

### Regression
```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

mse = mean_squared_error(y_true, y_pred)
rmse = mse ** 0.5
mae = mean_absolute_error(y_true, y_pred)
r2 = r2_score(y_true, y_pred)
```

### Cross-Validation
```python
from sklearn.model_selection import cross_val_score, StratifiedKFold

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=cv, scoring='f1_weighted')
print(f"Mean: {scores.mean():.3f} +/- {scores.std():.3f}")
```

## Common Pitfalls
- Data leakage: fitting preprocessing on full dataset before CV
- Not stratifying CV for imbalanced classes
- Using accuracy for imbalanced datasets (use F1, AUC)
- Not setting random_state (non-reproducible results)
- Overfitting: model memorizes training data
- Underfitting: model too simple
- Not scaling features for distance-based algorithms
- Ignoring class imbalance (use class_weight, SMOTE, or resampling)
- Not checking for correlated features
- Test set contamination
""",
            "tags": ["machine learning", "scikit-learn", "PyTorch", "neural networks", "reference"],
        },
        {
            "title": "Training and Optimization Techniques",
            "content": r"""# Training and Optimization Techniques

## Loss Functions

### Classification
- CrossEntropyLoss: multi-class classification
- BCELoss: binary classification
- BCEWithLogitsLoss: binary, numerically stable

### Regression
- MSELoss: mean squared error (sensitive to outliers)
- MAELoss / L1Loss: mean absolute error (robust)
- HuberLoss: combination, robust + smooth
- SmoothL1Loss: Huber with beta parameter

## Optimizers

### SGD
```python
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9, weight_decay=1e-4)
```

### Adam (most common)
```python
optimizer = optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999), weight_decay=0)
```

### AdamW (recommended for transformers)
```python
optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
```

## Learning Rate Schedulers
```python
# Step decay
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)

# Cosine annealing
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50)

# One-cycle (fast.ai)
scheduler = optim.lr_scheduler.OneCycleLR(optimizer, max_lr=0.01, total_steps=1000)

# Reduce on plateau
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)
```

## Regularization

### Dropout
```python
self.dropout = nn.Dropout(p=0.5)
# In training: randomly zero elements with probability p
# In eval: identity
```

### Weight Decay (L2)
```python
optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
```

### Early Stopping
```python
best_loss = float('inf')
patience = 5
counter = 0

for epoch in range(100):
    train_loss = train(model, train_loader, optimizer)
    val_loss = evaluate(model, val_loader)
    
    if val_loss < best_loss:
        best_loss = val_loss
        counter = 0
        torch.save(model.state_dict(), 'best.pt')
    else:
        counter += 1
        if counter >= patience:
            print(f"Early stopping at epoch {epoch}")
            break
```

### Data Augmentation
```python
from torchvision import transforms

train_transform = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.RandomResizedCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```

## Transfer Learning
```python
import torchvision.models as models

# Load pretrained
model = models.resnet50(weights='ResNet50_Weights.DEFAULT')

# Freeze backbone
for param in model.parameters():
    param.requires_grad = False

# Replace head
model.fc = nn.Linear(model.fc.in_features, num_classes)

# Train only head
optimizer = optim.Adam(model.fc.parameters(), lr=0.001)

# Later: unfreeze and fine-tune with lower LR
for param in model.layer4.parameters():
    param.requires_grad = True
optimizer = optim.Adam([
    {'params': model.layer4.parameters(), 'lr': 1e-5},
    {'params': model.fc.parameters(), 'lr': 1e-3},
])
```

## Mixed Precision Training
```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch_x, batch_y in dataloader:
    optimizer.zero_grad()
    with autocast():
        outputs = model(batch_x)
        loss = criterion(outputs, batch_y)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

## Gradient Clipping
```python
# Prevent exploding gradients
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

## Distributed Training
```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

dist.init_process_group("nccl")
model = model.to(local_rank)
model = DDP(model, device_ids=[local_rank])
```

## Hyperparameter Tuning
```python
# Optuna
import optuna

def objective(trial):
    lr = trial.suggest_float('lr', 1e-5, 1e-1, log=True)
    n_layers = trial.suggest_int('n_layers', 1, 5)
    dropout = trial.suggest_float('dropout', 0, 0.5)
    
    model = build_model(lr, n_layers, dropout)
    accuracy = train_and_eval(model)
    return accuracy

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
print(study.best_params)
```

## Common Pitfalls
- Not shuffling training data
- Learning rate too high (diverging) or too low (slow)
- Not normalizing/standardizing input data
- Batch size too large (poor generalization) or too small (noisy)
- Not using validation set (overfitting to test)
- Forgetting model.eval() before inference (affects dropout/batchnorm)
- Not using torch.no_grad() during inference (wastes memory)
- Not saving best model (saving last model which may be worse)
- Not setting seeds for reproducibility
- Gradient explosion/vanishing (use clipping, proper init, batch norm)
""",
            "tags": ["training", "optimization", "PyTorch", "regularization", "reference"],
        },
    ],
    "computing_natural_language_processing": [
        {
            "title": "NLP and Transformers Reference",
            "content": r"""# NLP and Transformers Reference

## Text Preprocessing
```python
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Tokenization
nltk.download('punkt')
tokens = nltk.word_tokenize("Hello, world! How are you?")

# Lowercase
text = text.lower()

# Remove punctuation
text = re.sub(r'[^\w\s]', '', text)

# Remove stopwords
stop_words = set(stopwords.words('english'))
tokens = [t for t in tokens if t not in stop_words]

# Lemmatization
lemmatizer = WordNetLemmatizer()
tokens = [lemmatizer.lemmatize(t) for t in tokens]

# Stemming
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()
tokens = [stemmer.stem(t) for t in tokens]
```

## Word Embeddings

### Word2Vec / GloVe
```python
import gensim

# Train Word2Vec
model = gensim.models.Word2Vec(sentences, vector_size=100, window=5, min_count=1, workers=4)
vector = model.wv['computer']
similar = model.wv.most_similar('computer', topn=10)
```

### Using Pretrained
```python
import gensim.downloader as api

model = api.load("glove-wiki-gigaword-100")
print(model.most_similar("king"))
print(model.most_similar(positive=["king", "woman"], negative=["man"]))
```

## Hugging Face Transformers

### Pipeline (high-level)
```python
from transformers import pipeline

# Sentiment analysis
classifier = pipeline("sentiment-analysis")
result = classifier("I love this product!")
# [{'label': 'POSITIVE', 'score': 0.9998}]

# Text generation
generator = pipeline("text-generation", model="gpt2")
text = generator("Once upon a time", max_length=50, num_return_sequences=1)

# Named entity recognition
ner = pipeline("ner")
entities = ner("Apple was founded by Steve Jobs in California.")

# Question answering
qa = pipeline("question-answering")
answer = qa(question="Who founded Apple?", context="Apple was founded by Steve Jobs.")

# Summarization
summarizer = pipeline("summarization")
summary = summarizer(long_text, max_length=130, min_length=30)

# Translation
translator = pipeline("translation_en_to_fr")
translation = translator("Hello, how are you?")
```

### Direct Model Usage
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased")

inputs = tokenizer("Hello, world!", return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)
logits = outputs.logits
predicted_class = torch.argmax(logits, dim=1).item()
```

### Fine-tuning
```python
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir="./logs",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
)

trainer.train()
```

## Transformer Architecture

### Self-Attention
```python
import torch
import torch.nn.functional as F
import math

def self_attention(q, k, v, mask=None):
    d_k = q.size(-1)
    scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(d_k)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)
    attention = F.softmax(scores, dim=-1)
    return torch.matmul(attention, v)
```

### Positional Encoding
```python
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                             (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]
```

## Tokenization
```python
# BPE (Byte Pair Encoding) - used by GPT
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
tokenizer.pre_tokenizer = Whitespace()
trainer = BpeTrainer(special_tokens=["[UNK]", "[PAD]", "[CLS]", "[SEP]", "[MASK]"])
tokenizer.train_from_iterator(texts, trainer)

# SentencePiece - used by Llama, T5
# WordPiece - used by BERT
```

## Text Classification
```python
# Traditional approach
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
    ('clf', MultinomialNB()),
])
pipeline.fit(texts_train, labels_train)
predictions = pipeline.predict(texts_test)
```

## Common NLP Tasks
- **Sentiment Analysis**: classify text as positive/negative/neutral
- **NER**: extract entities (persons, organizations, locations)
- **POS Tagging**: assign part-of-speech to each token
- **Dependency Parsing**: analyze grammatical structure
- **Coreference Resolution**: find expressions referring to same entity
- **Text Summarization**: extractive or abstractive
- **Machine Translation**: translate between languages
- **Question Answering**: extractive or generative
- **Text Generation**: generate coherent text
- **Embedding**: convert text to vectors

## Pitfalls
- Not handling tokenization edge cases (subwords, special chars)
- Forgetting attention mask for padding
- Not using GPU for large models
- OOM with large batch sizes (reduce or use gradient accumulation)
- Not handling long sequences (truncation, sliding window, Longformer)
- Hallucination in generation (use grounding, retrieval)
- Bias in pretrained models (audit before deployment)
- Not using temperature/top-p for controlled generation
""",
            "tags": ["NLP", "transformers", "BERT", "Hugging Face", "tokenization", "reference"],
        },
    ],
    "computing_computer_vision": [
        {
            "title": "Computer Vision and Image Processing Reference",
            "content": r"""# Computer Vision Reference

## OpenCV Basics
```python
import cv2
import numpy as np

# Read/write
img = cv2.imread('image.jpg')
cv2.imwrite('output.jpg', img)

# Color spaces
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Resize
resized = cv2.resize(img, (width, height))
resized = cv2.resize(img, None, fx=0.5, fy=0.5)

# Crop
cropped = img[y:y+h, x:x+w]
```

## Image Processing

### Filtering
```python
# Blur
blurred = cv2.GaussianBlur(img, (5, 5), 0)

# Edge detection
edges = cv2.Canny(gray, 100, 200)

# Sharpen
kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
sharpened = cv2.filter2D(img, -1, kernel)
```

### Thresholding
```python
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
_, adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
```

### Morphology
```python
kernel = np.ones((5,5), np.uint8)
erosion = cv2.erode(binary, kernel, iterations=1)
dilation = cv2.dilate(binary, kernel, iterations=1)
opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
closing = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
```

### Contours
```python
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > 1000:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
```

## Deep Learning for Vision

### Image Classification (PyTorch)
```python
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

# Pretrained model
model = models.resnet50(weights='ResNet50_Weights.DEFAULT')
model.eval()

# Preprocessing
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

img = Image.open('image.jpg')
input_tensor = preprocess(img).unsqueeze(0)

with torch.no_grad():
    output = model(input_tensor)
    predicted = torch.argmax(output, dim=1).item()
```

### Object Detection (YOLO)
```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')  # nano version
results = model('image.jpg')
for r in results:
    boxes = r.boxes
    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        conf = box.conf[0]
        cls = box.cls[0]
        print(f"Class: {cls}, Conf: {conf:.2f}, Box: {x1},{y1},{x2},{y2}")
```

### Segmentation
```python
# Semantic segmentation
from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor

processor = SegformerImageProcessor.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")
model = SegformerForSemanticSegmentation.from_pretrained("nvidia/segformer-b0-finetuned-ade-512-512")

inputs = processor(images=img, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)
```

### Data Augmentation (albumentations)
```python
import albumentations as A

transform = A.Compose([
    A.RandomCrop(width=256, height=256),
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(p=0.2),
    A.Rotate(limit=10, p=0.5),
    A.Normalize(),
    ToTensorV2(),
])

augmented = transform(image=img)
img_aug = augmented['image']
```

## Evaluation Metrics

### Detection
- IoU (Intersection over Union): overlap between predicted and ground truth
- mAP (mean Average Precision): average AP across classes
- Precision-Recall curve

### Segmentation
- Pixel accuracy
- Mean IoU: average IoU across classes
- Dice coefficient: 2 * |A ∩ B| / (|A| + |B|)

## Common Pitfalls
- BGR vs RGB (OpenCV uses BGR, PIL uses RGB)
- Not normalizing images before neural network
- Forgetting to set model.eval() for inference
- Not using GPU for large models
- Wrong image size (must match training size)
- Not handling variable aspect ratios
- Data augmentation too aggressive (destroys signal)
- Not balancing classes in training data
- Overfitting on small datasets (use transfer learning)
""",
            "tags": ["computer vision", "OpenCV", "CNN", "YOLO", "image processing", "reference"],
        },
    ],
    "computing_data_science_analytics": [
        {
            "title": "Data Analysis with Python Reference",
            "content": r"""# Data Analysis with Python Reference

## pandas
```python
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data.csv')
df = pd.read_excel('data.xlsx')
df = pd.read_json('data.json')
df = pd.read_sql('SELECT * FROM users', connection)

# Inspect
df.head()
df.info()
df.describe()
df.shape
df.columns
df.dtypes

# Select
df['column']           # one column as Series
df[['col1', 'col2']]   # multiple columns
df.iloc[0:5]           # by position
df.loc[0:5, 'col1']    # by label
df[df['age'] > 18]     # filter

# Handle missing
df.isnull().sum()
df.dropna()
df.fillna(0)
df.fillna(df.mean())
df['col'].interpolate()

# Transform
df['new'] = df['col1'] + df['col2']
df['category'] = df['col'].astype('category')
df['date'] = pd.to_datetime(df['date_str'])

# Group by
grouped = df.groupby('category')['value'].agg(['mean', 'sum', 'count'])
grouped = df.groupby(['category', 'region'])['value'].mean()

# Pivot
pivot = df.pivot_table(values='sales', index='month', columns='product', aggfunc='sum')

# Merge
merged = pd.merge(df1, df2, on='id', how='left')
merged = pd.concat([df1, df2], axis=0)  # rows
merged = pd.concat([df1, df2], axis=1)  # columns

# Time series
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
df.resample('M').sum()      # monthly
df.rolling(window=7).mean() # 7-day moving average
df.shift(1)                  # lag by 1
```

## NumPy
```python
import numpy as np

# Create
arr = np.array([1, 2, 3, 4, 5])
matrix = np.array([[1, 2], [3, 4]])
zeros = np.zeros((3, 4))
ones = np.ones((2, 3))
identity = np.eye(3)
range_arr = np.arange(0, 10, 2)
linspace = np.linspace(0, 1, 11)

# Operations
arr.sum(), arr.mean(), arr.std(), arr.min(), arr.max()
arr.reshape(3, 4)
arr.T  # transpose
arr @ arr2  # matrix multiply
np.dot(a, b)

# Broadcasting
arr + 5  # add scalar to each element
matrix + arr  # if shapes compatible

# Boolean indexing
arr[arr > 2] = 0
mask = (arr > 1) & (arr < 4)
```

## Visualization

### matplotlib
```python
import matplotlib.pyplot as plt

# Line plot
plt.plot(x, y, label='data')
plt.xlabel('X')
plt.ylabel('Y')
plt.title('Title')
plt.legend()
plt.savefig('plot.png')
plt.show()

# Subplots
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes[0, 0].plot(x, y1)
axes[0, 1].scatter(x, y2)
axes[1, 0].hist(data, bins=30)
axes[1, 1].bar(categories, values)
```

### seaborn
```python
import seaborn as sns

# Statistical plots
sns.scatterplot(data=df, x='age', y='income', hue='category')
sns.boxplot(data=df, x='category', y='value')
sns.violinplot(data=df, x='category', y='value')
sns.heatmap(df.corr(), annot=True, cmap='coolwarm')
sns.pairplot(df)
sns.distplot(df['column'])
```

### plotly (interactive)
```python
import plotly.express as px

fig = px.scatter(df, x='age', y='income', color='category', hover_data=['name'])
fig.show()
```

## Statistical Analysis
```python
from scipy import stats

# Hypothesis testing
t_stat, p_value = stats.ttest_ind(group1, group2)
u_stat, p_value = stats.mannwhitneyu(group1, group2)
chi2, p_value, _, _ = stats.chi2_contingency(contingency_table)

# Correlation
pearson_r, p_value = stats.pearsonr(x, y)
spearman_r, p_value = stats.spearmanr(x, y)

# Distributions
stats.normaltest(data)  # test for normality
stats.shapiro(data)     # Shapiro-Wilk test
```

## Common Pitfalls
- Modifying a DataFrame slice (use .copy())
- Chained indexing (df[df.a > 0]['b'] = 1) -> SettingWithCopyWarning
- Not handling missing data explicitly
- Assuming data is sorted
- Not checking data types (numbers stored as strings)
- Memory issues with large DataFrames (use dtypes, chunks)
- Not setting index for time series
- Confusing .loc and .iloc
- Not using categorical dtype for low-cardinality strings
""",
            "tags": ["pandas", "numpy", "data analysis", "visualization", "statistics", "reference"],
        },
    ],
    "computing_data_engineering": [
        {
            "title": "Data Pipeline and ETL Reference",
            "content": r"""# Data Pipeline and ETL Reference

## Apache Airflow
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'etl_pipeline',
    default_args=default_args,
    description='Daily ETL',
    schedule_interval='0 2 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['etl'],
)

def extract(**context):
    # Extract from source
    data = pd.read_csv('/data/source.csv')
    context['task_instance'].xcom_push('data', data.to_json())

def transform(**context):
    ti = context['task_instance']
    data = pd.read_json(ti.xcom_pull('data'))
    # Transform
    data['total'] = data['price'] * data['quantity']
    data = data[data['total'] > 0]
    ti.xcom_push('data', data.to_json())

def load(**context):
    ti = context['task_instance']
    data = pd.read_json(ti.xcom_pull('data'))
    # Load to warehouse
    data.to_sql('orders', engine, if_exists='append', index=False)

t1 = PythonOperator(task_id='extract', python_callable=extract, dag=dag)
t2 = PythonOperator(task_id='transform', python_callable=transform, dag=dag)
t3 = PythonOperator(task_id='load', python_callable=load, dag=dag)

t1 >> t2 >> t3
```

## dbt (Data Build Tool)
```sql
-- models/staging/stg_orders.sql
SELECT
    order_id,
    customer_id,
    order_date,
    amount
FROM {{ source('raw', 'orders') }}
WHERE order_date >= '2024-01-01'

-- models/marts/fct_daily_revenue.sql
SELECT
    DATE(order_date) as date,
    SUM(amount) as revenue,
    COUNT(DISTINCT customer_id) as customers
FROM {{ ref('stg_orders') }}
GROUP BY 1
```

```yaml
# dbt_project.yml
models:
  my_project:
    staging:
      +materialized: view
    marts:
      +materialized: table
      +schema: marts
```

## Apache Spark
```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("ETL").getOrCreate()

# Read
df = spark.read.csv("data.csv", header=True, inferSchema=True)
df = spark.read.parquet("data.parquet")
df = spark.read.jdbc(url, table, properties=props)

# Transform
df = df.filter(F.col("amount") > 0)
df = df.withColumn("total", F.col("price") * F.col("quantity"))
df = df.groupBy("category").agg(
    F.sum("total").alias("revenue"),
    F.count("*").alias("count"),
    F.avg("total").alias("avg_order"),
)

# Write
df.write.mode("overwrite").parquet("output/")
df.write.mode("append").jdbc(url, "summary", properties=props)

# SQL
df.createOrReplaceTempView("orders")
result = spark.sql(
    "SELECT category, SUM(total) as revenue "
    "FROM orders "
    "GROUP BY category "
    "ORDER BY revenue DESC"
)
```

## Kafka
```python
from kafka import KafkaProducer, KafkaConsumer
import json

# Producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
)
producer.send('events', {'event': 'purchase', 'user_id': 123})
producer.flush()

# Consumer
consumer = KafkaConsumer(
    'events',
    bootstrap_servers=['localhost:9092'],
    group_id='etl-group',
    auto_offset_reset='earliest',
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
)
for message in consumer:
    process_event(message.value)
```

## Data Quality Checks
```python
# Great Expectations
import great_expectations as gx

df = pd.read_csv('data.csv')
df.expect_column_values_to_not_be_null('id')
df.expect_column_values_to_be_unique('id')
df.expect_column_values_to_be_between('age', 0, 120)
df.expect_column_values_to_be_in_set('status', ['active', 'inactive'])

# Custom check
def check_no_negative_revenue(df):
    assert (df['revenue'] >= 0).all(), "Negative revenue found"
    return True
```

## Idempotency
- Pipeline should produce same result when re-run
- Use MERGE/UPSERT instead of INSERT
- Track processed records with watermark
- Use deterministic keys

```sql
-- Idempotent upsert
INSERT INTO target (id, value, updated_at)
VALUES (1, 'a', '2024-01-01')
ON CONFLICT (id) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = EXCLUDED.updated_at;
```

## Common Pitfalls
- Non-idempotent pipelines (re-runs cause duplicates)
- Not handling schema evolution
- Loading before validation (garbage in, garbage out)
- Not monitoring pipeline failures
- Long-running transformations blocking downstream
- Not using partitioning for large datasets
- Memory issues with large DataFrames (use chunks or Spark)
- Not setting timeouts on external calls
- Not handling late-arriving data
- Hardcoding credentials in pipeline code
""",
            "tags": ["ETL", "Airflow", "Spark", "dbt", "Kafka", "pipelines", "reference"],
        },
    ],
}
