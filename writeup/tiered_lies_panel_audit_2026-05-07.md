# DET tiered_lies — frontier-model audit panel (2026-05-07)

Panel: GPT-4.1, Gemini-2.5-Pro, DeepSeek-R1.
Total OR spend: $0.092 ($0.033 + $0.043 + $0.015).

## Per-model results

### openai/gpt-4.1
_elapsed: 26.0s — completion 1651, reasoning_tokens (hidden) 0, cost $0.0334_

Here is a careful, skeptical peer review focusing on the specific concerns you raised:

---

**1. [BLOCKER] [SECTION: §4.1]**
quoted line: "The simplest model consistent with the data is two distinct behavioral pathways with prompt framing as the gate."
issue: The evidence presented (behavioral regime flips under prompt framing) does not justify the claim that there are two distinct *pathways* in any meaningful sense beyond observed behavior. The data are fully consistent with a single computation whose output is highly sensitive to prompt wording, without any necessity to posit discrete, switchable "pathways." The language risks overreach and could mislead readers into inferring a mechanistic or architectural separation that is not supported by the behavioral-only evidence.
suggested fix: Rephrase to clarify that "compliance" and "derivation" are *behavioral patterns* induced by prompt framing, not evidence of distinct computational pathways. Explicitly state that the observed inversion is compatible with a highly prompt-sensitive but unified computation, and that the "pathway" terminology is strictly descriptive.

---

**2. [SHOULD-FIX] [SECTION: §3.1 Table]**
quoted line: Table of override counts by tier, model, frame, and context length.
issue: Cell counts for regime flips and compliance/rejection-dominant cells do not fully reproduce from the table as described in the text. For example, the text claims "44 of 60 model-checkpoint cells" flip regime on frame inversion, but a careful tally (by row and frame) yields 43, not 44. Similarly, the instruct_no_repeat regime-flip count (6 cells) and amplitude-shift count (7) are not transparently reproducible from the table as formatted. This undermines confidence in the summary statistics and the override metric's application.
suggested fix: Provide a supplementary table or appendix with explicit cell-by-cell regime assignments and regime-flip tallies, or annotate the main table to make regime boundaries and flips auditable. Double-check all summary counts for consistency with the table.

---

**3. [SHOULD-FIX] [SECTION: §3.7, §4.1]**
quoted line: "The Qwen×T4 result is a third behavioral mode, narrowly localised to one model × one tier."
issue: The claim of a "third behavioral mode" is grandiose relative to the evidence: n=2 probes, 1 model, 1 tier, and only a handful of regime flips. This is more parsimoniously described as a local interaction or outlier, not a robustly identified "mode." The current framing risks overinterpreting a small-sample, model-specific anomaly.
suggested fix: Downgrade the language to describe this as a "localized exception" or "model-tier-specific interaction." Emphasize the limited scope and sample size, and avoid suggesting a generalizable third mode without further evidence.

---

**4. [SHOULD-FIX] [SECTION: §4.2]**
quoted line: "The present result constrains the cognitive reading... Whatever produces the surge-and-decay is therefore not tracking an evaluation-of-content stage — at least not under instruction framing."
issue: The pushback against content-evaluating interpretations of the prior surge-and-decay is overstated. The current experiment only tests the *instruction* and *verify* framings, and only on a new, harder lie set. It does not directly test the surge-and-decay phenomenon or its underlying mechanism. The claim that the new results "constrain" the cognitive reading of the old surge is a stretch: the lack of evaluation under instruction framing here does not rule out content evaluation as a factor in the prior surge, especially since model, context, and prompt details differ.
suggested fix: Soften the language to clarify that the present results are *consistent* with a pattern-persistence reading but do not *rule out* content-evaluation mechanisms in the prior surge-and-decay. Suggest that further experiments (e.g., running the same prompt manipulations on the original surge models) are needed for a definitive link.

---

**5. [SHOULD-FIX] [SECTION: §3.6, §4.3]**
quoted line: "The capability ceiling is the more parsimonious interpretation: Mistral's instruction tuning may not include enough chained-inference verification training to fight a high-confidence planted assertion, while Qwen and Llama at comparable parameter scale do."
issue: The interpretation that Mistral's failure to reject T4 lies under verify framing is due to a "capability ceiling" is plausible but not uniquely supported. An alternative explanation — that Mistral's instruction tuning causes it to ignore or mishandle the verify prompt (i.e., prompt misalignment rather than lack of capability) — is not ruled out. The paper acknowledges this but still presents the capability ceiling as preferred without sufficient justification.
suggested fix: Present both interpretations (capability ceiling vs. prompt misalignment) as equally plausible, and explicitly state that the current data do not distinguish between them. Suggest targeted follow-up experiments (e.g., prompt engineering, instruction-tuning analysis) to discriminate.

---

**6. [SHOULD-FIX] [SECTION: §3.1, §4.5]**
quoted line: "Two probes per tier per frame is small. Cross-tier and cross-frame comparisons should be read as suggestive, not statistically tight."
issue: Despite this caveat, the main text repeatedly draws strong cross-tier and cross-model conclusions (e.g., "Llama is the cleanest two-mode case," "Qwen has residual compliance bleed," "Mistral exposes a capability ceiling") based on n=2 per cell. This is not statistically robust, and the risk of overfitting to probe idiosyncrasies is high.
suggested fix: Further temper all cross-tier and cross-model claims, explicitly flagging them as preliminary and hypothesis-generating rather than conclusive. Consider collapsing some claims to the aggregate (e.g., "in this sample, Llama shows the cleanest inversion") and recommend replication with larger probe sets.

---

**7. [SHOULD-FIX] [SECTION: §4, §4.5]**
quoted line: "We use 'compliance' and 'derivation' as labels for behavioral regimes only — no mechanistic-circuit identification is claimed."
issue: Despite this disclaimer, the repeated use of "pathway," "circuit," and "gating" language throughout the results and discussion sections risks sneaking in a mechanistic interpretation by implication. This is especially problematic given the lack of mechanistic interventions.
suggested fix: Scrub the text for language that implies mechanism (e.g., "circuit," "pathway," "routing," "gate") and replace with strictly behavioral descriptors (e.g., "pattern," "regime," "response type"). Reiterate in every section that these are observed behaviors, not inferred mechanisms.

---

**8. [SHOULD-FIX] [SECTION: §2.4, §4.5]**
quoted line: "An override is counted when with_anchor.fidelity_hits ≥ 1 AND with_anchor.fidelity_hits > without_anchor.fidelity_hits."
issue: The override metric relies on keyword matches, which can conflate surface-form overlap with true semantic agreement. For example, Mistral's "30,000 feet" matching "30,000" as fidelity for everest_height_t2 may not indicate parroting the planted lie, but rather restating a common Everest height fact. This risks misclassifying correct answers as compliance or vice versa.
suggested fix: Add a more nuanced analysis of fidelity matches, especially for numeric and ambiguous probes. Consider supplementing with human judgment or semantic similarity metrics, and explicitly discuss this limitation in the main text, not just in the limits section.

---

**No further major or minor concerns.** The writeup is otherwise clear, well-motivated, and transparent about its limitations.

---

### google/gemini-2.5-pro
_elapsed: 27.8s — completion 2996, reasoning_tokens (hidden) 2879, cost $0.0430_

Thank you for the opportunity to review this draft. The experimental design is strong, and the results are intriguing. My feedback focuses on areas where the claims may overreach the evidence, where interpretations could be strengthened by considering alternatives more directly, or where the methodology has subtle but important limitations.

---

[1] [SHOULD-FIX] [SECTION: §4.1]
quoted line: "The simplest model consistent with the data is two distinct behavioral pathways with prompt framing as the gate. The compliance pathway lifts asserted material forward without auditing it. The derivation pathway evaluates the

---

### deepseek/deepseek-r1
_elapsed: 103.7s — completion 3000, reasoning_tokens (hidden) 2351, cost $0.0145_

_(no visible content — model exhausted output budget on hidden reasoning tokens)_

---

