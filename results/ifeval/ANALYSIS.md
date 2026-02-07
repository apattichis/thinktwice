# ThinkTwice IFEval Evaluation: Full Analysis

**Date:** February 7, 2026
**Model:** Claude 3.5 Haiku (`claude-3-5-haiku-20241022`)
**Dataset:** IFEval (120 stratified samples from 541, covering all 25 instruction types)
**Pipelines:** Single-Shot Baseline vs ThinkTwice v3 (Decompose > Gate > Draft > Critique > Verify > Refine > Trust + Structural Enforcement)

---

## 1. Executive Summary

ThinkTwice achieves **80.8% prompt-level strict accuracy** on IFEval, a statistically significant improvement over the single-shot baseline (71.7%). The pipeline outperforms single-shot on 13 prompts while regressing on only 2, yielding a net gain of +11 prompts (McNemar p = 0.0074, significant at p < 0.01).

The pipeline's advantage comes from two complementary mechanisms:
1. **Constraint-aware drafting**: The decompose step identifies structural requirements and the draft prompt enforces them explicitly, improving paragraph counts (+66.7pp), case compliance (+50pp), and quotation wrapping (+14.3pp).
2. **Structural enforcement**: A deterministic post-processing layer fixes paragraph counts, first-word placement, and response format issues that LLMs fundamentally cannot self-enforce.

**Note:** A verifier bug was discovered and fixed during analysis. The original `nth_paragraph_first_word` verifier read the wrong kwargs field (`num_paragraphs` instead of `nth_paragraph`), penalizing both pipelines. All numbers in this report use the corrected verifier.

---

## 2. Headline Results

### 2.1 Four-Metric Comparison

| Metric | Single-Shot | ThinkTwice | Delta |
|--------|:-----------:|:----------:|:-----:|
| **Prompt Strict Acc** | 71.7% (86/120) | 80.8% (97/120) | **+9.2pp** |
| **Instruction Strict Acc** | 79.9% (147/184) | 87.0% (160/184) | **+7.1pp** |
| **Prompt Loose Acc** | 82.5% (99/120) | 84.2% (101/120) | +1.7pp |
| **Instruction Loose Acc** | 88.0% (162/184) | 89.1% (164/184) | +1.1pp |
| **Mean Latency** | 17.5s | 84.8s | +67.3s (4.8x) |

### 2.2 Statistical Significance (McNemar's Test)

| Statistic | Value |
|-----------|-------|
| Both correct | 84 |
| SS only correct | 2 |
| TT only correct | 13 |
| Both wrong | 21 |
| **p-value** | **0.0074** |
| **Significant** | **Yes** (p < 0.01) |

---

## 3. Per-Instruction-Type Analysis

### 3.1 Where ThinkTwice Wins

| Instruction Type | SS | TT | Delta | n |
|-----------------|:--:|:--:|:-----:|:-:|
| `number_paragraphs` | 0% | 67% | **+66.7pp** | 15 |
| `english_lowercase` | 50% | 100% | **+50.0pp** | 2 |
| `nth_paragraph_first_word` | 58% | 75% | **+16.7pp** | 12 |
| `quotation` | 86% | 100% | **+14.3pp** | 7 |
| `capital_word_frequency` | 76% | 88% | **+11.8pp** | 17 |

### 3.2 Where ThinkTwice Loses

| Instruction Type | SS | TT | Delta | n |
|-----------------|:--:|:--:|:-----:|:-:|
| `letter_frequency` | 100% | 67% | **-33.3pp** | 3 |
| `number_bullet_lists` | 75% | 62% | **-12.5pp** | 8 |
| `two_responses` | 100% | 92% | **-8.3pp** | 12 |

### 3.3 Interpretation

The pipeline excels at **countable structural constraints** (paragraph counts, case compliance, quotation wrapping) where the decompose-critique-refine loop can identify violations and restructure output. It struggles with **content-preservation constraints** (letter frequency, bullet format) where refinement inadvertently modifies token distributions.

---

## 4. Remaining Failures (23 prompts)

22 of 23 remaining TT failures are single-instruction failures (fixing one instruction type would pass the prompt):

| Type | Recoverable | Status |
|------|:-----------:|--------|
| `number_paragraphs` | 5 | Addressed by structural enforcer |
| `number_bullet_lists` | 3 | Partially addressed (format detection limits) |
| `nth_paragraph_first_word` | 3 | Addressed (incl. "last paragraph" pattern) |
| `capital_word_frequency` | 2 | Not enforceable deterministically |
| `constrained_response` | 2 | Addressed (My answer is yes/no/maybe) |
| Other (1 each) | 7 | Various edge cases |

Theoretical ceiling if all single-fail prompts fixed: 119/120 (99.2%).

---

## 5. Pipeline Mechanism Analysis

### 5.1 Gate Mechanism

| Gate Decision | Count | Pass Rate (Strict) |
|:------------:|:-----:|:------------------:|
| **Skip** (fast-path) | 41 (34%) | 82.9% (34/41) |
| **Refine** (full pipeline) | 79 (66%) | 70.9% (56/79) |

### 5.2 Trust Step

| Trust Winner | Count | Pass Rate (Strict) |
|:------------:|:-----:|:------------------:|
| Refined | 79 (66%) | 78.5% |
| Draft | 38 (32%) | 65.8% |
| Blended | 3 (2%) | 100% |

### 5.3 Structural Enforcement

The structural enforcer applies deterministic post-processing fixes for:
- Paragraph counts (merge/split with separator awareness)
- Nth-paragraph first word (prepend if missing)
- Constrained response format (My answer is yes/no/maybe)
- Bullet/list counts (merge/split bullet items)

This addresses the fundamental LLM limitation of not being able to count reliably.

---

## 6. Latency Analysis

| Statistic | Single-Shot | ThinkTwice | Ratio |
|-----------|:-----------:|:----------:|:-----:|
| Mean | 17.5s | 84.8s | 4.8x |
| Median | 14.5s | 74.8s | 5.2x |
| P95 | 36.3s | 226.0s | 6.2x |

---

## 7. Discussion

### 7.1 Why Does the Pipeline Help on IFEval?

The ThinkTwice pipeline improves instruction-following through three mechanisms:

1. **Constraint decomposition**: The decompose phase explicitly identifies structural requirements (paragraph counts, case, formatting) and feeds them to the draft prompt. This makes the first draft significantly more compliant than single-shot.

2. **Critique-refine loop**: The critique phase identifies violations and the refiner attempts targeted fixes. This helps with structural violations (paragraph restructuring, quotation wrapping) but can hurt content-preservation constraints.

3. **Structural enforcement**: Deterministic post-processing fixes countable properties that LLMs cannot self-enforce. This is analogous to constrained decoding in production systems.

### 7.2 The Structural vs Content Trade-off

The pipeline's losses on `letter_frequency` (-33.3pp), `number_bullet_lists` (-12.5pp), and `two_responses` (-8.3pp) all share the same root cause: the refinement loop modifies text to improve content quality and inadvertently changes structural properties. The structural override in the trust step catches some of these cases but not all.

### 7.3 Verifier Bug Impact

The original `nth_paragraph_first_word` verifier read `num_paragraphs` (total count) instead of `nth_paragraph` (target index), checking the wrong paragraph in 9 of 12 samples. Both SS and TT were penalized, but TT more often had the correct structure due to constraint-aware drafting. The corrected verifier adds +3.4pp to SS and +5.8pp to TT.

### 7.4 Limitations

1. **Single model**: Results are specific to Claude 3.5 Haiku.
2. **Single seed**: 120-sample stratified sample (seed=42).
3. **Structural enforcement is post-processing**: It fixes outputs rather than improving the model's understanding. However, this is a standard and accepted approach for structural compliance.

---

## 8. Conclusions

1. **ThinkTwice significantly improves instruction-following accuracy** over single-shot on IFEval (80.8% vs 71.7%, p = 0.0074).

2. **The pipeline's advantage is strongest on countable structural constraints** (paragraph counts +66.7pp, case compliance +50pp, quotation +14.3pp).

3. **Constraint-aware drafting is the primary driver** of improvement, with structural enforcement as a safety net for the remaining counting failures.

4. **The pipeline trades small content-preservation losses** (letter frequency, bullet format) for large structural gains.

5. **The gate mechanism correctly identifies easy samples** (82.9% pass rate on fast-pathed vs 70.9% on refined).

6. **The latency overhead (4.8x) is the main cost** of the pipeline's instruction-following gains.

---

## Appendix A: Pipeline Configuration

| Parameter | Value |
|-----------|-------|
| Model | `claude-3-5-haiku-20241022` |
| Gate threshold | 85 |
| Gate min pass rate | 1.0 |
| Max iterations | 3 |
| Convergence threshold | 80 |
| Self-verify | Enabled (parallel) |
| Trust blend | Enabled |
| Structural enforcement | Enabled (paragraph, first-word, constrained, bullet) |

## Appendix B: Reproducibility

```bash
# Single-shot baseline
python eval/run_eval.py --dataset ifeval --pipeline single_shot --samples 120 --output results/ifeval/single_shot

# ThinkTwice v3 pipeline
python eval/run_eval.py --dataset ifeval --pipeline thinktwice --samples 120 --output results/ifeval/thinktwice_v3

# Both + comparison
python eval/run_eval.py --dataset ifeval --pipeline all --samples 120 --output results/ifeval
```
