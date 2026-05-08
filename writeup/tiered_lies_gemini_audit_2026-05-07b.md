Here is a peer review of the draft writeup.

1.  **BLOCKER:** The quantitative summary of the core finding is arithmetically incorrect.
    *   Reference: §3.3 "The cross-frame inversion is the headline result"
    *   Finding: The text claims the switch from `instruct` to `verify` inverts behavior in "113 of 120 paired cells." A manual tally of regime flips (from compliance-dominant [≥1/2 override] to rejection-dominant [0/2 override], or vice-versa) in the §3.1 table shows the number is much lower, closer to 52 flips. For example, Mistral on T4 does not invert at all, and other models have several non-inverting cells. This is a significant error in reporting the magnitude of the paper's central result.

2.  **SHOULD-FIX:** The summary statistics for the `instruct_no_repeat` control group are inconsistent with the data table.
    *   Reference: §3.7 "Frame-asymmetry control..."
    *   Finding: The text claims that `instruct_no_repeat` "retains compliance-dominant override behavior in 57/60 cells." A manual count of cells with ≥1/2 override in the §3.1 table yields 52/60. The text also claims "only 3 cells flip the regime entirely" from compliance- to rejection-dominant. The data shows at least six such flips: three in Qwen×T4, two in Qwen×T2, and one in Mistral×T2. The summary appears to have inaccurately generalized from the most salient Qwen×T4 result while ignoring other changes.

3.  **SHOULD-FIX:** The claim of "full compliance" in the abstract for Llama-3.1-8B under the `verify` frame is contradicted by the data.
    *   Reference: Abstract, point (ii)
    *   Finding: The abstract states Llama has "19/20 full rejection under verify." This is correct. However, this contradicts the statement in §3.4 that Llama has "19/20 full rejection (0/2) under verify framing — one slip on T3 (`einstein_t3` at 16000 tokens, where the model parroted '1976' on one of the two probes)." One of these statements must be corrected for consistency. Given the data table, the description in §3.4 is the accurate one, and the abstract should be updated.

4.  **NIT:** The core framing of the prompt-gating mechanism could be slightly more precise.
    *   Reference: §4.1 "Compliance and derivation behave as prompt-gated modes"
    *   Finding: The sentence "Which pathway runs is fixed by which the prompt frame loads" is a powerful summary, but the paper's own excellent analysis of the Qwen×T4 case shows that for some model-task pairs, the gating is more complex, involving other template elements like the answer-binding line. While this is correctly caveated later, the initial claim could be softened (e.g., "is largely fixed," "is primarily determined by") to integrate the caveat more centrally.

5.  **NIT:** No new threats to validity were identified from the third-frame control that were not already well-addressed in §4.5. The factual and arithmetic claims in the lie design (§2.1) were checked and appear correct.
