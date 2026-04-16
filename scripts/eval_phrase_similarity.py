import os
import argparse
import numpy as np
import pandas as pd
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from scipy.stats import pearsonr, spearmanr
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
from tqdm import tqdm
from dotenv import load_dotenv

# Load env for HF_TOKEN
load_dotenv(os.path.join(os.path.dirname(__file__), '../backend/.env'))

def get_model():
    """Initializes the EmbeddingGemma model directly."""
    model_id = "google/embeddinggemma-300m"
    try:
        print(f"Loading {model_id}...")
        return SentenceTransformer(
            model_id, 
            trust_remote_code=True,
            token=os.getenv("HF_TOKEN") or True
        )
    except Exception as e:
        print(f"Failed to load model: {e}")
        return None

def compute_cosine_similarity(vec1, vec2):
    """Computes cosine similarity between two 1D arrays."""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm1 * norm2)

import pickle

class EmbeddingCache:
    def __init__(self, model, cache_file="embedding_cache.pkl"):
        self.model = model
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            print(f"Loading embedding cache from {self.cache_file}...")
            try:
                with open(self.cache_file, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Failed to load cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        print(f"Saving embedding cache ({len(self.cache)} items) to {self.cache_file}...")
        try:
            with open(self.cache_file, "wb") as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"Failed to save cache: {e}")

    def get_embeddings(self, texts):
        # Identify unique texts not in cache
        unique_texts = list(set(texts))
        missing_texts = [t for t in unique_texts if t not in self.cache]
        
        if missing_texts:
            print(f"Encoding {len(missing_texts)} unique phrases...")
            # Batch encode
            embeddings = self.model.encode(missing_texts, batch_size=32, show_progress_bar=True)
            for text, emb in zip(missing_texts, embeddings):
                self.cache[text] = emb
            
            # Save after update
            self._save_cache()
        
        return np.array([self.cache[t] for t in texts])

def main():
    print("Loading dataset 'tasksource/patent-phrase-similarity'...")
    try:
        # Load the dataset
        ds = load_dataset("tasksource/patent-phrase-similarity")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # Check for splits
    print(f"Available splits: {ds.keys()}")
    
    # We mainly care about labeled data. 
    # Usually 'train' has labels. 'test' might not.
    # We will combine all labeled splits and then do our own 80/20 split if needed.
    
    labeled_rows = []
    
    # Iterate over splits to find labeled data
    for split_name in ds.keys():
        split_data = ds[split_name]
        # Check if 'score' or 'label' exists
        if 'score' in split_data.features:
            print(f"Found 'score' in split '{split_name}'. Adding {len(split_data)} rows.")
            for row in split_data:
                labeled_rows.append({
                    'anchor': row['anchor'],
                    'target': row['target'],
                    'score': row['score'],
                    'context': row['context']
                })
    
    df = pd.DataFrame(labeled_rows)
    print(f"Total labeled rows: {len(df)}")
    
    if len(df) == 0:
        print("No labeled data found!")
        return

    # Analyze Label Distribution
    print("Label Distribution:")
    print(df['score'].value_counts().sort_index())

    # Split 80/20
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['score'])
    print(f"Train size: {len(train_df)}, Val size: {len(val_df)}")

    # Load Model
    model = get_model()
    if not model:
        return

    embedder = EmbeddingCache(model)

    # Process Train
    print("Processing Train Set...")
    train_anchors = embedder.get_embeddings(train_df['anchor'].tolist())
    train_targets = embedder.get_embeddings(train_df['target'].tolist())
    
    # Compute Cosine Similarities (Train)
    # Optimized: Dot product of normalized vectors
    # SentenceTransformers outputs are usually normalized if normalize_embeddings=True is set or by default for some
    # But let's verify or manually normalize. 
    # Actually, simpler to just use sklearn cosine_similarity or manual loop if RAM is tight.
    # Manual loop is slow in python. Let's use numpy.
    
    def fast_cosine_sim(a, b):
        # a and b are (N, D) arrays
        # Normalize
        a_norm = a / np.linalg.norm(a, axis=1, keepdims=True)
        b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
        return np.sum(a_norm * b_norm, axis=1)

    train_cosines = fast_cosine_sim(train_anchors, train_targets)
    train_labels = train_df['score'].values

    # Learn Calibration (Linear)
    # Reshape for sklearn
    X_train = train_cosines.reshape(-1, 1)
    y_train = train_labels
    
    calib_model = LinearRegression()
    calib_model.fit(X_train, y_train)
    print(f"Calibration developed: Score = {calib_model.coef_[0]:.4f} * Cosine + {calib_model.intercept_:.4f}")

    # Process Validation
    print("Processing Validation Set...")
    val_anchors = embedder.get_embeddings(val_df['anchor'].tolist())
    val_targets = embedder.get_embeddings(val_df['target'].tolist())
    
    val_cosines = fast_cosine_sim(val_anchors, val_targets)
    val_labels = val_df['score'].values
    
    # Apply Calibration
    val_preds_calib = calib_model.predict(val_cosines.reshape(-1, 1))
    # Clip predictions to [0, 1] range as labels are within that
    val_preds_calib = np.clip(val_preds_calib, 0, 1)

    # Metrics
    pearson_corr, _ = pearsonr(val_cosines, val_labels)
    spearman_corr, _ = spearmanr(val_cosines, val_labels)
    
    mae_raw = mean_absolute_error(val_labels, val_cosines)
    rmse_raw = np.sqrt(mean_squared_error(val_labels, val_cosines))
    
    mae_calib = mean_absolute_error(val_labels, val_preds_calib)
    rmse_calib = np.sqrt(mean_squared_error(val_labels, val_preds_calib))

    # Empirical Distribution Analysis
    print("Computing empirical distributions...")
    dist_data = []
    unique_labels = sorted(np.unique(val_labels))
    
    for label in unique_labels:
        mask = (val_labels == label)
        scores_for_label = val_cosines[mask]
        if len(scores_for_label) > 0:
            dist_data.append({
                "Label": label,
                "Count": len(scores_for_label),
                "Mean": np.mean(scores_for_label),
                "Median": np.median(scores_for_label),
                "P25": np.percentile(scores_for_label, 25),
                "P75": np.percentile(scores_for_label, 75)
            })
    
    dist_df = pd.DataFrame(dist_data)
    
    # Generate Report
    report = f"""# EmbeddingGemma Patent Phrase Similarity Evaluation

**Date**: {pd.Timestamp.now()}
**Dataset**: tasksource/patent-phrase-similarity (Hugging Face)
**Model**: google/embeddinggemma-300m
**Split**: 80/20 Random Split (Seed 42)

## 1. Metrics (Validation Set)

| Metric | Raw (Cosine) | Calibrated |
|---|---|---|
| **Pearson Correlation** | **{pearson_corr:.4f}** | - |
| **Spearman Correlation** | **{spearman_corr:.4f}** | - |
| **MAE** | {mae_raw:.4f} | **{mae_calib:.4f}** |
| **RMSE** | {rmse_raw:.4f} | **{rmse_calib:.4f}** |

> [!NOTE]
> **Pearson/Spearman** reflect the quality of the ranking (crucial for retrieval).
> **MAE/RMSE** reflect the accuracy of the score interpretation after calibration.

## 2. Empirical Cosine Distributions (Validation)
Instead of a theoretical mapping, here is how the model actually scores pairs at each human similarity level:

{dist_df.to_markdown(index=False, floatfmt=".4f")}

## 3. Calibration
Linear fit on Train set:
`Predicted_Score = {calib_model.coef_[0]:.4f} * Cosine_Similarity + {calib_model.intercept_:.4f}`

> [!WARNING]
> **Limitations of Linear Calibration**:
> The linear model is a global approximation. As seen in the empirical distributions, the cosine scores for "Unrelated" (0.0) and "Weak Match" (0.25) often overlap significantly. The linear fit implies a negative human score for low cosines, which is impossible. Use the calibrated score for rough guidance, but rely on the **rank** for retrieval.

## 4. Recommended Usage in APEX
Based on the validation distributions, we recommend the following retrieval prioritization bands. These are for **retrieval filtering**, not legal anticipation judgments.

| Band | Cosine Range (Approx) | APEX Action |
|---|---|---|
| **Unrelated / Noise** | < {dist_df.loc[dist_df['Label']==0.25, 'P25'].values[0]:.2f} | **Filter Out**: Likely irrelevant to the active element. |
| **Thematically Related** | {dist_df.loc[dist_df['Label']==0.25, 'P25'].values[0]:.2f} - {dist_df.loc[dist_df['Label']==0.5, 'Mean'].values[0]:.2f} | **Background**: Useful for defining the field of invention but likely not anticipatory. |
| **Potentially Relevant** | {dist_df.loc[dist_df['Label']==0.5, 'Mean'].values[0]:.2f} - {dist_df.loc[dist_df['Label']==0.75, 'Median'].values[0]:.2f} | **Examiner Review**: Candidate for "A" (background) or "Y" (obviousness) references. |
| **Strong Candidate** | > {dist_df.loc[dist_df['Label']==0.75, 'Median'].values[0]:.2f} | **Priority**: High probability of being an "X" (anticipatory) reference. |

"""
    
    print(report)
    
    # Save Report
    with open("EVAL_GEMMA_PPS.md", "w") as f:
        f.write(report)
    print("Report saved to EVAL_GEMMA_PPS.md")

if __name__ == "__main__":
    main()
