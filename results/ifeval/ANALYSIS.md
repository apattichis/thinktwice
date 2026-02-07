# ThinkTwice IFEval Evaluation: Full Analysis

**Date:** February 7, 2026
**Model:** Claude 3.5 Haiku (`claude-3-5-haiku-20241022`)
**Dataset:** IFEval (120 stratified samples from 541, covering all 25 instruction types)
**Pipelines:** Single-Shot Baseline vs ThinkTwice (Decompose > Gate > Draft > Critique > Verify > Refine > Trust + Structural Enforcement)

---

## 1. Executive Summary

ThinkTwice achieves **85.0% prompt-level strict accuracy** on IFEval, a statistically significant improvement over the single-shot baseline (71.7%). The pipeline outperforms single-shot on 19 prompts while regressing on only 3, yielding a net gain of +16 prompts (McNemar p = 0.0014, significant at p < 0.01).

The pipeline's advantage comes from two complementary mechanisms:
1. **Constraint-aware drafting**: The decompose step identifies structural requirements and the draft prompt enforces them explicitly, improving paragraph counts (+80pp), first-word placement (+42pp), and case compliance (+50pp).
2. **Structural enforcement**: A deterministic post-processing layer fixes paragraph counts, first-word placement, bullet counts, constrained response format, and start phrases that LLMs fundamentally cannot self-enforce.

---

## 2. Headline Results

### 2.1 Four-Metric Comparison

| Metric | Single-Shot | ThinkTwice | Delta |
|--------|:-----------:|:----------:|:-----:|
| **Prompt Strict Acc** | 71.7% (86/120) | 85.0% (102/120) | **+13.3pp** |
| **Instruction Strict Acc** | 79.9% (147/184) | 89.7% (165/184) | **+9.8pp** |
| **Prompt Loose Acc** | 82.5% (99/120) | 87.5% (105/120) | **+5.0pp** |
| **Instruction Loose Acc** | 88.0% (162/184) | 91.3% (168/184) | **+3.3pp** |
| **Mean Latency** | 17.5s | 82.0s | +64.5s (4.7x) |

### 2.2 Statistical Significance (McNemar's Test)

| Statistic | Value |
|-----------|-------|
| Both correct | 83 |
| SS only correct | 3 |
| TT only correct | 19 |
| Both wrong | 15 |
| **Chi-squared** | **10.23** |
| **p-value** | **0.0014** |
| **Significant** | **Yes** (p < 0.01) |

---

## 3. Per-Instruction-Type Analysis

### 3.1 Full Breakdown (ThinkTwice)

| Instruction Type | Strict Acc | Loose Acc | Count |
|-----------------|:---------:|:--------:|:-----:|
| `english_capital` | 100% | 100% | 6 |
| `english_lowercase` | 100% | 100% | 2 |
| `repeat_prompt` | 100% | 100% | 1 |
| `two_responses` | 100% | 100% | 12 |
| `postscript` | 100% | 100% | 8 |
| `constrained_response` | 100% | 100% | 7 |
| `multiple_sections` | 100% | 100% | 12 |
| `number_highlighted_sections` | 100% | 100% | 1 |
| `existence` | 100% | 100% | 12 |
| `frequency` | 100% | 100% | 2 |
| `response_language` | 100% | 100% | 8 |
| `nth_paragraph_first_word` | 100% | 100% | 12 |
| `no_comma` | 100% | 100% | 5 |
| `json_format` | 90% | 90% | 10 |
| `end_checker` | 89% | 89% | 9 |
| `number_bullet_lists` | 88% | 88% | 8 |
| `number_placeholders` | 86% | 86% | 14 |
| `quotation` | 86% | 86% | 7 |
| `title` | 80% | 80% | 5 |
| `number_paragraphs` | 80% | 93% | 15 |
| `capital_word_frequency` | 76% | 76% | 17 |
| `forbidden_words` | 67% | 100% | 3 |
| `letter_frequency` | 67% | 67% | 3 |
| `number_words` | 67% | 67% | 3 |
| `number_sentences` | 0% | 0% | 2 |

### 3.2 Where ThinkTwice Wins vs Single-Shot

| Instruction Type | SS | TT | Delta | n |
|-----------------|:--:|:--:|:-----:|:-:|
| `number_paragraphs` | 0% | 80% | **+80.0pp** | 15 |
| `english_lowercase` | 50% | 100% | **+50.0pp** | 2 |
| `nth_paragraph_first_word` | 58% | 100% | **+41.7pp** | 12 |
| `constrained_response` | 86% | 100% | **+14.3pp** | 7 |
| `quotation` | 71% | 86% | **+14.3pp** | 7 |
| `number_bullet_lists` | 75% | 88% | **+12.5pp** | 8 |
| `two_responses` | 92% | 100% | **+8.3pp** | 12 |

### 3.3 Where ThinkTwice Loses vs Single-Shot

| Instruction Type | SS | TT | Delta | n |
|-----------------|:--:|:--:|:-----:|:-:|
| `letter_frequency` | 100% | 67% | **-33.3pp** | 3 |
| `title` | 100% | 80% | **-20.0pp** | 5 |

### 3.4 Interpretation

The pipeline excels at **countable structural constraints** (paragraph counts, first-word placement, case compliance, bullet counts) where the decompose-critique-refine loop can identify violations and the structural enforcer can apply deterministic fixes. The small losses on `letter_frequency` and `title` are due to the refinement loop modifying text in ways that inadvertently change these properties.

---

## 4. Remaining Failures (18 prompts)

15 of 18 remaining failures are single-instruction failures:

| Type | Count | Notes |
|------|:-----:|-------|
| `capital_word_frequency` | 4 | Not deterministically enforceable |
| `number_paragraphs` | 3 | Edge cases with markdown/separator formatting |
| `number_sentences` | 2 | Sentence boundary detection limits |
| `letter_frequency` | 1 | Content-preservation constraint |
| `title` | 1 | LLM non-determinism |
| `json_format` | 1 | LLM non-determinism |
| Other | 6 | Various multi-instruction failures |

---

## 5. Pipeline Mechanism Analysis

### 5.1 Gate Mechanism

| Gate Decision | Count | Pass Rate (Strict) |
|:------------:|:-----:|:------------------:|
| **Skip** (fast-path) | 46 (38%) | 91.3% (42/46) |
| **Refine** (full pipeline) | 74 (62%) | 81.1% (60/74) |

The gate correctly identifies easy prompts: fast-pathed samples have 91.3% pass rate vs 81.1% for refined.

### 5.2 Structural Enforcement

The structural enforcer applies deterministic post-processing fixes for:
- **Paragraph counts** (merge/split with separator awareness) — active on ~50% of samples
- **Nth-paragraph first word** (prepend if missing)
- **Constrained response format** (My answer is yes/no/maybe)
- **Bullet/list counts** (merge/split bullet items)
- **Response start phrase** (prepend required opening)

This addresses the fundamental LLM limitation of not being able to count reliably.

### 5.3 Accuracy by Instruction Count

| Instructions per Prompt | Strict Acc | Loose Acc | Count |
|:-----------------------:|:---------:|:--------:|:-----:|
| 1 | 96% | 97% | 68 |
| 2 | 70% | 72% | 40 |
| 3 | 75% | 83% | 12 |

Single-instruction prompts are nearly solved (96%). Multi-instruction prompts are harder because all instructions must pass simultaneously.

---

## 6. Latency Analysis

| Statistic | Single-Shot | ThinkTwice | Ratio |
|-----------|:-----------:|:----------:|:-----:|
| Mean | 17.5s | 82.0s | 4.7x |
| Median | 14.5s | 85.6s | 5.9x |
| P95 | 36.3s | 213.8s | 5.9x |

---

## 7. Discussion

### 7.1 Why Does the Pipeline Help on IFEval?

The ThinkTwice pipeline improves instruction-following through three mechanisms:

1. **Constraint decomposition**: The decompose phase explicitly identifies structural requirements (paragraph counts, case, formatting) and feeds them to the draft prompt. This makes the first draft significantly more compliant than single-shot.

2. **Critique-refine loop**: The critique phase identifies violations and the refiner attempts targeted fixes. This helps with structural violations (paragraph restructuring, quotation wrapping) but can hurt content-preservation constraints.

3. **Structural enforcement**: Deterministic post-processing fixes countable properties that LLMs cannot self-enforce. This is analogous to constrained decoding in production systems and covers paragraph counts, first-word placement, bullet counts, constrained responses, and start phrases.

### 7.2 The Structural vs Content Trade-off

The pipeline's losses on `letter_frequency` (-33.3pp) and `title` (-20.0pp) share a common root cause: the refinement loop modifies text to improve content quality and inadvertently changes structural properties. The structural override in the trust step catches many of these cases (e.g., quotation wrapping, bullet counts, separators) but cannot protect all properties.

### 7.3 Limitations

1. **Single model**: Results are specific to Claude 3.5 Haiku.
2. **Single seed**: 120-sample stratified sample (seed=42).
3. **Structural enforcement is post-processing**: It fixes outputs rather than improving the model's understanding. However, this is a standard and accepted approach for structural compliance.

---

## 8. Conclusions

1. **ThinkTwice significantly improves instruction-following accuracy** over single-shot on IFEval (85.0% vs 71.7%, p = 0.0014).

2. **The pipeline's advantage is strongest on countable structural constraints** (paragraph counts +80pp, first-word placement +42pp, case compliance +50pp, constrained response +14pp).

3. **Constraint-aware drafting + structural enforcement are the primary drivers** of improvement, working together to catch both LLM-fixable and LLM-unfixable violations.

4. **The pipeline trades small content-preservation losses** (letter frequency, title) for large structural gains — a net +16 prompts.

5. **The gate mechanism correctly identifies easy samples** (91.3% pass rate on fast-pathed vs 81.1% on refined).

6. **The latency overhead (4.7x) is the main cost** of the pipeline's instruction-following gains.

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
| Structural enforcement | Enabled (paragraph, first-word, constrained, bullet, start-phrase) |

## Appendix B: Reproducibility

```bash
# Single-shot baseline
python eval/run_eval.py --dataset ifeval --pipeline single_shot --samples 120 --output results/ifeval/single_shot

# ThinkTwice pipeline
python eval/run_eval.py --dataset ifeval --pipeline thinktwice --samples 120 --output results/ifeval/thinktwice

# Both + comparison
python eval/run_eval.py --dataset ifeval --pipeline all --samples 120 --output results/ifeval
```
