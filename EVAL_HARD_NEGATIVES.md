# APEX Hard Negative Evaluation (Adversarial)
**Date**: 2025-12-11 19:12:43.756837
**Sample Size**: 20 Modified Claims

## 1. Retrieval Robustness
| Metric | Value | Target |
|---|---|---|
| **Robust Recall@20** | **100.00%** | > 80% |
*Can we find the original patent even when a keyword is swapped?*

## 2. Reasoning Reliability (Anti-Hallucination)
| Metric | Value | Target |
|---|---|---|
| **Hallucination Rate** | **0.00%** | 0% |
*Frequency where model claims "Anticipation" for the modified term.*

## 3. Evidence Integrity
| Metric | Value | Target |
|---|---|---|
| **Fake Quote Rate** | **0.00%** | 0% |
*Frequency where cited quote text does not exist in the source.*

## Failure Examples
| modification   | support_type   |
|----------------|----------------|

## Full Data
|    | original_id           | modification                  | retrieval_hit   | support_type   | reasoning_result   | quote_check   |
|---:|:----------------------|:------------------------------|:----------------|:---------------|:-------------------|:--------------|
|  0 | US-11570219-B2_clm_3  | \bclient\b -> server          | True            | N/A            | ERROR              | N/A           |
|  1 | US-11645301-B2_clm_10 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
|  2 | US-11601101-B2_clm_34 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
|  3 | US-12185302-B2_clm_21 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
|  4 | US-11700355-B2_clm_11 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
|  5 | US-11700052-B2_clm_14 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
|  6 | US-11698669-B2_clm_17 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
|  7 | US-11651331-B2_clm_1  | \bserver\b -> client          | True            | N/A            | ERROR              | N/A           |
|  8 | US-12185102-B2_clm_42 | \bconnected\b -> disconnected | True            | N/A            | ERROR              | N/A           |
|  9 | US-11632496-B2_clm_7  | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
| 10 | US-11570219-B2_clm_66 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
| 11 | US-12185302-B2_clm_20 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
| 12 | US-11563938-B2_clm_10 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
| 13 | US-11817099-B2_clm_23 | \bclient\b -> server          | True            | N/A            | ERROR              | N/A           |
| 14 | US-11630729-B2_clm_33 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
| 15 | US-11563568-B2_clm_9  | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
| 16 | US-11790167-B2_clm_11 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
| 17 | US-11615009-B2_clm_3  | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
| 18 | US-11611855-B2_clm_33 | \bconnected\b -> disconnected | True            | N/A            | ERROR              | N/A           |
| 19 | US-11630729-B2_clm_42 | \bplurality\b -> single       | True            | N/A            | ERROR              | N/A           |
    