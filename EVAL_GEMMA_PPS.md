# EmbeddingGemma Patent Phrase Similarity Evaluation

**Date**: 2025-12-11 16:11:36.202084
**Dataset**: tasksource/patent-phrase-similarity (Hugging Face)
**Model**: google/embeddinggemma-300m
**Split**: 80/20 Random Split (Seed 42)

## 1. Metrics (Validation Set)

| Metric | Raw (Cosine) | Calibrated |
|---|---|---|
| **Pearson Correlation** | **0.5756** | - |
| **Spearman Correlation** | **0.5527** | - |
| **MAE** | 0.2997 | **0.1695** |
| **RMSE** | 0.3552 | **0.2117** |

> [!NOTE]
> **Pearson/Spearman** reflect the quality of the ranking (crucial for retrieval).
> **MAE/RMSE** reflect the accuracy of the score interpretation after calibration.

## 2. Empirical Cosine Distributions (Validation)
Instead of a theoretical mapping, here is how the model actually scores pairs at each human similarity level:

|   Label |     Count |   Mean |   Median |    P25 |    P75 |
|--------:|----------:|-------:|---------:|-------:|-------:|
|  0.0000 | 1988.0000 | 0.5722 |   0.5795 | 0.4939 | 0.6493 |
|  0.2500 | 3059.0000 | 0.5624 |   0.5431 | 0.4703 | 0.6442 |
|  0.5000 | 3277.0000 | 0.7019 |   0.7174 | 0.6128 | 0.8000 |
|  0.7500 | 1070.0000 | 0.7802 |   0.7979 | 0.7158 | 0.8709 |
|  1.0000 |  316.0000 | 0.9422 |   0.9490 | 0.9161 | 1.0000 |

## 3. Calibration
Linear fit on Train set:
`Predicted_Score = 0.9715 * Cosine_Similarity + -0.2652`

> [!WARNING]
> **Limitations of Linear Calibration**:
> The linear model is a global approximation. As seen in the empirical distributions, the cosine scores for "Unrelated" (0.0) and "Weak Match" (0.25) often overlap significantly. The linear fit implies a negative human score for low cosines, which is impossible. Use the calibrated score for rough guidance, but rely on the **rank** for retrieval.

## 4. Recommended Usage in APEX
Based on the validation distributions, we recommend the following retrieval prioritization bands. These are for **retrieval filtering**, not legal anticipation judgments.

| Band | Cosine Range (Approx) | APEX Action |
|---|---|---|
| **Unrelated / Noise** | < 0.47 | **Filter Out**: Likely irrelevant to the active element. |
| **Thematically Related** | 0.47 - 0.70 | **Background**: Useful for defining the field of invention but likely not anticipatory. |
| **Potentially Relevant** | 0.70 - 0.80 | **Examiner Review**: Candidate for "A" (background) or "Y" (obviousness) references. |
| **Strong Candidate** | > 0.80 | **Priority**: High probability of being an "X" (anticipatory) reference. |

> [!IMPORTANT]
> **Decision Boundary Clarification**
> Final anticipation/obviousness determinations in APEX are made exclusively by **element-level examiner reasoning** (LLM analysis), **not** by similarity score thresholds. These bands serve only to prioritize which text chunks are presented to the examiner for analysis.

