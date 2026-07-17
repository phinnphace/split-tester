#!/usr/bin/env python3
"""
Phase 10: Split Ratio Comparison
Fixed model initialization, fixed data, fixed seed.
Varies only the train/val split ratio.
Measures internal validation accuracy for each split.
"""
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
from PIL import Image
import secrets
import json

BATCH_SIZE = 32
EPOCHS = 30
LEARNING_RATE = 0.001
TARGET_SIZE = (100, 100)
DEVICE = torch.device("cpu")
FIXED_SEED = 42  # Constant across all runs

SPLITS = [0.5, 0.6, 0.7, 0.8, 0.9]

class CharacterCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.fc = nn.Linear(128, 2)
    
    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)

class InMemoryDataset(Dataset):
    def __init__(self, images, labels):
        self.images = images
        self.labels = labels
    def __len__(self):
        return len(self.images)
    def __getitem__(self, idx):
        return self.images[idx], self.labels[idx]

def load_all_data():
    images, labels = [], []
    for label_val, dir_path in [(1, "data/isolated/target")]:
        if os.path.isdir(dir_path):
            for f in sorted(os.listdir(dir_path)):
                if f.endswith('.png'):
                    img = Image.open(os.path.join(dir_path, f)).convert('L')
                    img = img.resize(TARGET_SIZE, Image.LANCZOS)
                    t = torch.tensor(np.array(img), dtype=torch.float32) / 255.0
                    images.append(t.unsqueeze(0))
                    labels.append(label_val)
    for ch in sorted(os.listdir("data/isolated/distractors")):
        ch_dir = os.path.join("data/isolated/distractors", ch)
        if os.path.isdir(ch_dir):
            for f in sorted(os.listdir(ch_dir)):
                if f.endswith('.png'):
                    img = Image.open(os.path.join(ch_dir, f)).convert('L')
                    img = img.resize(TARGET_SIZE, Image.LANCZOS)
                    t = torch.tensor(np.array(img), dtype=torch.float32) / 255.0
                    images.append(t.unsqueeze(0))
                    labels.append(0)
    return images, labels

def train_and_evaluate(train_img, train_lbl, val_img, val_lbl):
    torch.manual_seed(FIXED_SEED)
    np.random.seed(FIXED_SEED)
    
    train_ds = InMemoryDataset(train_img, train_lbl)
    val_ds = InMemoryDataset(val_img, val_lbl)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    model = CharacterCNN().to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    best_val_acc = 0.0
    for epoch in range(EPOCHS):
        model.train()
        for imgs, lbls in train_loader:
            imgs, lbls = imgs.to(DEVICE), lbls.to(DEVICE)
            optimizer.zero_grad()
            loss = criterion(model(imgs), lbls)
            loss.backward()
            optimizer.step()
        
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for imgs, lbls in val_loader:
                imgs, lbls = imgs.to(DEVICE), lbls.to(DEVICE)
                _, preds = torch.max(model(imgs), 1)
                total += lbls.size(0)
                correct += (preds == lbls).sum().item()
        acc = correct / total
        if acc > best_val_acc:
            best_val_acc = acc
    
    return best_val_acc

# Main
print("Phase 10: Split Ratio Window")
print(f"Fixed seed: {FIXED_SEED}")
print()

images, labels = load_all_data()
print(f"Total images: {len(images)} ({sum(labels)} da, {len(labels)-sum(labels)} other)")

# Fixed shuffle order for all splits
rng = secrets.SystemRandom()
indices = list(range(len(images)))
rng.shuffle(indices)

results = {}
for split in SPLITS:
    split_name = f"train_{int(split*100)}_val_{int((1-split)*100)}"
    split_idx = int(len(indices) * split)
    train_idx = indices[:split_idx]
    val_idx = indices[split_idx:]
    
    train_img = [images[i] for i in train_idx]
    train_lbl = [labels[i] for i in train_idx]
    val_img = [images[i] for i in val_idx]
    val_lbl = [labels[i] for i in val_idx]
    
    acc = train_and_evaluate(train_img, train_lbl, val_img, val_lbl)
    results[split_name] = {
        'train_size': len(train_idx),
        'val_size': len(val_idx),
        'val_accuracy': acc
    }
    print(f"  {split_name}: train={len(train_idx)}, val={len(val_idx)}, accuracy={acc:.4f}")

print(f"\nSplit ratio window:")
for name, r in results.items():
    print(f"  {name}: {r['val_accuracy']:.4f}")

with open('models/split_window.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nSaved to models/split_window.json")
