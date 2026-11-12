# Fable audit issues — revision d430d75

**Status: run r1 consolidated (audit, verification, and completeness round 1 complete; no Critical/High entries, so no spot-checks are required) · Issues: 83 · Open: 83 · Resolved: 0 · By importance: Critical 0 · High 0 · Medium 3 · Low 70 · Presentation 10**

**Last updated:** November 10, 2026

This register records the independent Fable audit of "High-Dimensional Dynamics of Self-Training with Confidence Selection and Data Reuse" (Cattaneo, Klusowski, Rioual) at Overleaf commit `d430d75` (November 5, 2026): abstract, Sections 1–5, Appendices A–E, Figures 1–2, and the cited bibliography, together with the companion code repository `HighDimensionalDynamicsOfSelfTraining` at commit `e823bf3` (November 5, 2026). It is shared with the coauthors through Overleaf. The supporting evidence (protocol, inventory, auditor reports, verifier verdicts, scratch computations, and the consolidation notes mapping finding IDs to register IDs) is kept in the audit folder `2026-11-10 AUDIT-Fable/` at the project root, outside Overleaf; paths below such as `runs/r1/reports/M4.unit.md` are relative to that folder. The manuscript sources were not changed during the audit.

Locations refer to the audited commit `d430d75` (snapshot lines; the files are those of the Overleaf repository at that commit) and to page numbers printed in its PDF; for this paper the printed page equals the PDF page (the title page is page 1). File keys are the `.tex` stems (`setting` = `setting.tex`, `proof-mean-field` = `proof-mean-field.tex`, and so on; `main` = `main.tex`, `references` = `references.bib`). Code locations are files and lines at `e823bf3`. Results are named by printed number and label; note that assumptions have their own counter, so Assumption 4.1 and Proposition 4.1 are different objects. Importance levels are Critical, High, Medium, Low, and Presentation. States follow the research-wide review standard (Open, In progress, Pending author review, Approved/cleanup pending, Resolved, Deferred, Rejected/unsupported).

**Headline result of run r1.** No theorem, proposition, corollary, or lemma of the paper was found false, and no proof was found to need a new argument; no finding is rated Critical or High. Every live proof (Appendices A–E) was checked line by line by a Fable proof auditor, and two Fable chain audits traced Theorem 4.7, Corollary 4.8, Proposition 4.9, Theorem 4.10, and Corollary 4.11 to their appendix sources. The three Medium items are: the hypothesis list of Theorem 4.7 and Proposition B.4 cites display (6) instead of Assumption 3.1 and so omits $\bar\rho\in(0,1)$, which Definition 4.6 needs, and every result stated "under the hypotheses of Theorem 4.7" inherits the omission (F01); the "Selected fraction" panel of Figure 1 plots $\omega^{t-1}$ with an artificial $0$ at $t=0$, a convention of the plotting code (F02); and the Section 5.3 sentences on fixing the intercept and on labeled-only intercept updates rest on experiments that are not displayed, with an independent simulation showing that holding the intercept at its initial value $0$, the only value the paper defines, makes the error worse (F03). The **code check** found that the finite-dimensional code implements Algorithm 3.2 exactly, that the particle effective process is an exact reformulation of Definition 4.6, that the captions match the notebook configurations, and that both figures are reproduced pixel-identically by the unchanged notebooks (154 tests pass). An **independent implementation written from the paper alone** confirmed Definition 4.6 against Algorithm 3.2 in eight regimes (errors shrinking roughly like $d^{-1/2}$) and confirmed Proposition 5.3; an analytic check showed that Definition 4.6 reduces at $\pi=0$ to known DMFT systems; and a long-time simulation found the hypotheses of Theorem 4.10 nonvacuous, the effective process stabilizing as Corollary 4.11 asserts, and $T_{\mathrm{id}}$ growing with $d$ as Proposition 4.9 predicts. The Low entries are one- or two-sentence gaps whose conclusions stand (F05, F09–F13, F15, F17, F23, F28, F30), hypothesis and statement mismatches (F04, F08, F16, F21, F29), optional strengthenings (F06–F07, F14, F18–F20, F22, F24–F27, F31), figure, code, and Section 5.3 interpretation points (F32–F37), front matter (F38–F43), positioning and literature (F44–F52), notation (F53–F55), sources and bibliography (F56–F59), and a streamlining group (F60–F73) listing assumptions, clauses, results, displays, and notation that no proof uses. Presentation entries F74–F83 collect wording, notation, cross-reference, and formatting points; F77–F83 are single-check.

**Reading the entries.** "Type" uses the protocol categories (error, gap, unverified-source, inconsistency, overclaim, redundancy, presentation, improvement). "Established" means the finding was confirmed by at least one independent verifier (verdict `confirmed` or `confirmed-with-changes`; corrections made by verifiers are incorporated into the entry). "Single-check" means a Presentation finding seen by one auditor and not separately verified, which the protocol allows only as Presentation/Low items. A *gap* entry means the conclusion is true but a step is not written to the standard of a hostile referee; a *redundancy* entry means the object is correct but unused, duplicated, or implied, so removing it is an author choice, not a correction; an *improvement* entry is an optional strengthening or simplification. Proposed repairs are minimal; following the research-wide standard, any manuscript change would be proposed in red for author review. Each entry's verification field lists every contributing finding ID (reports in `runs/r1/reports/<ITEM>.<lens>.md`, verdicts in `runs/r1/verify/`). The version audited, the items, the models, and what remains unchecked are summarized under [Scope and method](#scope-and-method) at the end.

| ID | Issue | Importance | Type | Location | Brief description | State | resolved? |
|---|---|---|---|---|---|---|---|
| F01 | [Theorem 4.7 and Proposition B.4 cite display (6) instead of Assumption 3.1, omitting ρ̄ ∈ (0,1)](#issue-f01) | Medium | inconsistency | mean-field 431–434, p. 12; proof-mean-field 684–687, p. 30 | Definition 4.6 divides by ρ̄ and 1−ρ̄; with ρ̄ ∈ {0,1}, which display (6) allows, it is undefined. Inherited by Corollary 4.8, Lemma B.1, Theorem 4.10, Corollary 4.11, Propositions 5.2–5.3. | Open | no |
| F02 | [Figure 1's "Selected fraction ω^t" panel plots ω^{t−1}, with an artificial 0 at t = 0](#issue-f02) | Medium | inconsistency (paper–code) | numerical 28–42, p. 15; code src/callbacks.py 280–285, figures/experiments.py 213 | Both curves are shifted by one step; the true ω⁰ ≈ 0.166 exceeds the plotted e⁰ ≈ 0.083, while the plot shows ω⁰ = 0 < e⁰. | Open | no |
| F03 | [Section 5.3 intervention claims (fixed intercept, labeled-only intercept) are undisplayed; "fixing the intercept improves" is false at b = 0](#issue-f03) | Medium | overclaim | numerical 239–241, p. 17 | No value, configuration, metric, or result is given; simulation: intercept held at 0 ends at error ≈ 0.256 vs 0.199; labeled-only updates help (0.158) but are not shown. | Open | no |
| F04 | [Sign conventions for λ, π disagree across Section 3, Algorithm 3.2, Section 4.2, and individual results](#issue-f04) | Low | inconsistency | setting 160, 218, pp. 6–7; mean-field 111–112, p. 10; finite-dim 186, p. 8 | Section 3 fixes λ, π > 0; Section 4.2 allows λ, π ≥ 0; Proposition 4.3 and Lemma A.1 use other ranges; Theorem 4.7 refers to an algorithm defined only for λ, π > 0. | Open | no |
| F05 | [Upper Hessian bound ∇²L_c ⪯ H_d is asserted and used but not proved](#issue-f05) | Low | gap | finite-dim 236–240, p. 9; proof-finite-dim 483–489, p. 25 | One line from ℓ'' ≤ L_ℓ, j'' ≤ L_j, π ≥ 0; it enters the rate in Theorem 4.4. | Open | no |
| F06 | [Remark 4.5 can be stated exactly and should name the configuration](#issue-f06) | Low | improvement | finite-dim 286–291, p. 9 | G(θ*_c) = 0 iff θ*_c ∈ Θ_c for the identified c; the boundary case occurs. | Open | no |
| F07 | [Geometric rate in Theorem 4.4 holds from T_id; t₀ is unnecessary](#issue-f07) | Low | improvement | finite-dim 273–280, p. 9; proof-finite-dim 490–517, p. 25 | Contraction on the compact convex hull of the tail gives the rate directly. | Open | no |
| F08 | [T_id is "some time" in Theorem 4.4 and Lemma A.2 but "the first time" in Proposition 4.9](#issue-f08) | Low | inconsistency | finite-dim 260–266, p. 9; proof-finite-dim 296–303, p. 24; long-time-behavior 34–44, p. 13 | One symbol names an existential time and a specific random time. | Open | no |
| F09 | [Conditional-law notation =^d_G is used from Proposition B.4 on but defined only in passing in Lemma B.6](#issue-f09) | Low | presentation | proof-mean-field 708, p. 30; 1271–1272, p. 33 | No formal definition (a.s. equality of regular conditional laws on an extension) before first use. | Open | no |
| F10 | [Proposition B.8: passage from Lemma B.7 (deterministic directions) to history-measurable directions is asserted in one sentence](#issue-f10) | Low | gap | proof-mean-field 1883–1892, p. 38 | True (written out and checked by the auditor); needs a jointly measurable kernel and two-stage conditioning. | Open | no |
| F11 | [Lemma B.6 step 4 uses disintegration without saying so](#issue-f11) | Low | gap | proof-mean-field 1523–1552, p. 35 | The middle equality of the displayed chain is the claim; one citation closes it. | Open | no |
| F12 | [Subsequence arguments in Lemmas B.5–B.6 need all dimensions on one probability space](#issue-f12) | Low | gap | proof-mean-field 1037–1056, 1416–1430, pp. 32–34 | True since hypotheses and conclusions depend only on marginal laws; one sentence. | Open | no |
| F13 | [Lemmas B.5–B.6 are indexed by row count, but sample-side arrays have n(d) rows](#issue-f13) | Low | gap | proof-mean-field 933–955, 1234–1244, pp. 31, 33 | n(d) need not be injective; the proofs do not use the indexing. | Open | no |
| F14 | [Facts established inside the proof of Lemma B.1 are invoked later as part of its statement](#issue-f14) | Low | improvement | proof-mean-field 73–103, 176–191, 337–349, pp. 26–28; uses at 2374–2391, 2760–2767, proof-long-time 80–92 | One-step forms and fresh-noise representations are not in the statement. | Open | no |
| F15 | [Remark after Theorem 4.7 cites the deterministic Proposition E.4 for a convergence in probability](#issue-f15) | Low | gap | mean-field 475–477, p. 12; also 11–13, p. 9 | The applicable statement is Corollary E.7 (never cited); "2-pseudo-Lipschitz" has no pointer to Definition E.3. | Open | no |
| F16 | [Claims proved elsewhere cite the wrong result or none (atomlessness, τ̄^t > 0, well-definedness)](#issue-f16) | Low | inconsistency | proof-mean-field 3003–3004, p. 45; mean-field 181–185, 502–510, pp. 11–12 | Atomlessness is Lemma B.1, not Theorem 4.7; Definition 4.6's well-definedness holds only under Theorem 4.7's hypotheses. | Open | no |
| F17 | [Appendix E states nontrivial facts without proof or pinpoint source](#issue-f17) | Low | gap / unverified-source | mathematical-preliminaries 7, 51–145, 213–218, pp. 58–60 | Proposition E.4 item 4 and Lemma E.5 (p > 1) are not in Villani Ch. 6; the random case of Corollary E.7 needs the subsequence criterion. All true. | Open | no |
| F18 | [Theorem 4.7 uses only continuity and linear growth of ℓ'(y,·) and j'](#issue-f18) | Low | improvement | mean-field 48–64, p. 10 | No step compares ℓ' or j' at two points. | Open | no |
| F19 | [Gram systems of Definition 4.6 become numerically singular; a pseudo-inverse solve is needed in practice](#issue-f19) | Low | improvement | mean-field 181–183, 193–261, p. 11; numerical 17–22, p. 15 | cond(C^[w]) reaches 10¹⁰–10¹⁶; a literal solve fails at π = 0. | Open | no |
| F20 | [Initialization assumptions exclude warm starts and zero initialization; roles of assumptions not discussed](#issue-f20) | Low | improvement | mean-field 65–107, p. 10 | Assumption 4.3(iii) is structural; a teacher fitted on D_L is data-dependent and outside the proof. | Open | no |
| F21 | [Corollary 4.11's last identity is claimed P̃-a.s., but Theorem 4.10 fixes c̃^∞ only P̃_U-a.s.](#issue-f21) | Low | inconsistency | long-time-behavior 237–251, p. 15; proof-long-time 1194–1212, 1284–1291, p. 55 | On labeled observations the identity holds only by an extension chosen inside the proof. | Open | no |
| F22 | [Atom condition in Corollary 4.11 is stronger than the proof needs](#issue-f22) | Low | improvement | long-time-behavior 237–251, p. 15 | The identity holds iff P̃_U(c̃^∞ = 0, r̃^∞ ∈ {κ±}) = 0. | Open | no |
| F23 | [Limit (117) of the two-time switching indicator is asserted without citing the lemmas that justify it](#issue-f23) | Low | gap | proof-long-time 46–68, p. 47 | Needs Lemma B.1 (no atoms) and Lemma B.5 part 2; carries Proposition 4.9, Proposition C.3, Lemma C.5. | Open | no |
| F24 | [Proposition C.3 and the stabilization conclusions use fewer hypotheses than stated](#issue-f24) | Low | improvement | proof-long-time 124–125, 319–567, pp. 47–51; long-time-behavior 139–236, pp. 14–15 | Stabilization of the configuration needs neither Assumption 4.4 nor λ > 0 nor p̄_L ∈ (0,1). | Open | no |
| F25 | [Long-time step-size condition is valid but about three times conservative](#issue-f25) | Low | improvement | long-time-behavior 110–137, p. 14 | Λ_bd ≈ 7.9–11 against Λ_d ≈ 2.7–3.9 in simulated configurations. | Open | no |
| F26 | [Restrictions to t ≥ 1 in Proposition 4.9, (115)–(117), and Proposition C.2 are unnecessary](#issue-f26) | Low | improvement | long-time-behavior 46–49, p. 13; proof-long-time 37–205, pp. 46–48 | Each holds for t ≥ 0 with the same proof. | Open | no |
| F27 | [Long-time limit is not characterized; no rate; convergence of the error not stated](#issue-f27) | Low | improvement | long-time-behavior 139–252, pp. 14–15; introduction 91–92, p. 2 | Error convergence holds whenever τ̄^∞ > 0 (unproved); the limit interchange is open. | Open | no |
| F28 | [Proposition 5.1 states no standing hypotheses and does not name the quantity whose limit it asserts](#issue-f28) | Low | gap | numerical 84–120, p. 16; proof-numerical 71, p. 56 | The proof uses Assumption 3.1 (p → p̄ ∈ (0,1), s_μ → s̄_μ). | Open | no |
| F29 | [Proof of Proposition 5.1 proves an extra claim, while nonnegativity of the alignment regret has no stated reason](#issue-f29) | Low | inconsistency | proof-numerical 16–39, p. 56; numerical 156, p. 16 | The middle paragraph is exactly what makes the alignment regret nonnegative. | Open | no |
| F30 | [Finite-dimensional regret decomposition omits its conditions and the identity it rests on](#issue-f30) | Low | gap | numerical 68–70, 169–181, p. 16 | Needs s_μ > 0, p ∈ (0,1), and the exact identity E^t = E_p(α^t, β^t) from the proof of Corollary 4.8. | Open | no |
| F31 | [The hypothesis s̄_μ > 0 can be removed from Proposition 5.1 and the regret definitions](#issue-f31) | Low | improvement | numerical 95, 107–118, 140, p. 16 | The Bayes error is E^opt_p(s_μ/σ), continuous in (p, α). | Open | no |
| F32 | [Finite selected-error fraction e^t in Figure 1 is undefined; caption symbols and runs unexplained](#issue-f32) | Low | inconsistency | numerical 28–42, p. 15; code src/callbacks.py 273–278 | e^t is computed unconditionally on selection, matching ē^t of Corollary 4.11; no finite definition or convergence statement. | Open | no |
| F33 | [Code draws labels and supervision indicators i.i.d. and evaluates errors at the configured p](#issue-f33) | Low | inconsistency (paper–code) | numerical 36–37, 196–197, pp. 15, 17; code src/environment.py 125–132 | No visible effect (deviation O(n^{−1/2})); captions read as exact proportions. | Open | no |
| F34 | [Code documentation reuses the paper's residual symbols under a −η convention and cites a nonexistent manuscript section](#issue-f34) | Low | inconsistency (paper–code) | code docs/effective_process.md 6–7, 79–249 | Code g, p, χ equal −η times the paper's; no conversion table. | Open | no |
| F35 | [Figure 1 is cited as the "accompanying evolution" of the Figure 2 run but uses another configuration; the normalized intercept is shown nowhere](#issue-f35) | Low | inconsistency | numerical 220–225, p. 17 | The overshoot is real (β^T ≈ 1.6 β⋆ in simulation) but not displayed. | Open | no |
| F36 | [Intercept-feedback explanation omits that most of the late error rise in Figure 2 is alignment regret](#issue-f36) | Low | overclaim | numerical 220–231, p. 17 | Of the rise after t ≈ 88, about 89% is alignment regret; intercept regret drives only the early rise. | Open | no |
| F37 | [General empirical statements in Section 5.3 rest on one displayed realization per class balance](#issue-f37) | Low | overclaim | numerical 205–216, p. 17 | "Consistently", "repeatedly", and "depends strongly on the hyperparameters" are not displayed; simulation supports the monotone and U-shaped patterns. | Open | no |
| F38 | [Abstract, contributions, and scope paragraph do not reflect Section 5](#issue-f38) | Low | inconsistency | main 90–109, p. 1; introduction 98–138, p. 3 | Class imbalance is called out of scope although Section 5.3 takes it up. | Open | no |
| F39 | [Roadmap omits Sections 3 and 5 and Appendices D–E, and calls appendices "Sections"](#issue-f39) | Low | inconsistency | introduction 140–145, p. 3 | "Respectively" has one antecedent for three items. | Open | no |
| F40 | [Abstract's "joint parameter and score trajectory laws" conflicts with the two-space construction](#issue-f40) | Low | inconsistency | main 103–105, p. 1; related_work 54, 130, pp. 4–5 | Definition 4.6 prescribes no joint law between the two sides. | Open | no |
| F41 | [Contribution 3 says "unlabeled scores", but Theorem 4.10 gives convergence of all scores](#issue-f41) | Low | inconsistency | introduction 122–124, p. 3 | Understates the result. | Open | no |
| F42 | [Introduction does not state the order of limits or the data conditions of the results](#issue-f42) | Low | improvement | main 99–108, p. 1; introduction 89–127, pp. 2–3 | Long-time results concern d → ∞ first; Proposition 4.9 indicates the limits need not commute. | Open | no |
| F43 | ["The training objective changes at each iteration" versus Proposition 4.1](#issue-f43) | Low | overclaim | introduction 76–80, p. 3 | Off a null set the iterates follow preconditioned GD on one fixed potential V; only the surrogate changes. | Open | no |
| F44 | [Positioning of Theorem 4.7 against rigorous GD/DMFT results states the obstruction imprecisely](#issue-f44) | Low | improvement | related_work 180–187, 202–210, p. 5; mean-field 566–587, p. 13 | The failing hypotheses: discontinuity plus data-driven scalars (b^t, m^t) that shift the thresholds; mean-shift design. | Open | no |
| F45 | [Closest prior DMFT for this model (Mignacco et al. 2021) is in references.bib but not cited](#issue-f45) | Low | gap (literature) | related_work 136–166, pp. 4–5 | Definition 4.6 at π = 0, no intercept, ridge reduces to a discretization of their equations. | Open | no |
| F46 | [Gaussian conditioning credited only to Bolthausen in the main text; Bayati–Montanari lemma not pointed to](#issue-f46) | Low | improvement | mean-field 566–571, p. 13; proof-mean-field 1583–1584, p. 36 | The rectangular conditioning of Proposition B.8 is Bayati–Montanari §III-H, Lemmas 10–11. | Open | no |
| F47 | [Discontinuities attributed to hard pseudo-labeling, but the only jumps are at the selection thresholds](#issue-f47) | Low | inconsistency | related_work 202–206, p. 5 | With κ₋ < 0 < κ₊ the sign jump at 0 never affects the update. | Open | no |
| F48 | [Positioning undersells the projection-defined memory coefficients, which carry the jump terms](#issue-f48) | Low | improvement | related_work 202–210, p. 5 | Derivative-based response kernels miss the Stein boundary term. | Open | no |
| F49 | [Section 5.3 credits only Takahashi for intercept drift and fixing; Takanami et al. (cited) report both](#issue-f49) | Low | gap (literature) | numerical 233–238, p. 17 | Takanami et al. §7 observe the drift and propose bias fixing with repeated data. | Open | no |
| F50 | [Oymak–Gulcu described without noting that their characterization is rigorous and proportional-asymptotic](#issue-f50) | Low | presentation (literature) | related_work 20–21, 36–43, pp. 3–4 | Their Theorem 3.3 is a rigorous limit with fresh batches. | Open | no |
| F51 | ["Hard pseudo-labels" understates Takanami et al., who analyze soft labels with hard labels as a limit](#issue-f51) | Low | inconsistency (source) | related_work 40–42, p. 4 | Their §3.2 uses an inverse temperature. | Open | no |
| F52 | [Javanmard et al. (2025), a rigorous AMP analysis of iterated retraining with reused data, is not discussed](#issue-f52) | Low | gap (literature) | related_work 36–55, pp. 3–4 | Supervised noisy-label setting, no confidence selection; the novelty claim stands. | Open | no |
| F53 | [Normalized alignment ᾱ^t reuses the symbol of the projection coefficients](#issue-f53) | Low | inconsistency (notation) | numerical 57–75, 145–153, 452–461, pp. 16, 19 | Clashes with ᾱ^[w](t,s), ᾱ^[g](t,s) of Definition 4.6. | Open | no |
| F54 | [κ denotes the threshold pair in Sections 3–4 and a positive scalar in Section 5](#issue-f54) | Low | inconsistency (notation) | numerical 15–16, 426, pp. 15, 18 | Write κ₋ = −κ₊ instead. | Open | no |
| F55 | [z, ξ denote both effective scalars and finite-dimensional Gaussian vectors, contrary to the tilde convention](#issue-f55) | Low | inconsistency (notation) | proof-mean-field 671–676, 753–762, 2309–2318, 2383, 2759, pp. 30–31, 41, 44 | Both meanings occur within 70 lines. | Open | no |
| F56 | [External result pointers: Kallenberg (3rd ed.) numbers verified correct; Ethier–Kurtz pointer unverified](#issue-f56) | Low | unverified-source | proof-mean-field 1040–3100 (12 Kallenberg pointers), 1413–1415, pp. 32–46 | Four auditors could not confirm the Kallenberg numbers; the gap task confirmed all of them. | Open | no |
| F57 | [Cited preprints with published versions](#issue-f57) | Low | inconsistency (bibliography) | references: oymak2020, dang2026, yang2022, arous2021online, arous2023highdimensional, paquette2022, wormhille2009ergodic | Oymak–Gulcu (AISTATS 2021, retitled), Dang et al. (ICML 2026), and others. | Open | no |
| F58 | [Bibliography metadata errors: Piccialli volume/year, Lecoiu title, Ben Arous sorting](#issue-f58) | Low | error (bibliography) | references 93–102, 846–888, pp. 19–20 | Volume 217 is 2026; the arXiv v2 title differs; "Ben Arous" parsed with surname "Arous". | Open | no |
| F59 | [Labels: model definition unlabeled, item labels resolve to "B.4", a duplicate label, many unreferenced labels](#issue-f59) | Low | presentation | setting 13–40, p. 5; proof-mean-field 683, 699–908, pp. 30–31 | Latent; no wrong reference prints today. | Open | no |
| F60 | [Streamlining: Assumption 4.4(3), j(0) = j'(0) = 0, is used once and can be dropped](#issue-f60) | Low | redundancy | long-time-behavior 80, p. 14; proof-long-time 610–620, p. 51 | A unique minimizer u₀ of j gives the needed bound. | Open | no |
| F61 | [Streamlining: Assumption 4.2 is implied by Assumption 4.1; L_ℓ, L_j defined twice](#issue-f61) | Low | redundancy | mean-field 48–64, p. 10; finite-dim 13–37, p. 7; long-time-behavior 60–82, 141–142, p. 14 | Theorem 4.10 assumes both. | Open | no |
| F62 | [Streamlining: p̄ ∈ (0,1) in Assumption 3.1 is used only in Section 5](#issue-f62) | Low | redundancy | setting 112, p. 6 | No proof in Appendices A–C uses it; Proposition 5.1 needs it but does not cite it. | Open | no |
| F63 | [Streamlining: ν_μ → ν̄_μ in display (6) is implied by Assumption 4.3(1); ν̄_μ is never used](#issue-f63) | Low | redundancy | setting 55–60, 97, p. 6 | Compatibility of the two limits is forced, not stated. | Open | no |
| F64 | [Streamlining: unused clauses in Propositions 4.1–4.3](#issue-f64) | Low | redundancy | finite-dim 68–210, p. 8; proof-finite-dim 12–164, pp. 22–23 | Global Lipschitz Ψ_κ, branch convexity, polyhedral closures, the K_c identity are unused. | Open | no |
| F65 | [Streamlining: Remark A.3 and the closing lines of the proof of Theorem 4.4 are unused](#issue-f65) | Low | redundancy | proof-finite-dim 518–556, p. 25 | Correct, but referenced nowhere. | Open | no |
| F66 | [Streamlining: Proposition B.4 restates Lemma B.1, Lemma B.3, and Proposition B.8](#issue-f66) | Low | redundancy | proof-mean-field 683–851, pp. 30–31; 1772–1793, p. 37 | Items (i) are proved by citing B.8; strong induction is unnecessary; several labels unreferenced. | Open | no |
| F67 | [Streamlining: the value 0 in the atomlessness display of Lemma B.1 is never used](#issue-f67) | Low | redundancy | proof-mean-field 54–58, 204–206, pp. 26–27 | Only the thresholds κ± are used. | Open | no |
| F68 | [Streamlining: unused conditions in Lemmas B.5–B.6](#issue-f68) | Low | redundancy | proof-mean-field 940–941, 1238–1257, pp. 31, 33 | Closedness of X, measurability and sign of c, v. | Open | no |
| F69 | [Streamlining: Lemma E.5 and Corollary E.7 are never cited; their content is re-derived or duplicated](#issue-f69) | Low | redundancy | mathematical-preliminaries 62–66, 130–145, 178–219, pp. 58–60; proof-mean-field 969–1144, 1465, 2073–2076, 2866–2869 | Only p = 2 is used; Definition E.2's completeness/separability facts unused. | Open | no |
| F70 | [Streamlining: limit (116) and several Appendix C symbols are unused; Lemma C.5 re-derives recorded limits](#issue-f70) | Low | redundancy | proof-long-time 8–64, 1058–1086, pp. 46–47, 54 | P̃_L, c_κ, Ẽ_U, (116) unused; the full-sample limit used is not recorded. | Open | no |
| F71 | [Streamlining: quantities defined two or three times (ω̄^t, s̄_μ, s_μ, H^[g], P̃_U, …)](#issue-f71) | Low | redundancy | mean-field 533–540, p. 13; long-time-behavior 112–113, 205–210, pp. 14–15; numerical 86–90, 180, p. 16 | All definitions agree; the second ":=" reads as a new object. | Open | no |
| F72 | [Streamlining: Proposition 5.2's sign hypothesis is needed only for Ã^t ≥ 0](#issue-f72) | Low | redundancy | numerical 247–346, pp. 17–18; proof-numerical 76–212, pp. 56–57 | The identities are sign free; part (ii) partly restates Definition 4.6. | Open | no |
| F73 | [Streamlining: unused packages, macros, and environment in the preamble](#issue-f73) | Low | redundancy | main 4–75, p. 1 (nonprinting) | tikz, fancyhdr, bm, accents, cleveref; \R, \sign, \1, …; misleading comments. | Open | no |
| F74 | [Eventual geometric rate of Theorem 4.4 is not uniform in d](#issue-f74) | Presentation | presentation | finite-dim 273–280, p. 9; long-time-behavior 29–56, p. 13 | t₀ ≥ T_id → ∞ in probability; one sentence after Proposition 4.9. | Open | no |
| F75 | [Separate assumption counter duplicates printed numbers](#issue-f75) | Presentation | presentation | main 44 | Assumption 4.1 and Proposition 4.1, …, Assumption 4.4 and Theorem 4.4. | Open | no |
| F76 | [Notation clashes: j, script H, W, recycled letters, symbols used before definition](#issue-f76) | Presentation | presentation | proof-long-time 349–354, 51–101; proof-mean-field 515, 911–916; setting 141–156; various | Grouped notation points confirmed by a verifier. | Open | no |
| F77 | [Single-check presentation: Sections 3–4.1 and Appendix A](#issue-f77) | Presentation | presentation | finite-dim, proof-finite-dim, pp. 8–9, 22–25 | Bare references, unreferenced labels, missing citations of Propositions 4.2–4.3. | Open | no |
| F78 | [Single-check presentation: Section 4.2 and Appendices B and E](#issue-f78) | Presentation | presentation | mean-field, proof-mean-field, mathematical-preliminaries, pp. 9–13, 25–46, 58–60 | Includes a non-conformable transpose at proof-mean-field 1850 and r^T not produced by Algorithm 3.2. | Open | no |
| F79 | [Single-check presentation: Section 4.3 and Appendix C](#issue-f79) | Presentation | presentation | long-time-behavior, proof-long-time, pp. 13–15, 46–55 | Wording, cross-references, symbol reuse. | Open | no |
| F80 | [Single-check presentation: Section 5, Appendix D, captions, and code documentation](#issue-f80) | Presentation | presentation | numerical, proof-numerical, pp. 15–19, 56–57; code README | Star conventions, missing pointers, captions without horizons and seeds. | Open | no |
| F81 | [Single-check presentation: abstract, introduction, related work](#issue-f81) | Presentation | presentation | main, introduction, related_work, pp. 1–5 | Missing "and", linear vs affine, pronoun for a single author. | Open | no |
| F82 | [Single-check presentation: cross-reference style and typography across the paper](#issue-f82) | Presentation | presentation | proof-mean-field 6–9, 678; proof-finite-dim 6–7; proof-long-time 126–131; mean-field 185 | Bare \ref prints "well defined in B.1"; \eqref on a definition; double period. | Open | no |
| F83 | [Single-check presentation: theorem style, source comments, figures, BibTeX capitalization](#issue-f83) | Presentation | presentation | main 40–46; finite-dim and proof-finite-dim (25 comments); numerical 28–42, 185–200; references | Italic definitions, % CHANGE notes, small figure fonts, unprotected capitals. | Open | no |

## Detailed entries

<a id="issue-f01"></a>

### F01. Theorem 4.7 and Proposition B.4 cite display (6) instead of Assumption 3.1, so $\bar\rho\in(0,1)$ is missing from their hypotheses

**Importance:** Medium · **Type:** inconsistency (statement hypotheses) · **State:** Open · **resolved?** no

**Location (d430d75):** mean-field 429–434 (Theorem 4.7, `theorem:trajectory`, p. 12); proof-mean-field 684–687 (Proposition B.4, `proposition:master-recursion`, p. 30) and 4–5 (Appendix B preamble, p. 25); compare setting 91–115 (Assumption 3.1, `assumption:asymptotic-regime`, display (6) = `eq:finite-dim-limits` at 94–102 and the sentence "We assume $\bar p,\bar\rho\in(0,1)$" at 112, p. 6). Inherited at proof-mean-field 39 (Lemma B.1, p. 26), mean-field 516 (Corollary 4.8, p. 12), long-time-behavior 141–145 (Theorem 4.10, p. 14) and 203 (Corollary 4.11, p. 15), proof-long-time 4–5 (p. 46), numerical 249 and 411 (Propositions 5.2–5.3, pp. 17–18).

**Finding and evidence (established):** Theorem 4.7 assumes "the proportional asymptotics \eqref{eq:finite-dim-limits}, Assumption 4.2, and Assumption 4.3". Display (6) contains only $\delta\to\bar\delta$ and the $W_2$ limits of $\nu_\mu$ and $\nu_{(Y,\Delta)}$; the conditions $\bar\delta\in(0,\infty)$ (setting 103) and $\bar p,\bar\rho\in(0,1)$ (setting 112) are separate sentences of Assumption 3.1, and $\bar\rho$ itself is introduced only in the second display (`eq:finite-dim-limits-2`). Read literally, the hypotheses admit $\bar\rho\in\{0,1\}$: for example, $\Delta_i=1$ for all but one sample satisfies display (6) with $\bar\rho=1$. Definition 4.6 then divides by zero (the factors $\tilde\Delta/\bar\rho$ and $(1-\tilde\Delta)/(1-\bar\rho)$ in (35), mean-field 387, 395; also $1/\sqrt{\bar\delta}$ at 309, 416). The proofs use the omitted condition explicitly: proof-mean-field 215 and 222 (Lemma B.1, the source of $\bar v^{[g]}>0$, p. 27), 2431, 2443–2444, 2469 (proof of Proposition B.4, p. 42), 2994–3000 (proof of Corollary 4.8, p. 45), proof-long-time 64, 400, 1216. Citation styles disagree within the paper: the proof of Corollary 4.8 (proof-mean-field 3084) and Proposition 4.9 (long-time-behavior 31) cite Assumption 3.1 itself, and setting 279–281 says assumptions are introduced alongside each theorem, so the hypothesis lists are meant to be complete. The verifiers note that $\bar p\in(0,1)$ is not needed by Theorem 4.7 or Appendix B (see F62); citing the whole assumption also imports that condition.

**Consequence:** Theorem 4.7, Corollary 4.8, Lemma B.1, Proposition B.4, Theorem 4.10, Corollary 4.11, and Propositions 5.2–5.3 are not well posed as literally stated when $\bar\rho\in\{0,1\}$. Under the intended hypothesis all of them hold as proved; no mathematical change is needed.

**Proposed repair and completion criterion:** In Theorem 4.7 (mean-field 431–432) and Proposition B.4 (proof-mean-field 684–685), replace "the proportional asymptotics \eqref{eq:finite-dim-limits}" by "Assumption~\ref{assumption:asymptotic-regime}". Minimal alternative (avoids importing $\bar p\in(0,1)$): keep the display and add "with $\bar\delta\in(0,\infty)$ and $\bar\rho\in(0,1)$". Complete when every result that invokes Definition 4.6, divides by $\bar\rho$ or $1-\bar\rho$, or conditions on $\tilde\Delta$ has $\bar\rho\in(0,1)$ in its hypothesis chain, and Theorem 4.7 and Proposition 4.9 cite the regime in the same form.

**Dependencies:** Related: F62 (where $\bar p\in(0,1)$ is actually used), F63 ($\nu_\mu$ limit), F28 (Proposition 5.1 cites no assumption), F04 (other hypothesis inconsistencies). The same fix covers the presentation point "Assumptions~\ref" (plural) at proof-mean-field 3084 (F82).

**Verification:** Reported independently by eleven items: M1-01, M2-01, M5-01, M7-01 (unit), L1-01 (unit), C1-01, C2-01 (chain), X01-01, X04-01, X10-06 (first part) (cross), G1-03-04 (gap task). Two-verifier checks: C1-01 (v1, v2 both confirmed-with-changes, Low), X01-01 (v1, v2 confirmed-with-changes, Low; v1 notes Medium defensible), X04-01 (v1 confirmed-with-changes Medium, v2 confirmed-with-changes Low); batch verdicts `M1.low.md`, `M2.low.md`, `M5.low.md`, `M7.low.md`, `L1.low.md`, `C2.low.md`, `G1-03.low.md`, `X10.low.md` confirmed. Importance: the verifiers split between Medium and Low; the register uses Medium because a condition must be added to the hypothesis list of the paper's central theorem and propagates to eight results (protocol: "conditions … that must be restated").

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f02"></a>

### F02. Figure 1's "Selected fraction $\omega^t$" panel plots $\omega^{t-1}$, with an artificial $0$ at $t=0$

**Importance:** Medium · **Type:** inconsistency (paper–code; figure) · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 28–42 (Figure 1, `fig:mean-field-validation`, second panel, p. 15); definition mean-field 494–501 (`eq:finite-dimensional-trajectory-observables`, p. 12) and 533–540 ($\bar\omega^t$, Corollary 4.8, p. 13). Code `e823bf3`: `src/callbacks.py` 280–285 (finite callback), `figures/experiments.py` 213 (effective series), docstrings at `figures/experiments.py` 139–140 and 308.

**Finding and evidence (established):** The panel is labeled $\omega^t=\frac1M\sum_{j\in I_{\mathcal U}}S_\kappa(r_j^t)$, the fraction selected at the current scores. Both curves (algorithm and effective process) start at $0$ at $t=0$ and jump to about $0.165$ at $t=1$–$2$, while the adjacent panel shows $e^0\approx0.083$. Since selected errors are a subset of selected observations, $e^t\le\omega^t$ identically, so the plotted pair is impossible. In the caption's setting ($b^{\rm init}=0$, $w^{\rm init}$ independent of $\mu$, $\sigma=1$, $\kappa_\pm=\pm\log4$), $\tilde r^0=\sigma\bar\tau^0z$ with $\bar\tau^0=1$, so $\bar\omega^0=\mathbb P(|z|\ge\log4)=0.166$ and $\bar e^0=\Phi(-\log4)=0.083$; the plotted $e^0$ matches exactly. The code records `update_records_[t-1].omega` at iteration $t$ and $0$ at $t=0$, and the effective series is `[0.0] + se.selection_rate[:T]`, a documented convention. So the plotted value at $t$ is $\omega^{t-1}$ for every $t$, for both methods. The true $\omega^0$ in the stored results is $0.168$ (finite, median) and $0.166$ (effective). An independent implementation written from the paper alone (X13) obtains $\omega^0=0.166$ and otherwise reproduces the panel (e.g. $\omega^{300}\approx0.91$).

**Consequence:** Local to Figure 1. The validation conclusion ("closely track") is unaffected because both curves carry the same shift, but the displayed $\omega^t$ does not match its definition at any $t$, and the two selection panels are offset by one step.

**Proposed repair and completion criterion:** Record the current-score $\omega^t$ for $t=0,\dots,T$ (finite: from the current scores; effective: `se.selection_rate[0..T]`) and regenerate Figure 1; or retitle the panel $\omega^{t-1}$ and state the lag in the caption. Complete when the plotted $\omega^0\approx0.17$ and $e^t\le\omega^t$ at every plotted $t$ (or the lag is stated).

**Dependencies:** Related: F32 ($e^t$ undefined), F80 (caption details). A code change in the companion repository and a regenerated `approximation_accuracy.png`.

**Verification:** X02-01 (cross; v1 confirmed, v2 confirmed-with-changes identifying the code convention, `X02-01.v1.md`, `X02-01.v2.md`); X09-01 (cross, code; v1, v2 confirmed, `X09-01.v1.md`, `X09-01.v2.md`); X13-01 (independent simulation; confirmed, `X13.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f03"></a>

### F03. Section 5.3's intervention claims are undisplayed and unspecified, and "fixing the intercept likewise improves performance" is false at the only intercept value the paper defines

**Importance:** Medium · **Type:** overclaim · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 239–241 (Section 5.3, `subsec:intercept-dynamics`, p. 17), within the paragraph 233–245.

**Finding and evidence (established):** The text says: "In the settings we examined, fixing the intercept likewise improves performance. We also observe gains by modifying the algorithm so that the intercept is updated using only labeled observations." Neither experiment appears in any figure, table, or appendix (the live paper has two figures, both of the standard update, and no tables); neither variant is defined; no fixed value, configuration, baseline, metric, or effect size is given. The companion code has the switches (`train_bias=False` with `initial_bias`; `bias_pseudo_label_param=0.0`) but no notebook, configuration, or output exercises them (X09-03). An independent simulator written from the paper (checked against a second independent implementation to $10^{-15}$) at the Figure 2 imbalanced configuration ($p=0.2$, $d=5000$, $T=400$, 30 seeds) gives:

- **Intercept held at $b^{\rm init}=0$** (the only value the experiments define): final error $0.256$ $[0.245,0.263]$ against $0.199$ as written; worse at every $t\ge1$ in all seeds, ending above the majority-class error $0.2$; the effective process agrees ($0.258$ vs $0.199$). Figure 1 configuration (10 seeds): $0.240$ vs $0.184$. The cause is a persistent intercept regret of about $0.09$.
- **Intercept held near the classification-optimal value** (e.g. Takahashi's supervised-learning value, or fixed values between about $-0.5$ and $-3$): the final error improves ($\approx0.165$ vs $0.199$), but does not beat the best error of the unmodified algorithm ($0.162$ at $t\approx90$).
- **Labeled-only intercept updates:** final error $0.158$ vs $0.199$ and best error $0.158$ vs $0.163$ (30/30 seeds; effective process agrees), but worse until $t\approx123$–$139$; in the Figure 1 configuration the final error improves ($0.163$ vs $0.184$) while the best-over-horizon error is worse ($0.163$ vs $0.152$, 10/10).

These two sentences are the only interventional evidence for the intercept-feedback interpretation that motivates Propositions 5.2–5.3 and the open question.

**Consequence:** Local to the motivation of Section 5.3; no proved result depends on it, and the abstract and introduction do not repeat it. A reader would infer that holding $b$ at $0$ helps under imbalance, which is false.

**Proposed repair and completion criterion:** Either state the fixed value (for example the intercept from supervised training on the labeled data, as in `takahashi2026role`), the configuration, and the metric (end-of-horizon error), define the labeled-only variant in one sentence, and support both with a small figure, table, or numeric sentence (e.g. "in the setting of Figure 2, the final error drops from about 0.20 to about 0.16"); or delete lines 239–241. Complete when each retained claim names its variant, configuration, and metric and is supported by displayed or reproducible results.

**Dependencies:** Related: F35–F37 (other Section 5.3 empirical statements), F49 (attribution of intercept fixing). If retained, a configuration or notebook in the companion repository.

**Verification:** X02-04 (cross; v1, v2 confirmed, Medium, `X02-04.v1.md`, `X02-04.v2.md`); G1-01-01 (gap-task simulation, reported High; three verifiers confirmed-with-changes and lowered it to Medium, `G1-01-01.v1.md`–`v3.md`); G1-01-02 (confirmed, `G1-01.low.md`); X09-03 (code: no configuration or results; confirmed-with-changes, `X09.low.md`); X10-04 (intervention part; v1, v2 confirmed-with-changes, Medium, `X10-04.v1.md`, `X10-04.v2.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f04"></a>

### F04. Sign conventions for $\lambda,\pi$ disagree across Section 3, Algorithm 3.2, Section 4.2, and individual results

**Importance:** Low · **Type:** inconsistency · **State:** Open · **resolved?** no

**Location (d430d75):** setting 160 ("Fix dimension-independent coefficients $\lambda,\pi>0$", p. 6) and 218 (Algorithm 3.2, `alg:self-training`, inputs "$\eta,\lambda,\pi>0$", p. 7); mean-field 111–112 ("$\lambda,\pi\ge0$", p. 10); finite-dim 186 (Proposition 4.3, `prop:branch-convexity-coercivity`, "$\lambda>0$, $\pi\ge0$", p. 8) and 252 (Theorem 4.4, "$\lambda>0$, $\pi>0$", p. 9); proof-finite-dim 175 (Lemma A.1, "$\pi,\lambda\ge0$", p. 23); long-time-behavior 143 (Theorem 4.10, p. 14).

**Finding and evidence (established):** Four different conventions coexist. Theorem 4.7 concerns iterates "generated by Algorithm 3.2" (mean-field 470), whose inputs require $\lambda,\pi>0$, yet Section 4.2 announces $\lambda,\pi\ge0$; so for $\lambda=0$ or $\pi=0$ it refers to an algorithm the paper does not define. Each result's own requirements are the right ones and every statement is true in the range it states (checked): $\lambda>0$ enters Proposition 4.3, Lemma A.1 (boundedness), and Lemma C.4; $\pi>0$ enters only Lemma A.2 (strictness of (69)) and Proposition C.3 ($C_{\rm sw}\propto\pi^{-2}$); Lemma B.1, Proposition B.4, Theorem 4.7, Corollary 4.8, Proposition 4.9, and Propositions 5.1–5.3 use no sign. With $\pi=0$ the finite-dimensional limit and rate survive but identification can fail (constructed example: the configuration changes at each of 599 consecutive steps while $\theta^t$ converges). Literal runs of Algorithm 3.2 at $\pi=0$ match Definition 4.6 (X13).

**Consequence:** Presentation-level; no result is wrong. The scope of Theorem 4.7, Corollary 4.8, and Propositions 5.2–5.3 at $\lambda=0$ or $\pi=0$ is unclear.

**Proposed repair and completion criterion:** Write "$\lambda,\pi\ge0$" at setting 160 and 218 (keeping $\eta>0$), and keep the explicit positivity requirements already stated in Proposition 4.3, Theorem 4.4, Lemma A.2, and Theorem 4.10. Alternative: delete "$\lambda,\pi\ge0$" at mean-field 112 so the standing $>0$ applies. Complete when setting 160, setting 218, finite-dim 186, and mean-field 112 agree and every result that needs positivity says so.

**Dependencies:** Related: F01 (other hypothesis citations), F24 (hypotheses actually used in Appendix C).

**Verification:** P1-01, P2-05 (unit), M1-02 (unit), C1-02 (chain), X01-03, X04-07, X13-03, X08-04, X10-06 (second part) (cross/usage); all confirmed or confirmed-with-changes (`P1.low.md`, `P2.low.md`, `M1.low.md`, `C1.low.md`, `X01.low.md`, `X04.low.md`, `X13.low.md`, `X08.low.md`, `X10.low.md`). The related finding X02-07 (Hessian display lacks $\lambda>0$) was refuted because setting 160 makes $\lambda>0$ standing in Section 4.1.

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f05"></a>

### F05. The upper bound $\nabla^2L_{\mathfrak c}\preceq H_d$ is asserted in running text and used, but not proved

**Importance:** Low · **Type:** gap · **State:** Open · **resolved?** no

**Location (d430d75):** finite-dim 236–240 (text after (12)–(13), `eq:hessian`, `eq:lambda-d`, p. 9); used at proof-finite-dim 483–489 (proof of Theorem 4.4, `thm:st-convergence`, p. 25).

**Finding and evidence (established):** "For every configuration $\mathfrak c$ and $\theta$, the branch Hessians satisfy $0\prec\nabla^2L_{\mathfrak c}(\theta)\preceq H_d$." The lower bound is Proposition 4.3 (under the standing $\lambda>0$; it needs only $\lambda>0$, $N\ge1$, $\ell''>0$). The upper bound is proved nowhere: the proof of Proposition 4.3 shows only positivity, and Lemma A.1 proves the function-value bound (64). It follows in one line from $\ell''\le L_\ell$, $j''\le L_j$, $\pi\ge0$, and enlarging the unlabeled sum from $\{j:\mathfrak c_j\ne0\}$ to $I_{\mathcal U}$ (checked by hand and numerically).

**Consequence:** None once the line is added; the bound enters the geometric rate of Theorem 4.4.

**Proposed repair and completion criterion:** Add to the proof of Proposition 4.3 after proof-finite-dim 142: "Moreover, $\ell''\le L_\ell$, $j''\le L_j$, and $\pi\ge0$ give $\nabla^2L_{\mathfrak c}(\theta)\preceq H_d$ for every $\mathfrak c$ and $\theta$", citing `eq:hessian`, and refer to Proposition~\ref{prop:branch-convexity-coercivity} at finite-dim 236. Complete when the sandwich used in the proof of Theorem 4.4 has a proof location.

**Dependencies:** none. Related: F77 (missing citations of Propositions 4.2–4.3 in Appendix A).

**Verification:** P1-04 (unit; confirmed-with-changes, `P1.low.md`); P2-06 point 3 (single-check). X02-07 (same display, claimed missing $\lambda>0$) was refuted.

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f06"></a>

### F06. Remark 4.5 can be stated exactly, and should name the configuration it concerns

**Importance:** Low · **Type:** improvement · **State:** Open · **resolved?** no

**Location (d430d75):** finite-dim 286–291 (Remark 4.5, after Theorem 4.4, p. 9).

**Finding and evidence (established):** "If $\theta^\star_{\mathfrak c}\notin\mathcal S_\kappa$, then $\theta^\star_{\mathfrak c}\in\Theta_{\mathfrak c}$ and $G(\theta^\star_{\mathfrak c})=0$. At threshold points, $G(\theta^\star_{\mathfrak c})$ need not vanish." (1) The first sentence holds only for the configuration identified in Theorem 4.4 (it uses $\theta^\star_{\mathfrak c}\in\overline{\Theta_{\mathfrak c}}$); for an arbitrary configuration the minimizer of $L_{\mathfrak c}$ can lie in another branch. (2) The paper proves more: $G(\theta^\star_{\mathfrak c})=0$ if and only if $\theta^\star_{\mathfrak c}\in\Theta_{\mathfrak c}$; otherwise $\theta^\star_{\mathfrak c}\in\Theta_{\mathfrak d}$ for some $\mathfrak d\ne\mathfrak c$ and (69) gives $G(\theta^\star_{\mathfrak c})=\nabla L_{\mathfrak d}(\theta^\star_{\mathfrak c})\ne0$. (3) The boundary case occurs (constructed example with $d=1$, $N=4$, $M=1$, $\pi=1$, logistic loss).

**Consequence:** Local only. Theorem 4.4 and the introduction's description (introduction 111–113) are unaffected.

**Proposed repair and completion criterion:** Replace the remark by: "Let $\mathfrak c$ be the configuration identified in Theorem~\ref{thm:st-convergence}. Then $G(\theta^\star_{\mathfrak c})=0$ if and only if $\theta^\star_{\mathfrak c}\in\Theta_{\mathfrak c}$, which holds in particular when $\theta^\star_{\mathfrak c}\notin\mathcal S_\kappa$. Otherwise $\theta^\star_{\mathfrak c}$ lies on a threshold, belongs to a different branch, and is not a fixed point of the update." Complete when a checker confirms both cases against (69).

**Dependencies:** none.

**Verification:** P2-01 (unit; confirmed, `P2.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f07"></a>

### F07. The geometric rate of Theorem 4.4 holds from $T_{\rm id}$ on; $t_0$ is unnecessary

**Importance:** Low · **Type:** improvement · **State:** Open · **resolved?** no

**Location (d430d75):** finite-dim 273–280 (Theorem 4.4, `thm:st-convergence`, p. 9); proof-finite-dim 490–517 (`eq:st-branch-contraction`, (71), p. 25).

**Finding and evidence (established):** The theorem asserts an integer $t_0\ge T_{\rm id}$, $q\in(0,1)$, $C<\infty$ with $\|\theta^t-\theta^\star_{\mathfrak c}\|_{P_d^{-1}}\le Cq^{t-t_0}$ for $t\ge t_0$; the proof contracts only on a small ball around the limit. Let $K$ be the closed convex hull of $\{x^t:t\ge T_{\rm id}\}\cup\{x^\star_{\mathfrak c}\}$, compact by Lemma A.1. On $K$ the eigenvalues of $P_d^{1/2}\nabla^2L_{\mathfrak c}P_d^{1/2}$ lie in $[m_K,\Lambda_d]$ with $m_K>0$, so $\|DT_{\mathfrak c}\|\le q_K:=\max\{|1-\eta m_K|,|1-\eta\Lambda_d|\}<1$ there, and the mean-value formula along segments in $K$ gives contraction at every $t\ge T_{\rm id}$. In 256 random runs the one-step error ratio was below 1 at every step after the last configuration change.

**Consequence:** Local; the theorem as stated is correct, and this version is simpler and slightly stronger.

**Proposed repair and completion criterion:** Optional: state $\|\theta^t-\theta^\star_{\mathfrak c}\|_{P_d^{-1}}\le q^{t-T_{\rm id}}\|\theta^{T_{\rm id}}-\theta^\star_{\mathfrak c}\|_{P_d^{-1}}$ for $t\ge T_{\rm id}$, replace the ball in proof-finite-dim 492–510 by $K$, and adjust sketch step 3. Complete when a checker confirms the segment argument uses only convexity of $K$.

**Dependencies:** Related: F74 (the rate is not uniform in $d$), F08 ($T_{\rm id}$ definition).

**Verification:** P2-02 (unit; confirmed, `P2.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f08"></a>

### F08. $T_{\rm id}$ is "some time" in Theorem 4.4 and Lemma A.2 but "the first time" in Proposition 4.9

**Importance:** Low · **Type:** inconsistency (definition) · **State:** Open · **resolved?** no

**Location (d430d75):** finite-dim 260–266 (Theorem 4.4, `thm:st-convergence`, p. 9); proof-finite-dim 296–303 (Lemma A.2, `lem:st-finite-identification`, p. 24); long-time-behavior 34–44 (Proposition 4.9, `prop:identification-time-divergence`, p. 13).

**Finding and evidence (established):** Theorem 4.4: "there exist a finite integer $T_{\rm id}\ge1$ and a nonempty branch …", so any later integer also qualifies. Proposition 4.9 defines $T_{\rm id}:=\inf\{T\ge1:\mathfrak C(\theta^t)=\mathfrak C(\theta^T)\ \forall t\ge T\}$ (with $\inf\emptyset=+\infty$) and proves that it diverges in probability. The divergence statement is meaningful only for the minimal time. The two uses are compatible (the minimal time is a valid witness in Theorem 4.4), but the paper never says they are the same object. The long-time simulation (G1-04) used the minimal time.

**Consequence:** Local (notation). Both results are correct as intended.

**Proposed repair and completion criterion:** Define $T_{\rm id}$ once, as the infimum (with $\inf\emptyset=+\infty$), in Section 4.1 before Theorem 4.4 and without hypotheses attached; Theorem 4.4 then asserts $T_{\rm id}<\infty$, and Proposition 4.9 refers to that definition. Complete when Theorem 4.4, its proof, Lemma A.2, and Proposition 4.9 use one definition.

**Dependencies:** none. Related: F07, F74.

**Verification:** P2-04 (unit; confirmed, `P2.low.md`); G1-04-01 (gap task; confirmed-with-changes, `G1-04.low.md`); also noted in single-check groups L1-06 (10) and C2-06 (4).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f09"></a>

### F09. The conditional-law notation $\stackrel d=_{\mathcal G}$ is used from Proposition B.4 on but explained only in passing inside Lemma B.6

**Importance:** Low · **Type:** presentation (definition) · **State:** Open · **resolved?** no

**Location (d430d75):** first use proof-mean-field 708 (Proposition B.4, `eq:gaussian-decomposition`, p. 30; also 750, 836, 877, 1776, 1779, 1960, 2014, 2261, 2629); only gloss 1271–1272 (Lemma B.6, `lemma:mf-proof-gaussian-extension`, p. 33); partial glosses 690–693 (p. 30), 1522–1530 (p. 34), 2022–2027 (p. 39).

**Finding and evidence (established):** The symbol on which Propositions B.4 and B.8 rest first appears on p. 30 and is explained only on p. 33 by "denotes equality of conditional laws", for a generic $\mathcal G^{(m)}$ that is not introduced as a sub-$\sigma$-field. The right-hand sides involve variables on an extended probability space ($\check U$, $z_t^{[g]}$, $z_t^{[w]}$, $e^{(m)}$) and, for $U$, a function $M_t$ of $U$ itself. Lines 690–693 and 2025–2027 say $\check U$ is independent of the conditioning $\sigma$-field on an extension, but the formal meaning (a.s. equality of regular conditional distributions, hence $(A,\xi)\stackrel d=(A,\xi')$ for every $\mathcal G$-measurable $A$) is never stated, and $z_t^{[g]},z_t^{[w]}$ are not covered. With that reading every use was checked and is correct, and it is exactly what Lemma B.6 requires.

**Consequence:** Local; clarity of the central statement of Appendix B.

**Proposed repair and completion criterion:** Before Proposition B.4 (e.g. after proof-mean-field 678) add: "For random elements $\xi,\xi'$ defined on an extension of the probability space and a sub-$\sigma$-field $\mathcal G$, we write $\xi\stackrel d=_{\mathcal G}\xi'$ when $\mathscr L(\xi\mid\mathcal G)=\mathscr L(\xi'\mid\mathcal G)$ almost surely; then $(A,\xi)\stackrel d=(A,\xi')$ for every $\mathcal G$-measurable $A$. Auxiliary Gaussian variables are defined on a product extension and are independent of the conditioning $\sigma$-field." Consolidate the partial glosses into back-references. Complete when the notation is defined before line 708 and every listed use matches it.

**Dependencies:** none. Related: F10.

**Verification:** M2-03, M3-07, M4-02 (unit; each confirmed-with-changes, `M2.low.md`, `M3.low.md`, `M4.low.md`); also X04-10 point 3 (F76).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f10"></a>

### F10. Proposition B.8: the passage from Lemma B.7 (deterministic directions) to history-measurable directions is asserted in one sentence

**Importance:** Low · **Type:** gap · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 1883–1892 (proof of Proposition B.8, `proposition:mf-proof-conditional-matrix`, p. 38), applied at 1921–1926 and 1975–1981 (pp. 38–39); Lemma B.7 (`lemma:mf-proof-linear-conditioning`) at 1594–1764 (pp. 36–37).

**Finding and evidence (established):** "At each step, we condition first on the current history. The next observation direction is then fixed, so Lemma B.7 applies … These successive conditionings are justified by the disintegration property of regular conditional distributions [Kallenberg, Theorem 8.5]." Lemma B.7 is stated for deterministic $(m,F,T)$; in the induction they are $\mathcal F_t$-measurable ($M_t$, $\mathcal S(W_{t-1},G_{t-1})$, $A\mapsto Aw^t$). Passing from "for each fixed $\omega$, Lemma B.7 conditions $\kappa_t(\omega,\cdot)$ on $A\mapsto Aw^t(\omega)$" to "this is a version of $\mathscr L(U\mid\mathcal F_t\vee\sigma(Uw^t))$" is the content of Bolthausen's adaptive conditioning: it needs a two-stage conditioning identity, joint measurability in (history, observation) of the kernel, and a $\pi$-system argument; the $\omega$-dependent null set in Lemma B.7's "almost every $y$" also needs a word. The step is true: the auditor wrote the bridging claim with the explicit kernel $N(m_y,\Pi^\perp_G(\cdot)\Pi^\perp_{W_t})$, $m_y=M_t+\Pi^\perp_{G_{t-1}}(y-M_tw^t)(w^t_\perp)^\top/\|w^t_\perp\|^2$, checked it against Lemma B.7 by hand and numerically, and a Monte Carlo of the actual algorithm agreed. The cited Theorem 8.5 is correct (it gives existence, a.e. uniqueness, and disintegration; G1-02), but it does not by itself supply the two-stage identity. Bayati–Montanari's Lemma 11 also treats only fixed constraints.

**Consequence:** None for the stated results (Proposition B.8 → Proposition B.4(i) → Theorem 4.7 stand). It weakens the claim of a "self-contained Gaussian conditioning argument" (related_work 207) at the step a specialist referee reads first.

**Proposed repair and completion criterion:** Before the induction at 1883, add a four-to-six-line stage-conditioning claim: the kernel $(m,F,T,y)\mapsto N(m_y,\pi_K)$ is jointly Borel by the explicit formula (1849–1857), and integrating Lemma B.7 against $\mathscr L(U\mid\mathcal F_t)$ gives $\mathbb E[f(U)g(S,Uw^t)]=\mathbb E[\int f\,dN(M_t^+,\pi_{\mathcal S(W_t,G_{t-1})})\,g(S,Uw^t)]$, citing the disintegration formula. Alternatively, state Lemma B.7 for a random triple measurable with respect to $\mathcal G$ with $Z$ independent of $\mathcal G$. Complete when a checker confirms joint measurability of the kernel and that both induction steps invoke the new statement.

**Dependencies:** Related: F09, F46 (Bayati–Montanari pointer), F56 (Theorem 8.5 confirmed).

**Verification:** M4-01 (unit; confirmed, `M4.low.md`); X05-02 (cross; confirmed, `X05.low.md`). The completeness critic did not reopen it because M4 wrote out and verified the argument.

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f11"></a>

### F11. Step 4 of the proof of Lemma B.6 uses disintegration without saying so

**Importance:** Low · **Type:** gap · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 1523–1552 (proof of Lemma B.6, `lemma:mf-proof-gaussian-extension`, step 4, p. 35).

**Finding and evidence (established):** "Equality of the conditional laws of $x^{(m)}$ and $y^{(m)}+e^{(m)}$ also identifies their joint laws with $H^{(m)}$. Indeed, … $\mathbb E[\mathbb E[\varphi(H^{(m)},x^{(m)})\mid\mathcal G^{(m)}]]=\mathbb E[\mathbb E[\varphi(H^{(m)},y^{(m)}+e^{(m)})\mid\mathcal G^{(m)}]]$". The chain is the tower property around a middle equality that is itself the claim. It is true: for products $\varphi_1(h)\varphi_2(x)$, pull out the $\mathcal G^{(m)}$-measurable factor and use equality of conditional laws, then extend by a monotone-class argument; equivalently, the disintegration theorem the paper already cites at 1752 and 1892 (Kallenberg Theorem 8.5, confirmed in the third edition by G1-02).

**Consequence:** Local; this step makes the conclusion of Lemma B.6 a statement about the actual $x^{(m)}$.

**Proposed repair and completion criterion:** Insert after "Indeed,": "by disintegration \cite[Theorem~8.5]{kallenberg2021foundations}, since $H^{(m)}$ is $\mathcal G^{(m)}$-measurable,". Complete when a checker confirms the theorem's hypotheses hold.

**Dependencies:** none. Related: F09.

**Verification:** M3-04 (unit; confirmed, `M3.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f12"></a>

### F12. The subsequence arguments in Lemmas B.5–B.6 need all dimensions on one probability space

**Importance:** Low · **Type:** gap · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 1037–1056 and 1225–1228 (proof of Lemma B.5, `lemma:mf-proof-empirical-stability`, pp. 32–33); 1416–1430 (proof of Lemma B.6, step 1, p. 34).

**Finding and evidence (established):** "Every subsequence admits a further subsequence converging almost surely to the same limit", then "Fix an outcome $\omega\in\Omega$ where these convergences hold". The subsequence criterion (Kallenberg Lemma 5.2) concerns random elements on one probability space. The paper defines the model separately for each $d$ (mean-field 471–472: "probability is taken with respect to the finite-dimensional Gaussian design noise"; setting 81–89), and Lemma B.6 uses a separate $\mathcal G^{(m)}$ per $m$. The step is true: hypotheses and conclusions are convergences in probability to deterministic limits, so they depend only on the law of each term, and all terms may be placed on a product space; no step uses joint laws across different $m$ (checked, including step 4 of B.6).

**Consequence:** Local; Lemmas B.5–B.6 and everything built on them are unaffected once the convention is stated.

**Proposed repair and completion criterion:** Add one sentence at 1037 (referred to at 1418): since hypotheses and conclusions concern convergence in probability to deterministic limits, they depend only on the law of each term, so all terms may be assumed defined on one probability space. Complete when a checker confirms no step uses joint laws across different $m$.

**Dependencies:** Related: F13.

**Verification:** M3-01 (unit; confirmed, `M3.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f13"></a>

### F13. Lemmas B.5–B.6 are indexed by the number of rows, but the sample-side arrays have $n(d)$ rows

**Importance:** Low · **Type:** gap · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 933–936, 942–955 (Lemma B.5, `lemma:mf-proof-empirical-stability`, p. 31), 1234–1244 (Lemma B.6, p. 33); uses at 2215–2219, 2358–2372, 2446, 2474, 2538–2549, 2976–2991 (pp. 40–45).

**Finding and evidence (established):** "The superscript $(m)$ explicitly records dependence on the number of rows. We apply these lemmas with $m=d$ for parameter-side empirical laws and $m=n$ for sample-side empirical laws." The lemmas are stated for a sequence whose $m$-th term has exactly $m$ rows, $m\to\infty$. On the sample side the sequence is indexed by $d$ with $n=n(d)$ rows and only $n/d\to\bar\delta$; $d\mapsto n(d)$ need not be injective or monotone (for $\bar\delta<1$ it must repeat values), so the lemmas do not literally apply. The proofs never use that the index equals the row count: B.5 uses nothing about $m$, B.6 only that the row count tends to infinity (1365, 1376, 1400–1406).

**Consequence:** Local; the conclusions used in Proposition B.4 hold.

**Proposed repair and completion criterion:** State both lemmas for arrays indexed by $d$ with $m_d$ rows, $m_d\to\infty$ (not needed for B.5), and adjust the sentence at 936; align the notation $H^{(d)}$, $H^{(n)}$ at the invocations. Complete when a checker confirms the proofs go through verbatim.

**Dependencies:** Related: F12.

**Verification:** M3-02 (unit; confirmed, `M3.low.md`); also M5-04 point 3 (single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f14"></a>

### F14. Facts established inside the proof of Lemma B.1 are invoked later as if they were part of its statement

**Importance:** Low · **Type:** improvement (statement completeness) · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 73–103, 176–191, 337–349 (proof of Lemma B.1, `lemma:mf-proof-nondegeneracy`; `eq:mf-proof-score-fresh-noise`, `eq:mf-proof-weight-fresh-noise`, pp. 26–28); uses at proof-mean-field 2374–2391, 2760–2767 (pp. 41, 44) and proof-long-time 80–92 (p. 47).

**Finding and evidence (established):** proof-mean-field 98–103 says the one-step forms "follow from the cumulative-memory definitions: substituting the representations of the previous fluctuations and collecting coefficients gives precisely the defining recursions", and proof-long-time 80–81 says "Lemma B.1 and the effective recursion give" the fresh-noise representation of $\tilde r^{t+1}$. The statement of Lemma B.1 contains neither the one-step forms nor the fresh-noise representations, and the history $\sigma$-fields $\mathcal H^{[g]}_t$, $\mathcal H^{[w]}_t$ are defined only inside its proof. The cumulative/one-step equivalence links Definition 4.6 to the limits obtained in Proposition B.4 (the limiting new coordinate at 2374–2386 is the one-step form) but is given in one sentence. The auditor verified it by induction on $t$; it is correct.

**Consequence:** None for correctness. A reader of Proposition 4.9 or Proposition B.4 cannot find the cited facts in the statement of Lemma B.1.

**Proposed repair and completion criterion:** Add to the statement of Lemma B.1 the two one-step identities, the definitions of $\mathcal H^{[g]}_t$, $\mathcal H^{[w]}_t$, and the two fresh-noise representations with innovations independent of the respective histories; include the short induction in the proof; refer to these displays by label at proof-mean-field 2389–2391, 2765–2767 and proof-long-time 80–92. Complete when each later use points to a labeled display.

**Dependencies:** Related: F16, F70 (duplicate definition of $\mathcal H^{[g]}_{t+1}$ in Appendix C).

**Verification:** M1-03 (unit; confirmed, `M1.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f15"></a>

### F15. The remark after Theorem 4.7 cites the deterministic Proposition E.4 for a convergence in probability

**Importance:** Low · **Type:** gap (citation) · **State:** Open · **resolved?** no

**Location (d430d75):** mean-field 475–477 (remark after Theorem 4.7, `theorem:trajectory`, p. 12), supporting mean-field 11–27 (p. 9); mathematical-preliminaries 69–89 (Definition E.3, `definition:pseudo-lipschitz`), 91–128 (Proposition E.4), 178–219 (Corollary E.7, `corollary:wasserstein-empirical-observables`), pp. 58–60.

**Finding and evidence (established):** "By Proposition E.4, the trajectory convergence implies convergence of empirical averages of 2-pseudo-Lipschitz functions." Proposition E.4 concerns a deterministic sequence of measures; Theorem 4.7 gives $W_2\to0$ in probability for random empirical measures, and the conclusion at mean-field 15–27 is a convergence in probability. The bridge is the subsequence criterion, which is the last sentence of Corollary E.7 (stated without proof; see F17); Corollary E.7 is cited nowhere. The term "2-pseudo-Lipschitz" is used from p. 9 without a pointer to Definition E.3, which says "pseudo-Lipschitz of order $p$". For the score test function one also needs the projection from $(Y,\Delta,R_T)$ to $(Y,R_T)$. The claim itself was verified.

**Consequence:** Local; the preview at mean-field 11–27 is true.

**Proposed repair and completion criterion:** At mean-field 475 cite Corollary~\ref{corollary:wasserstein-empirical-observables} (together with, or instead of, Proposition E.4), and at mean-field 12 write "pseudo-Lipschitz functions of order 2 (Definition~\ref{definition:pseudo-lipschitz})". Complete when the cited result covers convergence in probability and both labels are referenced.

**Dependencies:** F17 (proof of the random case of Corollary E.7); F69 (Corollary E.7 otherwise unused).

**Verification:** M7-02 (unit; confirmed, `M7.low.md`); C1-05 (chain; confirmed, `C1.low.md`); X04-06 (cross; confirmed, `X04.low.md`); also X01-04 point 2.

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f16"></a>

### F16. Claims proved elsewhere cite the wrong result or none (atomlessness, $\bar\tau^t>0$, well-definedness of Definition 4.6)

**Importance:** Low · **Type:** inconsistency (citation) · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 3003–3008 (proof of Corollary 4.8, `cor:mean-field-observables`, part 2, p. 45) and 2858–2860 (proof of Theorem 4.7, p. 44); mean-field 181–185 (text of Definition 4.6, `def:mean-field-recursion`, p. 11) and 502–510 (p. 12).

**Finding and evidence (established):** (1) "The limiting score law is atomless by Theorem 4.7." The statement of Theorem 4.7 (mean-field 429–474) asserts three convergences and nothing about atoms; atomlessness is the last assertion of Lemma B.1 (proof-mean-field 54–58, proved at 192–206), and the first sentence of the proof of Theorem 4.7 restates Lemma B.1 as if it were part of the theorem. (2) Definition 4.6 states unconditionally that well-definedness "is established in Lemma B.1. All its coordinates have finite second moments, and $\tilde r^t$ has an atomless distribution"; Lemma B.1 proves these only under the hypotheses of Theorem 4.7 ($\bar\rho\in(0,1)$, $\ell'$ nonconstant, $\bar\tau^{\rm init}>0$). (3) "$\bar\tau^t>0$" (mean-field 502–510) has no reference; it follows from $\bar C^{[w]}_t\succ0$ in Lemma B.1. All three claims are true.

**Consequence:** Local only.

**Proposed repair and completion criterion:** (1) At proof-mean-field 3003–3004 cite Lemma~\ref{lemma:mf-proof-nondegeneracy}. (2) Prefix the sentence at mean-field 181–185 with "Under the hypotheses of Theorem~\ref{theorem:trajectory}". (3) Cite Lemma~\ref{lemma:mf-proof-nondegeneracy} for $\bar\tau^t>0$. Complete when each claim cites a statement that contains it.

**Dependencies:** Related: F01, F14, F29 (nonnegativity of the alignment regret, item 5 of X01-04).

**Verification:** M7-05 (unit; confirmed, `M7.low.md`); C1-07 (chain; confirmed, `C1.low.md`); X01-04 (cross; confirmed, `X01.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f17"></a>

### F17. Appendix E states nontrivial facts without proof or pinpoint source; two are not in the cited chapter

**Importance:** Low · **Type:** gap / unverified-source · **State:** Open · **resolved?** no

**Location (d430d75):** mathematical-preliminaries 7 ("we follow [Villani, Chapter 6]"), 51–67 (Definition E.2), 91–128 (Proposition E.4, `proposition:wasserstein-convergence-characterization`), 130–145 (Lemma E.5, `lemma:wasserstein-lipschitz-pushforward`), 178–219 (Corollary E.7), pp. 58–60; used at mean-field 475 (p. 12).

**Finding and evidence (established):** The gap task read Villani Chapter 6 in the published book. Items 1–3 of Proposition E.4 are Villani Definition 6.8(i),(iv) with Theorem 6.9, and the facts in Definition E.2 (completeness, separability, density of finitely supported measures) are Villani Theorem 6.18; neither pointer is given here (the first is given at proof-mean-field 1058). Item 4 of Proposition E.4 (pseudo-Lipschitz test functions) is not in Villani Chapter 6 ("pseudo" does not occur) and is unproved; it needs 3⇒4 (pseudo-Lipschitz functions of order $p$ are continuous with $p$-growth) and 4⇒2 (bounded Lipschitz functions and $\|x\|^p$ belong to $\mathrm{PL}_p$, using $|a^p-b^p|\le p|a-b|(a^{p-1}+b^{p-1})$). Lemma E.5 appears in Villani Chapter 6 only for $P_1$; it holds for all $p$ by pushing a coupling forward by $T\times T$, a one-line proof that appears only inside the proof of Theorem 4.7. The random case of Corollary E.7 ("If the matrices are random, the same conclusions hold in probability") needs the subsequence criterion and holds for each fixed test function. The growth claim of Definition E.3 is also unsourced (checked: $|\psi(x)|\le C(1+\|x\|^p)$). All statements are true.

**Consequence:** None for the results; no proof in Appendices A–D depends on E.4(4) or E.7 beyond the remark in F15. A referee cannot check item 4 or Corollary E.7 against the stated source.

**Proposed repair and completion criterion:** Add "[Villani, Definition 6.8 and Theorem 6.9]" to items 1–3 of Proposition E.4 and "[Villani, Theorem 6.18]" to Definition E.2 (or move those claims to a remark); add two-line proofs of item 4, of Lemma E.5, and of the random part of Corollary E.7. Complete when every Appendix E assertion has a precise pointer or a proof.

**Dependencies:** F15, F69 (whether to keep Lemma E.5 and Corollary E.7 at all).

**Verification:** M7-03 (unit; confirmed, `M7.low.md`); X05-03 (cross; confirmed, `X05.low.md`); G1-02-01 (gap task, primary source read; confirmed-with-changes, `G1-02.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f18"></a>

### F18. Theorem 4.7 uses only continuity and linear growth of $\ell'(y,\cdot)$ and $j'$, not the Lipschitz bounds

**Importance:** Low · **Type:** improvement · **State:** Open · **resolved?** no

**Location (d430d75):** mean-field 48–64 (Assumption 4.2, `assumption:regularity-of-loss-and-penalty`, p. 10); uses at proof-mean-field 207–213, 240–244, 353, 2437–2445, 2811–2814.

**Finding and evidence (established):** In the chain Definition 4.6 → Lemma B.1 → Proposition B.4 → Theorem 4.7 → Corollary 4.8, the constants $L_\ell$, $L_j$ enter only through the linear-growth bounds $|\ell'(y,r)|\le C(1+|r|)$, $|j'(u)|\le C(1+|u|)$, and the functions enter Lemma B.5 part 2 only through continuity; Lemma B.1 uses continuity and nonconstancy of $\ell'(y^*,\cdot)$. No step compares $\ell'$ or $j'$ at two points.

**Consequence:** None; Assumption 4.2 is sufficient. Theorem 4.7 holds for continuous $\ell'(y,\cdot)$, $j'$ of at most linear growth.

**Proposed repair and completion criterion:** Optional: leave as is (Section 4.3 uses the Lipschitz form), or add a remark after Theorem 4.7 that continuity and linear growth suffice. Complete when the remark (if added) is checked against the uses listed above.

**Dependencies:** Related: F61 (Assumption 4.2 implied by Assumption 4.1).

**Verification:** C1-04 (chain; confirmed, `C1.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f19"></a>

### F19. The Gram systems of Definition 4.6 become numerically singular; implementations need a pseudo-inverse solve

**Importance:** Low · **Type:** improvement (reproducibility) · **State:** Open · **resolved?** no

**Location (d430d75):** mean-field 181–183, 193–261 (Definition 4.6, `def:mean-field-recursion`, `eq:alpha-w-definition`, `eq:phi-w-definition`, `eq:alpha-g-definition`, `eq:phi-g-definition`, p. 11); numerical 17–22 (Section 5.1, p. 15).

**Finding and evidence (established):** The coefficients are unique solutions of linear systems with Gram matrices $C^{[w]}$, $C^{[g]}$, invertible by Lemma B.1; this is correct but not quantitative. In an implementation written from the paper: Figure 1 regime, $\mathrm{cond}\,C^{[w]}$ grows from $2\cdot10^6$ at $t=5$ to $10^{10}$ at $t=300$; Figure 2 balanced regime, $5\cdot10^{14}$ at $t=400$; at $\pi=0$ (allowed at mean-field 112), $\bar v^{[w]}_5\approx10^{-5}$ and $\mathrm{cond}\approx10^{16}$ by $t=10$, so a literal `numpy.linalg.solve` aborts or diverges after $t\approx30$ ($\bar\tau^{100}\approx2.5\cdot10^3$ against $1.28$). A least-squares (Moore–Penrose) solve restores agreement to about $0.01$. The projections and memory terms do not depend on the choice of generalized inverse.

**Consequence:** None for the stated results; affects reproducibility of the particle method.

**Proposed repair and completion criterion:** Optional: one sentence in Section 5.1 saying that the coefficient systems are solved by least squares because the Gram matrices become ill-conditioned, and optionally a note after Definition 4.6 that the projections are unchanged under the pseudo-inverse. Complete when the sentence is present and matches the code's solver.

**Dependencies:** none.

**Verification:** X13-02 (independent simulation; confirmed, `X13.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f20"></a>

### F20. The initialization assumptions exclude labeled-data warm starts and zero initialization, and the roles of the assumptions are not discussed

**Importance:** Low · **Type:** improvement (scope discussion) · **State:** Open · **resolved?** no

**Location (d430d75):** mean-field 65–107 (Assumption 4.3, `assumption:quenched-initialization`, p. 10); proof-mean-field 106–122 (p. 26); long-time-behavior 60–82 (Assumption 4.4, p. 14); numerical 36, 196 (captions); compare setting 279–288 (logistic loss and ridge penalty satisfy the conditions, p. 7).

**Finding and evidence (established):** $b^{\rm init}$ and $w^{\rm init}$ are deterministic with $(\bar\tau^{\rm init})^2>0$. A practical teacher fitted on $\mathcal D_{\mathcal L}$ depends on $U_{\mathcal L}$ and is excluded: the proof assumes $\mathcal F_0$ trivial (proof-mean-field 535, 593), so a teacher fitted to convergence needs a new argument; only warm starts produced by finitely many labeled-only gradient steps could be reached by a time-varying $\pi_t$, which Theorem 4.7 does not cover. Zero initialization is excluded because item (iii) starts the Gram-matrix nondegeneracy induction (proof-mean-field 106–122), so it is structural. The paper also does not discuss isotropic Gaussian noise and universality, the exclusion of the hinge loss (by $C^2$ smoothness and $\ell''>0$ in Assumption 4.1), the long-time class (logistic-type losses with bounded $\ell'$ and smooth strongly convex penalties), or that random $(Y,\Delta)$ are covered by conditioning. The experiments are within the theory's hypotheses.

**Consequence:** Limits the practical reading of Theorems 4.7 and 4.10 and Section 5; nothing is false.

**Proposed repair and completion criterion:** Optional: a short "discussion of assumptions" paragraph covering the role of each condition, the excluded initializations, and the conditioning remark; any claimed extension (e.g. time-varying $\pi_t$) only if stated and proved. Complete when the paragraph exists and makes no unproved claim.

**Dependencies:** Related: F42 (introduction precision).

**Verification:** X10-05 (cross; v1, v2 confirmed-with-changes, both lowering Medium to Low, `X10-05.v1.md`, `X10-05.v2.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f21"></a>

### F21. Corollary 4.11's last identity is claimed $\tilde{\mathbb P}$-a.s., but Theorem 4.10 determines $\tilde{\mathfrak c}^{\infty}$ only $\tilde{\mathbb P}_{\mathcal U}$-a.s.

**Importance:** Low · **Type:** inconsistency (statement vs proof) · **State:** Open · **resolved?** no

**Location (d430d75):** long-time-behavior 237–251 (Corollary 4.11, `cor:mean-field-selection-stabilization`, last display, p. 15) and 166–175 (Theorem 4.10, `thm:effective-process-convergence`, p. 14); proof-long-time 1194–1212 and 1284–1291 (p. 55).

**Finding and evidence (established):** "If $\tilde{\mathbb P}(\tilde r^\infty\in\{\kappa_-,\kappa_+\})=0$, then $\tilde{\mathfrak c}^\infty=\mathbf 1\{\tilde r^\infty\ge\kappa_+\}-\mathbf 1\{\tilde r^\infty\le\kappa_-\}$, $\tilde{\mathbb P}$-almost surely." Theorem 4.10 asserts only that some $\tilde{\mathfrak c}^\infty$ exists with $\tilde{\mathfrak c}^t=\tilde{\mathfrak c}^\infty$ eventually, $\tilde{\mathbb P}_{\mathcal U}$-a.s.; its value on $\{\tilde\Delta=1\}$ is unconstrained by the statement. The proof of Theorem 4.10 defines it there to be the right-hand side (1202–1205), and the corollary's proof gets the identity "by the chosen extension" (1289–1290). On labeled observations the identity is a definition with no content (no convergence of $\tilde{\mathfrak c}^t$ is proved there; Proposition C.3 controls unlabeled switching only), and it can fail on a set of probability $\bar\rho$ for another variable allowed by the theorem's statement. The argument on $\{\tilde\Delta=0\}$ is correct.

**Consequence:** Local to the last claim of Corollary 4.11; the limits and total-variation bounds for $\bar\omega^t$, $\bar e^t$ use only $\{\tilde\Delta=0\}$ and are unaffected.

**Proposed repair and completion criterion:** State the identity and the atom condition under $\tilde{\mathbb P}_{\mathcal U}$, define $\tilde{\mathfrak c}^\infty:=\limsup_t\tilde{\mathfrak c}^t$ everywhere, and delete the $\tilde\Delta=1$ case (proof-long-time 1202–1205, 1211–1212, 1289–1291); or keep "$\tilde{\mathbb P}$-almost surely" and move the extension into the statement of Theorem 4.10. Complete when the corollary uses only properties of $\tilde{\mathfrak c}^\infty$ stated in Theorem 4.10.

**Dependencies:** F22 (the atom condition can also be weakened).

**Verification:** L3-01 (unit), C2-02 (chain), X01-02, X04-13 (cross); all confirmed (`L3.low.md`, `C2.low.md`, `X01.low.md`, `X04.low.md`); also G1-04-03 point 3 (single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f22"></a>

### F22. The atom condition in Corollary 4.11 is stronger than the proof needs

**Importance:** Low · **Type:** improvement · **State:** Open · **resolved?** no

**Location (d430d75):** long-time-behavior 237–251 (Corollary 4.11, p. 15); proof-long-time 1265–1288 (p. 55).

**Finding and evidence (established):** The same subsequence argument gives, $\tilde{\mathbb P}_{\mathcal U}$-a.s. and with no extra condition, $\{\tilde{\mathfrak c}^\infty=+1\}\subseteq\{\tilde r^\infty\ge\kappa_+\}$, $\{\tilde{\mathfrak c}^\infty=-1\}\subseteq\{\tilde r^\infty\le\kappa_-\}$, and $\{\tilde{\mathfrak c}^\infty=0\}\subseteq\{\kappa_-\le\tilde r^\infty\le\kappa_+\}$. Because the thresholds are inclusive, the identity can fail only on $\{\tilde{\mathfrak c}^\infty=0,\ \tilde r^\infty\in\{\kappa_-,\kappa_+\}\}$; it holds iff that event is $\tilde{\mathbb P}_{\mathcal U}$-null. The stated condition also restricts labeled and selected observations, where nothing is needed. The paper does not verify the condition in any example; finite-time atomlessness (Lemma B.1) does not pass to an $L^2$ limit. (The long-time simulation found the scores depleted near the thresholds but without atoms.)

**Consequence:** None for correctness; the corollary could say more under a weaker hypothesis.

**Proposed repair and completion criterion:** Optional: replace the condition by $\tilde{\mathbb P}_{\mathcal U}(\tilde r^\infty\in\{\kappa_-,\kappa_+\})=0$, or state the three inclusions unconditionally and the identity under $\tilde{\mathbb P}_{\mathcal U}(\tilde{\mathfrak c}^\infty=0,\tilde r^\infty\in\{\kappa_\pm\})=0$. Complete when a checker re-derives the three inclusions.

**Dependencies:** F21.

**Verification:** L3-02 (unit; confirmed, `L3.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f23"></a>

### F23. Limit (117) of the two-time switching indicator is asserted without citing the results that justify it

**Importance:** Low · **Type:** gap (citation) · **State:** Open · **resolved?** no

**Location (d430d75):** proof-long-time 46–68 (display (117), `eq:long-time-configuration-limit`, p. 47); reused at 112 (proof of Proposition 4.9), 546 (Proposition C.3), 1078–1084 (Lemma C.5).

**Finding and evidence (established):** "For every fixed $s,t\ge1$, Theorem 4.7 gives … $h(s,t)\to\bar h(s,t)$ … Finite-time atomlessness therefore allows the empirical convergence to pass through this indicator." The statement of Theorem 4.7 gives $W_2$ convergence in probability only; it contains neither the absence of atoms at $\kappa_\pm$ nor a continuous-mapping statement for discontinuous test functions. Both exist in the paper: Lemma B.1 and Lemma B.5 part 2, used exactly this way for $\omega^t$ in the proof of Corollary 4.8 (proof-mean-field 2965–3010). The chain auditor checked that Lemma B.5(2) applies (bounded map; discontinuity set null by the marginal statement of Lemma B.1). The step is correct, but Proposition 4.9, Proposition C.3, and Lemma C.5 all rest on this one uncited sentence.

**Consequence:** None once the citation is added.

**Proposed repair and completion criterion:** After line 68 add: apply Lemma~\ref{lemma:mf-proof-empirical-stability}, part 2, to the array $[\Delta\mid r^s\mid r^t]$ with coefficient $(1-\rho)^{-1}\to(1-\bar\rho)^{-1}$ and map $F(c,(a,r,r')):=c(1-a)\mathbf 1\{c_\kappa(r)\ne c_\kappa(r')\}$, continuous outside a set that is null by Lemma~\ref{lemma:mf-proof-nondegeneracy}. Complete when (117) is tied to these two lemmas.

**Dependencies:** Related: F70 ((116) unused), F26 ($t\ge0$).

**Verification:** C2-05 (chain; confirmed, `C2.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f24"></a>

### F24. Proposition C.3 and the stabilization conclusions use fewer hypotheses than stated

**Importance:** Low · **Type:** improvement · **State:** Open · **resolved?** no

**Location (d430d75):** proof-long-time 124–125, 319–344, 346–567 (Proposition C.3, `prop:mean-field-configuration-switching`, pp. 47, 49–51), 1176–1264 (p. 55); long-time-behavior 139–176, 201–236 (Theorem 4.10, Corollary 4.11, pp. 14–15).

**Finding and evidence (established):** Proposition C.3 is stated under "the hypotheses of Theorem 4.10", which include Assumption 4.4, $\lambda>0$, and $\bar p_{\mathcal L}\in(0,1)$. Its proof uses the Gaussian design and $M/(d-1)\to(1-\bar\rho)\bar\delta$; $\ell''\le L_\ell$ and the signs $\ell'(-1,\kappa_-)>0>\ell'(+1,\kappa_+)$ from Assumption 4.1(1) (for any thresholds with $\kappa_-<\kappa_+$); $\pi>0$; two components of $\mathcal E_d$; the fixed-time limits from Theorem 4.7; and Proposition C.2, which rests on Lemma A.1 and the step-size condition. $B_\ell$, $m_j$, $j(0)=j'(0)=0$, $\lambda>0$, and $\bar p_{\mathcal L}\in(0,1)$ enter only through Lemmas C.4 and C.5. So the almost-sure eventual stabilization of $\tilde{\mathfrak c}^t$ (1176–1192) and the limits and finite total variation of $\bar\omega^t$, $\bar e^t$ (1216–1264) follow from the hypotheses of Theorem 4.7, Assumption 4.1, $\pi>0$, and the step-size condition alone.

**Consequence:** None for correctness. The paper could state that stabilization of the pseudo-label configuration needs no strongly convex penalty, bounded loss derivative, or two labeled classes; only convergence of $\tilde\theta^t$ and $\tilde r^t$ does.

**Proposed repair and completion criterion:** Optional: state in Proposition C.3 the hypotheses actually used, and optionally add a remark after Theorem 4.10 separating the hypotheses of the stabilization claim from those of the convergence claim. Complete when a checker confirms Propositions C.2–C.3 and the fixed-time limits invoke nothing else.

**Dependencies:** Related: F04, F60.

**Verification:** L2-02 (unit; confirmed, `L2.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f25"></a>

### F25. The long-time step-size condition is valid but about three times more conservative than necessary

**Importance:** Low · **Type:** improvement · **State:** Open · **resolved?** no

**Location (d430d75):** long-time-behavior 110–137 (`eq:s-mu-k-bar`, `eq:lambda-bd`, `eq:mean-field-long-time-step-size`, p. 14); used through Lemma C.1 (`lem:st-deterministic-curvature-bound`) and Proposition C.2, proof-long-time 134–200 (pp. 47–48).

**Finding and evidence (established):** The theorem requires $0<\eta<2/\Lambda_{\rm bd}$ with $\Lambda_{\rm bd}:=\lambda L_j+L_\ell(1+\bar K_{\mathcal L}^2)+\pi L_\ell(1+\bar K_{\mathcal U}^2)$. Appendix C uses $\Lambda_{\rm bd}$ only to produce a deterministic $\Lambda_*<2/\eta$ with $\mathbb P(\Lambda_d\le\Lambda_*)\to1$ (proof-long-time 137, 199). Two independent simulations: in configuration A ($\sigma=1$, $\bar\delta=2$, $\bar\rho=0.2$, $\bar s_\mu=1.5$, $\lambda=0.5$, $\pi=1$), $\Lambda_{\rm bd}=7.87$ ($\eta<0.254$) while $\Lambda_d=2.71$–$2.91$ for $d=250$–$16000$, and the effective process converges at $\eta=0.6$–$0.75$; in the two figure settings, $\Lambda_d\approx3.8$–$3.9$ against $\Lambda_{\rm bd}\approx11.07$, and $\approx2.3$ against $6.85$. The slack comes from triangle inequalities and the global curvature bound. Both figures satisfy the condition. This is a sufficient condition, not an error.

**Consequence:** None for correctness. The hypotheses of Theorem 4.10 are nonvacuous but exclude step sizes that Theorem 4.4 allows and that converge in practice; readers may take the condition as sharp.

**Proposed repair and completion criterion:** Optional: state Lemma C.1 "for every deterministic $\Lambda_*>\Lambda_{\rm bd}$", and add one sentence after `eq:mean-field-long-time-step-size` that the condition is sufficient and that the proofs need only a deterministic $\Lambda_*<2/\eta$ with $\mathbb P(\Lambda_d\le\Lambda_*)\to1$. Complete when a checker confirms Lemma C.1 and Proposition C.2 use only this property.

**Dependencies:** none.

**Verification:** L1-05 (unit; confirmed, `L1.low.md`); G1-04-02 (gap-task simulation; confirmed, `G1-04.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f26"></a>

### F26. The restrictions to $t\ge1$ in Proposition 4.9, the fixed-time limits, and Proposition C.2 are not needed

**Importance:** Low · **Type:** improvement · **State:** Open · **resolved?** no

**Location (d430d75):** long-time-behavior 46–49 (Proposition 4.9, `prop:identification-time-divergence`, p. 13); proof-long-time 37, 46, 74, 205, 223 ((115)–(117), Proposition C.2, pp. 46–48).

**Finding and evidence (established):** "$\bar h(t,t+1)>0$ for every finite $t\ge1$"; limits "for every fixed $s,t\ge1$"; $\bar V^t$ and its descent "for every $t\ge1$". Each holds for $t\ge0$ with the same proof: $\tilde c^0$ is $\mathcal H^{[g]}_1$-measurable and $\bar v^{[w]}_1>0$ by Lemma B.1, so $\bar h(0,1)>0$; $\tilde r^0$ is atomless since $\bar v^{[w]}_0=\bar\tau^{\rm init}>0$; the descent inequality (64) holds at every $\theta$. The restriction mirrors the convention $T_{\rm id}\ge1$ of Theorem 4.4. ("Finite" is redundant for an integer $t$.)

**Consequence:** Local; the stated results are slightly weaker than what is proved.

**Proposed repair and completion criterion:** Optional: write $t\ge0$ in Proposition 4.9 (dropping "finite"), or add a half-sentence that $t=0$ is included. No downstream change required. Complete when Proposition 4.9, the fixed-time limits (115)–(117), and Proposition C.2 state $t\ge0$ (or $t=0$ is noted as included), or the authors decline the optional change.

**Dependencies:** Related: F23.

**Verification:** L1-04 (unit; confirmed, `L1.low.md`); also X01-09 point 6 and G1-04-03 point 1 (single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f27"></a>

### F27. The long-time limit is not characterized, has no rate, and convergence of the limiting error is not stated

**Importance:** Low · **Type:** improvement (scope) · **State:** Open · **resolved?** no

**Location (d430d75):** long-time-behavior 139–252 (Theorem 4.10, `thm:effective-process-convergence`; Corollary 4.11, pp. 14–15); introduction 91–92, 121–127 (pp. 2–3); numerical 381–402 (p. 18).

**Finding and evidence (established):** Theorem 4.10 gives existence of $\tilde\theta^\infty$, $\tilde r^\infty$ with convergence in $\mathcal H$ and $L^2$, and eventual stabilization of the configuration. The paper gives no fixed-point equations for the limit and no rate. Corollary 4.11's identification of $\tilde{\mathfrak c}^\infty$ requires an atom condition on $\tilde r^\infty$ that cannot be checked because its law is not characterized (F22). Convergence of the limiting classification error is not stated: Theorem 4.10 implies convergence of $\bar b^t$, $\bar m^t$, $\bar\tau^t$, but the error formula needs $\bar\tau^\infty>0$, which is unproved (Lemma B.1 covers finite $t$ only). Nothing relates $\tilde\theta^\infty$ to the large-$d$ behavior of the finite-$d$ limit $\theta^\star_{\mathfrak c}$, and Proposition 4.9 concerns exact identification only. Introduction question 1 is answered at fixed $d$ by Theorem 4.4 (the limit is the branch minimizer $\theta^\star_{\mathfrak c}$); what is missing concerns only the mean-field regime. The long-time simulation (G1-04) found all observables stabilizing, including one admissible configuration that converges after a long transient to a collapsed limit (48% of selected pseudo-labels wrong).

**Consequence:** Limited significance of Theorem 4.10 and Corollary 4.11; nothing is false. Contribution 3 accurately claims convergence and stabilization only.

**Proposed repair and completion criterion:** Optional: one remark after Corollary 4.11 (or in numerical 381–402) stating that $\bar b^t$, $\bar m^t$, $\bar\tau^t$ converge, that the error converges whenever $\bar\tau^\infty>0$, that the limit is not characterized, and that the interchange of limits is open. Complete when the remark is present and makes no unproved claim.

**Dependencies:** Related: F22, F42 (order of limits in the introduction), F74.

**Verification:** X10-02 (cross; v1, v2 confirmed-with-changes, both lowering Medium to Low, `X10-02.v1.md`, `X10-02.v2.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f28"></a>

### F28. Proposition 5.1 states no standing hypotheses and does not name the quantity whose limit it asserts

**Importance:** Low · **Type:** gap (statement) · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 84–120 (Proposition 5.1, `prop:bayes-risk`, `eq:bayes-classification-error`, p. 16); proof at proof-numerical 41–73 (p. 56), in particular 71.

**Finding and evidence (established):** "Suppose $\bar s_\mu>0$. … The Bayes classification error of the test mixture converges, as $d\to\infty$, to $\bar{\mathcal E}_{\rm B}:=\mathcal E_{\bar p}(\alpha^\star,\beta^\star)$." (1) The only hypothesis is $\bar s_\mu>0$; the proof concludes from "$s_\mu\to\bar s_\mu>0$ and $p\to\bar p\in(0,1)$", which are Assumption 3.1, cited nowhere; $\bar p\in(0,1)$ is needed for $\beta_\star(\alpha^\star;\bar p)$ to be finite. (2) $\bar s_\mu=(\tilde{\mathbb E}[\tilde\mu^2])^{1/2}$ is defined through $\tilde\mu$, the first marginal of $\bar\nu_{(\mu,w^{\rm init})}$ (Assumption 4.3), and $s_\mu\to\bar s_\mu$ needs that this marginal is $\bar\nu_\mu$ (true, unstated; see F63). (3) "The Bayes classification error of the test mixture" has no symbol; the finite-dimensional $\mathcal E_{\rm B}$ appears at numerical 169–181, and the test law (positive-class probability $p$) is defined only inside Corollary 4.8. (4) $\bar s_\mu>0$ precedes the first assertion, which does not depend on it. The auditor re-derived the proof and confirmed the limit under Assumptions 3.1 and 4.3.

**Consequence:** Local. The second assertion is unsupported as stated and complete once the assumptions are added.

**Proposed repair and completion criterion:** Restate: "Suppose Assumption~\ref{assumption:asymptotic-regime} holds. (i) For every $\alpha>0$ and $p\in(0,1)$ the unique minimizer of $\beta\mapsto\mathcal E_p(\alpha,\beta)$ is $\beta_\star(\alpha;p)$. (ii) If $\bar s_\mu>0$, the Bayes classification error of the test observation of Corollary~\ref{cor:mean-field-observables}, $\mathcal E_{\rm B}:=\mathcal E_p(s_\mu/\sigma,\beta_\star(s_\mu/\sigma;p))$ with $s_\mu:=\|\mu\|/\sqrt d$, converges to $\bar{\mathcal E}_{\rm B}$." Move the definitions of $s_\mu$ and $\mathcal E_{\rm B}$ before the proposition; alternatively define $\bar s_\mu$ through $\bar\nu_\mu$ so that only Assumption 3.1 is needed. Complete when every limit at proof-numerical 71 follows from the stated hypotheses.

**Dependencies:** F62 ($\bar p\in(0,1)$), F63 ($\bar\nu_\mu$), F31 ($\bar s_\mu>0$ removable).

**Verification:** N1-01 (unit; confirmed, `N1.low.md`); X01-05 (cross; confirmed, `X01.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f29"></a>

### F29. The proof of Proposition 5.1 proves a claim not in its statement, while nonnegativity of the alignment regret is asserted without a reason

**Importance:** Low · **Type:** inconsistency (statement vs proof) · **State:** Open · **resolved?** no

**Location (d430d75):** proof-numerical 16–39 (proof of Proposition 5.1, p. 56); numerical 156 (after `eq:classification-regret-decomposition`, p. 16).

**Finding and evidence (established):** The proof's middle paragraph shows $|\bar\alpha^t|\le\bar s_\mu/\sigma$ by Cauchy–Schwarz and that "the smallest error attainable by the normalized parameters is $\mathcal E_{\bar p}(\alpha^\star,\beta^\star)$", i.e. $\inf_{|\alpha|\le\alpha^\star,\beta}\mathcal E_{\bar p}(\alpha,\beta)=\mathcal E_{\bar p}(\alpha^\star,\beta^\star)$. Proposition 5.1 asserts neither; this paragraph is not needed for either assertion, and it uses objects of the effective recursion that exist only under the hypotheses of Theorem 4.7, not assumed in Proposition 5.1. Conversely, it is exactly what makes $\bar{\mathcal R}^t_{\rm align}\ge0$ true ($\bar\alpha^t\le\alpha^\star$ and $\mathcal E^{\rm opt}$ decreasing in $\alpha$), yet numerical 156 says "Both quantities are nonnegative" with no pointer. The two-step argument and the monotonicity were verified (20,000 random pairs, no violation).

**Consequence:** Local; all statements are true, but the dependence is hidden.

**Proposed repair and completion criterion:** Either add a third assertion to Proposition 5.1 under the hypotheses of Theorem 4.7 ("for every finite $t$, $|\bar\alpha^t|\le\alpha^\star$ and $\mathcal E^{\rm opt}_{\bar p}(\bar\alpha^t)\ge\bar{\mathcal E}_{\rm B}$"), or move the paragraph to the text after `eq:classification-regret-decomposition` as the justification of nonnegativity. Complete when the proof of Proposition 5.1 proves exactly its statement and the nonnegativity claim has a stated reason.

**Dependencies:** F28, F30.

**Verification:** N1-02 (unit; confirmed, `N1.low.md`); X01-04 point 5 (confirmed, `X01.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f30"></a>

### F30. The finite-dimensional regret decomposition omits its conditions and the identity it rests on

**Importance:** Low · **Type:** gap · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 68–70, 169–181 (Section 5.2, `subsec:classification-error`, p. 16); identity at proof-mean-field 3044–3084 (proof of Corollary 4.8, p. 46).

**Finding and evidence (established):** "For finite-dimensional trajectories, we use the same decomposition with $(p,\alpha^t,\beta^t)$ and the finite-dimensional Bayes error $\mathcal E_{\rm B}:=\mathcal E_p(s_\mu/\sigma,\beta_\star(s_\mu/\sigma;p))$." Three facts are needed and none is stated: (1) $\mathcal E_{\rm B}$ is defined only when $s_\mu>0$ and $p\in(0,1)$ (the text mentions only $\tau^t>0$); (2) "the same decomposition" presupposes the exact identity $\mathcal E^t=\mathcal E_p(\alpha^t,\beta^t)$ on $\{\tau^t>0\}$, which appears only inside the proof of Corollary 4.8; (3) nonnegativity of the finite-dimensional alignment regret needs $|\alpha^t|\le s_\mu/\sigma$ (Cauchy–Schwarz). All three hold, and Figure 2's settings satisfy the conditions.

**Consequence:** Local; affects the reading of Figure 2's layers, not their correctness.

**Proposed repair and completion criterion:** Add one sentence: "For all $d$ with $\tau^t>0$, $s_\mu>0$ and $p\in(0,1)$, the conditional test error satisfies $\mathcal E^t=\mathcal E_p(\alpha^t,\beta^t)$ and $|\alpha^t|\le s_\mu/\sigma$, so the same decomposition applies with nonnegative terms," with a pointer to the proof of Corollary~\ref{cor:mean-field-observables}. Complete when the conditions are stated and the identity is referenced.

**Dependencies:** F29.

**Verification:** N1-03 (unit; confirmed, `N1.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f31"></a>

### F31. The hypothesis $\bar s_\mu>0$ can be removed from Proposition 5.1 and the regret definitions

**Importance:** Low · **Type:** improvement · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 95, 107–118, 140 (Proposition 5.1, `prop:bayes-risk`; `eq:classification-regret-decomposition`, p. 16).

**Finding and evidence (established):** $\bar s_\mu>0$ is needed only because $\beta^\star=\beta_\star(\alpha^\star;\bar p)$ divides by $\alpha^\star$. With the paper's own $\mathcal E^{\rm opt}_p$, the Bayes error at dimension $d$ is $\mathcal E^{\rm opt}_p(s_\mu/\sigma)$ for every $s_\mu\ge0$ (for $\mu=0$ it is $\min\{p,1-p\}=\mathcal E^{\rm opt}_p(0)$), and $(p,\alpha)\mapsto\mathcal E^{\rm opt}_p(\alpha)$ is continuous because $\sup_\beta|\mathcal E_p(\alpha,\beta)-\mathcal E_{p'}(\alpha',\beta)|\le|p-p'|+|\alpha-\alpha'|/\sqrt{2\pi}$. So the Bayes error converges to $\mathcal E^{\rm opt}_{\bar p}(\bar s_\mu/\sigma)$ whether or not $\bar s_\mu>0$. Numerically, at $p=0.2$ the Bayes error is $0.2000$ for $s_\mu\in\{10^{-1},10^{-2},10^{-3}\}$.

**Consequence:** None for correctness; the alignment regret would be defined in every case.

**Proposed repair and completion criterion:** Optional: define $\bar{\mathcal E}_{\rm B}:=\mathcal E^{\rm opt}_{\bar p}(\bar s_\mu/\sigma)$ (defining $\mathcal E^{\rm opt}_p$ before the proposition), note that it equals $\mathcal E_{\bar p}(\alpha^\star,\beta^\star)$ when $\bar s_\mu>0$, and drop "Assuming $\bar s_\mu>0$". Complete when a checker confirms the continuity bound.

**Dependencies:** F28.

**Verification:** N1-05 (unit; confirmed, `N1.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f32"></a>

### F32. The finite selected-error fraction $e^t$ in Figure 1 is undefined, and the caption does not explain its symbols or runs

**Importance:** Low · **Type:** inconsistency (figure vs text) · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 28–42 (Figure 1, `fig:mean-field-validation`, third panel and caption 32–40, p. 15); mean-field 494–501, 514–564 (Corollary 4.8, pp. 12–13); long-time-behavior 207–216 ($\bar e^t$, Corollary 4.11, p. 15). Code `e823bf3`: `src/callbacks.py` 273–278.

**Finding and evidence (established):** The panel "Selected-error fraction $e^t$" compares the algorithm with the effective process. The code computes $e^t=\frac1M\sum_{j\in I_{\mathcal U}}S_\kappa(r_j^t)\mathbf 1\{\operatorname{sign}(r_j^t)\ne Y_j\}$, unconditional on selection, which matches $\bar e^t$ of Corollary 4.11; but the paper defines no finite-dimensional $e^t$ ($e^t$ denotes a vector in proof-long-time 487–526), and Corollary 4.8 does not state $e^t\to\bar e^t$ (it follows as for $\omega^t$, by atomlessness at $\{\kappa_\pm\}$). The effective curves carry unbarred symbols. The caption does not say that each of the 20 runs redraws $\mu$, $w^{\rm init}$, the data, and the particle system, so that the orange bands include particle Monte Carlo error, or that the bands are interquartile ranges.

**Consequence:** Local; a plotted quantity has no definition or supporting statement.

**Proposed repair and completion criterion:** Define $e^t:=M^{-1}\sum_{j}\mathbf 1\{\mathfrak c_j(\theta^t)=-Y_j\}$ next to `eq:finite-dimensional-trajectory-observables`, define $\bar e^t$ next to $\bar\omega^t$ in Corollary 4.8 and add $e^t\to\bar e^t$ with the $\omega^t$ argument; use barred symbols for the effective curves or explain them in the caption; state what each run redraws. Complete when every Figure 1 symbol is defined before p. 15.

**Dependencies:** F02 (same figure).

**Verification:** X09-02 (code; confirmed, `X09.low.md`); X02-06 (cross; confirmed-with-changes, `X02.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f33"></a>

### F33. The code draws labels and supervision indicators i.i.d. and evaluates errors at the configured $p$, not the realized proportion

**Importance:** Low · **Type:** inconsistency (paper–code) · **State:** Open · **resolved?** no

**Location (d430d75):** setting 13–18, 54 (Definition 3.1, p. 5); mean-field 542–545 (Corollary 4.8, p. 13); numerical 36–37, 169–181, 196–197 (captions and Section 5.2, pp. 15–17). Code `e823bf3`: `src/environment.py` 125–132; `figures/experiments.py` 92, 112, 117–119, 183.

**Finding and evidence (established):** The paper's model is quenched, with $\mathcal E^t$ and $\mathcal E_{\rm B}$ evaluated at the realized proportion $p$. The code draws $(Y_i,\Delta_i)$ i.i.d. from the product law and then holds them fixed (conditionally an instance of the paper's model), but evaluates the population error and Bayes benchmarks at the configured `label_prior`; the deviation is $O(n^{-1/2})$ (standard deviation about $0.003$). The captions read as if $p$ and $\rho$ were exact proportions.

**Consequence:** No visible effect on the figures; wording and provenance only.

**Proposed repair and completion criterion:** Caption: "$(Y_i,\Delta_i)$ drawn i.i.d. with $\mathbb P(Y_i=+1)=p$ and $\mathbb P(\Delta_i=1)=\rho$, independently, then held fixed"; optionally evaluate at the realized $p$. Complete when caption and code agree.

**Dependencies:** none.

**Verification:** X09-06 (code; confirmed, `X09.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f34"></a>

### F34. The code documentation reuses the paper's residual symbols under a $-\eta$ convention and cites a nonexistent manuscript section

**Importance:** Low · **Type:** inconsistency (paper–code documentation) · **State:** Open · **resolved?** no

**Location (d430d75 / e823bf3):** paper mean-field 207–250, 374–419 (Definition 4.6, `eq:g-U-definition`, `eq:w-update-definition`, pp. 11–12), numerical 21 (p. 15). Code `e823bf3`: `docs/effective_process.md` 6–7, 79–91, 137–147, 191–249; `ARCHITECTURE.md` 55–79, 113–114.

**Finding and evidence (established):** The code docs define $g_i^t=-\eta_w[\Delta_i/\rho\,\ell'+(1-\Delta_i)\pi/(1-\rho)S\ell']$ and the update $w^{t+1}=w^t+h^t+\chi^t\mu+\dots$, naming the coefficients like the paper. The paper's $\tilde g^t$ has no $-\eta$ factor and its update subtracts $\eta[\bar\chi\mu+\sigma\bar\delta^{-1/2}\tilde p]$. So code $g,p,\chi,\zeta$ equal $-\eta$ times the paper's quantities, $C^{[g]}$ scales by $\eta^2$, $\alpha$ is unchanged, $\phi^{[g]}$ scales by $-\eta$ and $\phi^{[w]}$ by $-1/\eta$ (checked from the defining linear systems). `ARCHITECTURE.md` 113–114 states the convention but gives no conversion. `docs/effective_process.md` 7 says "The accompanying manuscript section, Implementation Details, supplies the mathematical interpretation", but no such section exists at `d430d75` (numerical 21 points back to the repository). This was item 4/5d of the November 4 code-repository audit and remains partly open.

**Consequence:** Local. The plotted observables do not depend on the sign or scale of $g$, and the figures reproduce pixel-identically; a reader comparing signed residual diagnostics or memory coefficients between paper and code would be misled.

**Proposed repair and completion criterion:** In `docs/effective_process.md`, replace the "Implementation Details" sentence by a pointer to Definition 4.6 and Section 5.1, and add a short correspondence table (code $g,p,\chi,\zeta=-\eta\times$ paper; $C^{[g]}$ scaled by $\eta^2$; $\alpha$ unchanged; $\phi^{[g]}$ by $-\eta$, $\phi^{[w]}$ by $-1/\eta$). Complete when the table is present and no nonexistent manuscript section is cited.

**Dependencies:** none (companion repository only).

**Verification:** X11-01 (regression check; confirmed-with-changes, `X11.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f35"></a>

### F35. Figure 1 is cited as the "accompanying evolution" of the Figure 2 discussion but uses another configuration, and the normalized intercept is shown in no figure

**Importance:** Low · **Type:** inconsistency (text vs figures) · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 220–225 (Section 5.3, p. 17); captions 32–40 (Figure 1, `fig:mean-field-validation`, p. 15) and 188–198 (Figure 2, `fig:class-imbalance-regret`, p. 17).

**Finding and evidence (established):** "The normalized intercept moves far beyond its classification-optimal value … Figure 1 shows the accompanying evolution of the intercept, signal alignment, and weight norm." The discussion concerns the Figure 2 imbalanced run ($d=5000$, $\rho=0.05$, $\eta=0.2$, $\pi=2$, $T=400$, one realization); Figure 1 uses $d=2000$, $\rho=0.1$, $\eta=0.1$, $\pi=5$, $T=300$, 20 runs. Figure 1 is itself an imbalanced ($p=0.2$) experiment with a U-shaped error (minimum about $0.150$ at $t\approx120$, $0.183$ at $t=300$) and plots $b^t$, $m^t$, $\tau^t$, so the reference is imprecise rather than wrong; but "accompanying" implies the Figure 2 run, and neither figure plots $\beta^t=b^t/(\sigma\tau^t)$ or $\beta_\star(\alpha^t;p)$. The overshoot is real: from Figure 1's data at $t=300$, $\beta\approx-1.88$ against $\beta_\star\approx-1.07$ ($\beta\approx\beta_\star$ at the error minimum); in simulations at the Figure 2 configuration, $\beta^T/\beta_\star\approx1.57$ (30 seeds), and the effective process shows the same pattern.

**Consequence:** Local; the reader is pointed to evidence from a different experiment, and the overshoot claim points to no displayed quantity.

**Proposed repair and completion criterion:** Say "Figure 1, for a related imbalanced configuration ($p=0.2$), shows …", and either add a panel of $\beta^t$ against $\beta_\star(\alpha^t;p)$ for the Figure 2 run or report the numbers. Complete when the cited figure matches the configuration and the overshoot claim points to a displayed quantity.

**Dependencies:** F03, F36, F37.

**Verification:** X02-03 (cross; v1, v2 confirmed-with-changes, both lowering Medium to Low, `X02-03.v1.md`, `X02-03.v2.md`); X09-04 (code; confirmed-with-changes, `X09.low.md`); G1-01-03 (gap-task simulation; confirmed, `G1-01.low.md`); X10-04 (figure-reference part); X13-04 point 2 (single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f36"></a>

### F36. The intercept-feedback explanation omits that most of the late error rise in Figure 2 is alignment regret

**Importance:** Low · **Type:** overclaim (interpretation) · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 220–231 (Section 5.3, p. 17); Figure 2 right panel (`fig:class-imbalance-regret`, p. 17).

**Finding and evidence (established):** "Intercept regret begins increasing before alignment regret … classification error approaches the majority-class benchmark … Together, these observations suggest an important role for intercept feedback in the deterioration observed under class imbalance." From the stored data behind Figure 2: the error reaches its minimum $0.1637$ at $t=88$; intercept regret starts rising at $t=83$ and alignment regret at $t=101$, so the first sentence is correct (also confirmed in 30/30 independent seeds). The rise from $t=88$ to $168$ ($+0.025$) is mostly intercept regret ($+0.014$), but of the total rise to $t=400$ ($+0.035$), about 89% is alignment regret ($+0.031$; final alignment regret $0.081$, intercept regret $0.004$). The approach to $0.2$ comes from the normalized alignment falling ($\alpha$ from about $0.68$ to $0.41$). The text is hedged ("suggest"), and the intervention sentences (F03) bear on it, but the long-run split is not mentioned.

**Consequence:** Interpretation in Section 5.3 and the motivation for the open problem; no theorem is affected.

**Proposed repair and completion criterion:** Add a sentence stating that the early rise is mainly intercept regret and the later rise mainly alignment regret, and frame the role of the intercept as a hypothesis linked to Propositions 5.2–5.3 (or as intercept drift degrading alignment, if supported). Complete when the text matches the layer thicknesses of Figure 2.

**Dependencies:** F03, F35.

**Verification:** X02-02 (cross; v1, v2 confirmed-with-changes, both lowering Medium to Low, `X02-02.v1.md`, `X02-02.v2.md`); X09-05 (code data; confirmed, `X09.low.md`); X10-04 (interpretation part).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f37"></a>

### F37. General empirical statements in Section 5.3 rest on one displayed realization per class balance

**Importance:** Low · **Type:** overclaim (evidence) · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 205–216 (Section 5.3, p. 17); Figure 2 (`fig:class-imbalance-regret`, p. 17).

**Finding and evidence (established):** "Performance depends strongly on the hyperparameters and the data distribution"; "In balanced settings … classification error decreases consistently"; "we repeatedly observe … a U-shaped error curve". Figure 2 shows one finite-dimensional realization (seed 49) at one setting for each $p$; no hyperparameter variation is displayed, and the repository contains no configuration for other settings. "Repeatedly" is partly supported by Figure 1 (20 runs, another imbalanced setting), which the text does not cite for it. The independent simulation supports the patterns: monotone decrease under balance in 30/30 seeds, and the U-shape under imbalance in 40/40 seeds over two configurations. (The imbalanced curve dips and then plateaus near $0.2$, so "U-shaped" is loose wording.)

**Consequence:** Local; the statements are true in the simulated settings but not supported by the displayed evidence.

**Proposed repair and completion criterion:** Restrict the wording to the displayed configurations and cite Figure 1 for the repeated U-shape, or add a small grid of seeds and parameters (the gap-task simulation shows the patterns are robust at the two displayed configurations). Complete when each general sentence points to displayed evidence or is scoped to it.

**Dependencies:** F03, F35.

**Verification:** X02-05 (cross; confirmed-with-changes, `X02.low.md`); X09-03 (code: balanced claim rests on one seed); X10-04 (generality part); G1-01 (simulation, `runs/r1/reports/G1-01.cross.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f38"></a>

### F38. The abstract, the contributions, and the scope paragraph do not reflect Section 5

**Importance:** Low · **Type:** inconsistency (front matter) · **State:** Open · **resolved?** no

**Location (d430d75):** main 90–109 (abstract, p. 1); introduction 98–138, especially 130–138 (Section 1.1, p. 3); compare numerical 1–471 (Section 5, pp. 15–19).

**Finding and evidence (established):** The abstract announces "three results" and the contribution list is "threefold". Section 5 (Propositions 5.1–5.3 with Appendix D, the numerical validation in Figure 1, the alignment/intercept regret decomposition, and the class-imbalance behavior of Figure 2) is mentioned nowhere in the abstract or introduction. Lines 132–138 call questions such as "when self-training improves generalization relative to its initial classifier, how class imbalance affects its dynamics, …" "beyond the scope of this paper", while Section 5.3 ("Intercept dynamics and class imbalance") takes the first two up; the introduction understates Section 5 rather than contradicting it. Corollary 4.8 (limiting error) is also absent from the contributions.

**Consequence:** Front matter only; no result is affected.

**Proposed repair and completion criterion:** Add a fourth contribution item on statistical interpretation (limiting error and Bayes benchmark, regret decomposition, numerical validation, intercept feedback under imbalance, and the symmetric zero-intercept case), citing Section~\ref{sec:numerical}; add one abstract sentence on Section 5; rewrite lines 130–138 to say that Section~\ref{sec:numerical} takes first steps while a quantitative theory remains open. Complete when every Section 4–5 result is named or deliberately omitted and the scope paragraph no longer calls out of scope what Section 5 studies.

**Dependencies:** F39 (roadmap).

**Verification:** X03-01 (cross; confirmed, `X03.low.md`); X10-07 points 1–2 (cross; confirmed-with-changes, `X10.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f39"></a>

### F39. The roadmap omits Sections 3 and 5 and Appendices D–E, and calls appendices "Sections"

**Importance:** Low · **Type:** inconsistency (front matter) · **State:** Open · **resolved?** no

**Location (d430d75):** introduction 140–145 (closing paragraph of Section 1.1, p. 3); also finite-dim 294, long-time-behavior 197, setting 9, mean-field 568, proof-mean-field 518 ("Section A", "Section C", "Section E.1" versus "Appendix B", "Appendix E.6").

**Finding and evidence (established):** Rendered: "Section 2 reviews related work on self-training, self-distillation, and dynamical mean-field theory. Section 4 presents our main results, whose proofs appear in Sections A, B, and C, respectively." (i) Section 3, Section 5 (`sec:numerical`), Appendix D (`sec:proof-numerical`), and Appendix E (`sec:math-prelim`) are not mentioned; the last two labels are never referenced and `sec:numerical` only in the Appendix D heading. (ii) The \ref targets are appendices but are called "Sections", and elsewhere the same appendices are called "Appendix". (iii) "Respectively" has one antecedent for three items; the intended antecedents are Sections 4.1–4.3. (iv) Section 2 also covers adaptive training procedures (Section 2.3) and high-dimensional dynamics (Section 2.4).

**Consequence:** Local (navigation).

**Proposed repair and completion criterion:** Rewrite the roadmap to name Section~\ref{sec:setting}; map Sections~\ref{subsec:finite-dim}, \ref{subsec:mean-field}, \ref{subsec:long-time} to Appendices~\ref{sec:proof-finite-dim}, \ref{sec:proof-mean-field}, \ref{sec:proof-long-time}, respectively; add Section~\ref{sec:numerical}, Appendix~\ref{sec:proof-numerical}, and Appendix~\ref{sec:math-prelim}; list all four Section 2 topics; use "Appendix~\ref" for every target after \appendix. Complete when the rendered roadmap names every section and appendix with the right word and the PDF never prints "Section A"–"Section E".

**Dependencies:** F38.

**Verification:** X03-02 (cross; confirmed, `X03.low.md`); X07-03 (single-check); X10-07 point 3.

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f40"></a>

### F40. The abstract's "joint parameter and score trajectory laws" conflicts with the two-space construction

**Importance:** Low · **Type:** inconsistency (wording) · **State:** Open · **resolved?** no

**Location (d430d75):** main 103–105 (abstract, p. 1); related_work 54, 130–131 (pp. 4–5); introduction 117 (contribution 2, p. 3); compare mean-field 116–145 (p. 10) and 429–474 (Theorem 4.7, p. 12).

**Finding and evidence (established):** "We provide a precise characterization of the joint parameter and score trajectory laws over every fixed time horizon through effective stochastic processes." Theorem 4.7 characterizes two separate empirical laws, each joint over time: one over the $d$ coordinates of $(\mu_k,w_k^0,\dots,w_k^T)$ and one over the $n$ samples of $(Y_i,\Delta_i,r_i^0,\dots,r_i^T)$. They live on two probability spaces, and mean-field 141–143 states that "no joint law between their random variables is prescribed". The phrase reads as a single joint law of parameters and scores. Contribution 2 is disambiguated only by "two effective stochastic processes".

**Consequence:** Wording only; Theorem 4.7 is unaffected.

**Proposed repair and completion criterion:** For example: "we characterize, over every fixed time horizon, the limiting empirical laws of the parameter-coordinate trajectories and of the training-score trajectories through two coupled effective stochastic processes" (optionally adding the intercept limit); apply consistent wording at related_work 54 and 130–131 and optionally in contribution 2. Complete when no wording suggests a joint law across the two sides.

**Dependencies:** none.

**Verification:** X03-03 (cross; confirmed-with-changes, `X03.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f41"></a>

### F41. Contribution 3 says "unlabeled scores", but Theorem 4.10 gives convergence of all effective scores

**Importance:** Low · **Type:** inconsistency (wording) · **State:** Open · **resolved?** no

**Location (d430d75):** introduction 122–124 (contribution 3, p. 3); compare long-time-behavior 153–164 (Theorem 4.10, `eq:effective-score-convergence`, p. 14) and proof-long-time 1160–1172 (p. 55).

**Finding and evidence (established):** "We establish convergence of the effective parameters and unlabeled scores processes as the number of iterations tends to infinity." The display `eq:effective-score-convergence` gives $\|\tilde r^t-\tilde r^\infty\|_{L^2(\tilde{\mathbb P})}\to0$ on the whole sample-side space, including $\tilde\Delta=1$; only the stabilization of $\tilde{\mathfrak c}^t$ is restricted to unlabeled observations. The sentence understates the result and is ungrammatical ("parameters and unlabeled scores processes").

**Consequence:** Local only.

**Proposed repair and completion criterion:** "We establish convergence of the effective parameter and score processes as the number of iterations tends to infinity." Complete when the wording matches `eq:effective-score-convergence`.

**Dependencies:** Related: F70 (the unlabeled-only limit (116) is unused).

**Verification:** X03-04 (cross; confirmed, `X03.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f42"></a>

### F42. The introduction does not state the order of limits or the data conditions of the results

**Importance:** Low · **Type:** improvement (front matter precision) · **State:** Open · **resolved?** no

**Location (d430d75):** main 99–108 (abstract, p. 1); introduction 8, 89–96, 100–127 (pp. 2–3); compare main 120 (Section 4 opening) and long-time-behavior 29–56 (Proposition 4.9, p. 13).

**Finding and evidence (established):** (a) The long-time results concern the effective process ($d\to\infty$ first). The introduction does not state this order of limits, nor Proposition 4.9 (identification times diverge in probability), which indicates that the limits need not commute; a reader may take $\tilde\theta^\infty$ to describe the algorithm's limit point in high dimensions. Main 120 states the order correctly. (b) The results also need data conditions: both labeled classes (Theorem 4.4), $\bar p_{\mathcal L}\in(0,1)$ (Theorem 4.10), Assumptions 3.1 and 4.3; the abstract says only "Under suitable assumptions on the loss, penalty, and algorithm". (c) Theorem 4.4 holds for any fixed dataset. (d) The existing bibliography entry `amini2025survey` could accompany Lee (2013) in the definition of self-training (no new reference).

**Consequence:** Front matter only.

**Proposed repair and completion criterion:** Optional: add to contribution 3 a sentence that the long-time results concern the high-dimensional limit taken first, citing Proposition~\ref{prop:identification-time-divergence}; write "Under suitable assumptions" (or add "data") in the abstract; optionally "for any fixed dataset" for Theorem 4.4. Complete when the introduction states the order of limits.

**Dependencies:** F27, F74.

**Verification:** X03-05 (cross; confirmed, `X03.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f43"></a>

### F43. "The training objective changes at each iteration" versus Proposition 4.1

**Importance:** Low · **Type:** overclaim (framing) · **State:** Open · **resolved?** no

**Location (d430d75):** introduction 76–80 (Section 1, p. 3); compare finite-dim 63–116 (Proposition 4.1, `prop:ST-potential`, p. 8); same framing at related_work 106–107.

**Finding and evidence (established):** "Unlike ordinary empirical risk minimization, the training objective changes at each iteration, as the pseudo-labels and selected observations depend on the current classifier." With the teacher refreshed at every step, the update map $G(\theta)=\nabla_1L_{\rm ST}(\theta;\theta)$ is time-invariant, and Proposition 4.1 gives $G=\nabla V$ off the finite union of hyperplanes $\mathcal S_\kappa$, with $V$ a fixed function of the data. Explicitly, since $\kappa_-<0<\kappa_+$, $S_\kappa(r)\ell'(\operatorname{sign}r,r)=\psi_\kappa(r)$ for every $r$, so $G(\theta)=\frac1N\sum_{I_{\mathcal L}}\ell'(Y_i,r_i)\breve X_i+\frac{\pi}{M}\sum_{I_{\mathcal U}}\psi_\kappa(r_j)\breve X_j+\frac{\lambda}{d}(0,\nabla J(w))$. The algorithm is therefore preconditioned gradient descent on one fixed empirical risk that is nonconvex with a discontinuous gradient; only the surrogate $L_{\rm ST}(\cdot;\theta^t)$ changes with $t$.

**Consequence:** Framing in the introduction only; no result is affected.

**Proposed repair and completion criterion:** Qualify: "the surrogate objective changes at each iteration; equivalently (Proposition~\ref{prop:ST-potential}), the iterates follow gradient descent on a fixed potential that is nonconvex and has a discontinuous gradient." Complete when the introduction and Section 4.1 describe the same structure.

**Dependencies:** F44 (positioning that uses this viewpoint).

**Verification:** G1-03-03 (gap task; confirmed, `G1-03.low.md`); X10-01 (introduction part; v1 locates the overclaim here, `X10-01.v1.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f44"></a>

### F44. The positioning of Theorem 4.7 against rigorous GD/DMFT results states the obstruction imprecisely

**Importance:** Low · **Type:** improvement (positioning) · **State:** Open · **resolved?** no

**Location (d430d75):** related_work 180–187, 202–210 (Section 2.4, `subsec:high-dim-dynamics`, p. 5); mean-field 566–587 (paragraph after Corollary 4.8, p. 13).

**Finding and evidence (established):** The paper says "Although some results accommodate discontinuous nonlinearities, applying them here requires encoding our recursion, verifying the assumptions, and identifying the resulting effective processes" and "their direct application to our recursion requires additional arguments to accommodate the discontinuities". This is true but generic, and does not use the fact that Algorithm 3.2 is preconditioned GD on a fixed potential (F43). The gap task read the cited sources and found: (a) Gerbelot et al. (Theorem 3.2, Corollary 3.3) and Celentano–Cheng–Montanari (Theorem 2) cover discrete GD with data reuse but need (pseudo-)Lipschitz update maps and a centered design without global scalars (no mean shift, no intercept), even for smooth losses; (b) Yang's NETSOR-T master theorem (Tensor Programs III, Theorem 2.10, Remark 2.12) allows discontinuous maps and defines memory coefficients by the same projection formula, but has no scalar variables; the versions with scalars (E.5, E.11, F.9) need pseudo-Lipschitz or parameter-controlled maps (Definition E.8), which the intercept- and alignment-shifted indicator fails under the direct encoding; (c) Ranasinghe et al. cover jumps only for scalar AMP with fixed thresholds (their Remark 2 excludes data-dependent thresholds), whereas here the effective thresholds move with $b^t$; (d) Han–Xu (arXiv:2412.09498, uncited) allow iteration-dependent row-separable nonconvex losses but require a Lipschitz or $C^3$ loss derivative ((A5)/(A5′)), so they do not cover $\psi_\kappa$. What no existing theorem handles is data-driven scalars ($b^t$, $m^t$) that shift the thresholds of a discontinuous update map. The novelty claim at related_work 53–55 ("for this combination of features") is not false. The gap task judged a smoothing-plus-anticoncentration route feasible but about as costly as the paper's direct proof.

**Consequence:** Positioning only; the novelty of Theorem 4.7 is real but under-described, and the tensor-program sentence can be misread as saying the theorem follows after bookkeeping.

**Proposed repair and completion criterion:** Replace related_work 184–187 and 202–206 by two or three sentences naming (a)–(c) with the existing citations (and the mean-shift design and intercept next to the discontinuities); optionally state the GD-on-$V$ viewpoint. Citing Han–Xu or Han (arXiv:2406.19061) needs a new bibliography entry and is the authors' decision. Complete when a reader can see which hypothesis of each cited framework fails here, checked against the cited statements.

**Dependencies:** F43, F45, F47, F48.

**Verification:** X10-01 (cross; v1 confirmed-with-changes, Medium at the boundary with Low; v2 confirmed-with-changes, Low, `X10-01.v1.md`, `X10-01.v2.md`); G1-03-02 (gap task; confirmed-with-changes, `G1-03.low.md`; the gap task also calibrated this positioning issue as Low); X12-05 (cross; confirmed, `X12.low.md`). The register uses Low following two of the three assessments.

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f45"></a>

### F45. The closest prior DMFT analysis of this model (Mignacco et al. 2021) is in references.bib but not cited

**Importance:** Low · **Type:** gap (literature) · **State:** Open · **resolved?** no

**Location (d430d75):** related_work 136–166, 202–211 (Section 2.4, pp. 4–5); references.bib 123–134 (key `Mignacco_2021`).

**Finding and evidence (established):** Mignacco, Krzakala, Urbani, Zdeborová (J. Stat. Mech. 2021, 124008) derive, non-rigorously, the DMFT of stochastic and full-batch gradient flow for a linear classifier on the two-cluster Gaussian mixture with logistic loss and ridge penalty. The gap task showed analytically that Definition 4.6 with $\pi=0$, no intercept, ridge penalty, balanced classes, and isotropic initialization independent of the data reduces to the step-$\eta$ discretization of their Eqs. (15)–(19) ($\eta_M=\eta/\bar\delta$, $\lambda_M=\bar\delta\lambda$, $\Delta_M=\sigma^2$), up to how the weight $\Delta/\bar\rho$ is represented; it also showed that at $\pi=0$, $\mu=0$, no intercept, Definition 4.6 coincides term by term with Gerbelot et al. Corollary 3.3 and the discrete system (112) of Celentano–Cheng–Montanari. Their dynamics are continuous-time and without intercept, so this is an analogue of the $\pi=0$ logistic/ridge case, not an exact counterpart of Algorithm 3.2. The bib entry title also has a stray asterisk.

**Consequence:** Positioning only. It also gives an independent analytic consistency check of Definition 4.6 that the paper could mention.

**Proposed repair and completion criterion:** Authors' decision: one sentence after related_work 166 citing `Mignacco_2021` as a non-rigorous DMFT analysis of gradient-based Gaussian-mixture classification, optionally noting the $\pi=0$ reduction of Definition~\ref{def:mean-field-recursion}; remove the stray asterisk in the bib title. Complete when the citation appears in the compiled bibliography and the sentence matches the special case above.

**Dependencies:** F44.

**Verification:** X12-01 (cross; confirmed-with-changes, `X12.low.md`); G1-03-01 (gap task, analytic reduction; confirmed-with-changes, `G1-03.low.md`); X10-01 (Mignacco part).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f46"></a>

### F46. The main text credits the Gaussian conditioning argument only to Bolthausen, and the Bayati–Montanari lemma is not pointed to

**Importance:** Low · **Type:** improvement (attribution) · **State:** Open · **resolved?** no

**Location (d430d75):** mean-field 566–571 (paragraph after Corollary 4.8, p. 13); proof-mean-field 1582–1584 (opening of the Gaussian conditioning subsection, p. 36); Proposition B.8 (`proposition:mf-proof-conditional-matrix`, 1772–1793, p. 37).

**Finding and evidence (established):** "The proof of Theorem 4.7 uses an iterative Gaussian conditioning argument following the approach of Bolthausen [bolthausen2014]." Bolthausen (2014) conditions a symmetric SK matrix; the rectangular conditioning on $(UW,U^\top G)$ in Proposition B.8, with conditional mean $U\Pi_W+\Pi_GU-\Pi_GU\Pi_W$ and fluctuation $\Pi_G^\perp\check U\Pi_W^\perp$, is Bayati–Montanari's version (IEEE TIT 57(2), §III-H: Lemma 10, conditional law, and Lemma 11, linear-conditioning formula, which assumes full row rank; Lemmas 11–12 in arXiv v4; verified in the journal text). Appendix B cites both papers, without a pointer; the main text cites only Bolthausen. The paper's Lemma B.7 drops the rank condition. Related work 165–166 already credits Gerbelot et al. with iterative conditioning applied directly to GD.

**Consequence:** Local (attribution precision); no new reference is needed.

**Proposed repair and completion criterion:** Cite `bayati2011dynamics` alongside `bolthausen2014` at mean-field 568; optionally add "[Section III-H, Lemmas 10–11]" at proof-mean-field 1584 and note that Lemma~\ref{lemma:mf-proof-linear-conditioning} extends it to rank-deficient histories. Complete when the overview and Appendix B credit the same sources with a checked lemma number.

**Dependencies:** F10.

**Verification:** X05-05 (cross; confirmed, `X05.low.md`); X12-02 (cross; confirmed-with-changes, `X12.low.md`); G1-02-03 (gap task, journal text read; confirmed, `G1-02.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f47"></a>

### F47. The discontinuities are attributed to hard pseudo-labeling, but the only jumps are at the selection thresholds

**Importance:** Low · **Type:** inconsistency (description) · **State:** Open · **resolved?** no

**Location (d430d75):** related_work 202–206 (Section 2.4 closing paragraph, p. 5); also related_work 97–98 (p. 4).

**Finding and evidence (established):** "The discontinuities arising from hard pseudo-labeling and confidence selection". In Algorithm 3.2 the unlabeled map is $S_\kappa(r)\ell'(\operatorname{sign}r,r)$ with $\kappa_-<0<\kappa_+$ (setting 143, 218); it vanishes on $(\kappa_-,\kappa_+)$, which contains $0$, so the sign discontinuity at $0$ never affects the update. The only jumps are at $\kappa_-$ and $\kappa_+$, of sizes $-\ell'(-1,\kappa_-)$ and $\ell'(1,\kappa_+)$: pseudo-labeling sets the jump sizes; selection creates the jump points.

**Consequence:** Local (precision of the positioning).

**Proposed repair and completion criterion:** Reword to "discontinuities created by confidence selection of hard pseudo-labels (jumps at the thresholds $\kappa_\pm$)". Complete when the wording matches Algorithm 3.2.

**Dependencies:** F44.

**Verification:** X12-03 (cross; confirmed, `X12.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f48"></a>

### F48. The positioning undersells that projection-defined memory coefficients carry the jump terms that derivative-based response kernels miss

**Importance:** Low · **Type:** improvement (positioning) · **State:** Open · **resolved?** no

**Location (d430d75):** related_work 202–210 (p. 5); mean-field 569–571 (p. 13); Definition 4.6 (`def:mean-field-recursion`, `eq:phi-w-definition`, `eq:phi-g-definition`, p. 11).

**Finding and evidence (established):** Gerbelot et al. (3.29)–(3.30) and Celentano et al. define response kernels through derivatives. For maps with jumps, the almost-everywhere derivative misses the Stein boundary term $\sum_j\Delta_jf(\beta_j)$ (Ranasinghe et al., Lemma 2 and Corollary 1). Definition 4.6 defines its coefficients through Gaussian covariances (orthogonal projections), which include this term automatically. A computation for the paper's unlabeled map (logistic loss, $\kappa=\pm1$, $(b,s)=(0,1)$) gives regression coefficient $-0.0828$ against an a.e.-derivative average of $+0.0473$, with boundary term $-0.1302$. The gap task (G1-03) proved that the projection-defined coefficients equal the DMFT response functions defined by differentiating in a shift of the Gaussian input. The paper does not state this advantage.

**Consequence:** None for correctness; the contribution is stated less sharply than it could be.

**Proposed repair and completion criterion:** Optional: one sentence at related_work 207–209 or mean-field 569–571 explaining that projection-defined coefficients remain valid at the selection thresholds, where derivative-based ones would omit the jump contributions. Complete when the sentence is consistent with Definition 4.6.

**Dependencies:** F44.

**Verification:** X12-04 (cross; confirmed, `X12.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f49"></a>

### F49. Section 5.3 credits only Takahashi for intercept drift and intercept fixing; the already-cited Takanami et al. report both with repeated data

**Importance:** Low · **Type:** gap (attribution) · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 233–238 (Section 5.3, `subsec:intercept-dynamics`, p. 17).

**Finding and evidence (established):** "The importance of the intercept relative to the weight norm is also emphasized by Takahashi … They propose fixing the intercept as a heuristic to improve classification performance." The description of Takahashi is accurate (§1 and "bias-fixing (Heuristic 2)", checked in arXiv v5). Takanami et al. (`takanami2025effect`, already cited) report the same drift and heuristic in a setting closer to this paper, where the same data are reused across stages: §7, "the rescaled bias worsens as training progresses, deviating from its Bayes-optimal value … fixing the bias at an early stage is a simple and effective heuristic"; their abstract mentions "bias parameter fixing, which helps under label imbalance". This mirrors numerical 222–223.

**Consequence:** Local (attribution and positioning of the Section 5.3 observations).

**Proposed repair and completion criterion:** Add \cite{takanami2025effect} to the paragraph, noting that they observe intercept drift and propose intercept fixing in repeated-data self-distillation (no new bibliography entry). Complete when the sentence credits both works.

**Dependencies:** F03 (the paper's own intercept-fixing claim).

**Verification:** X06-01 (cross; confirmed, `X06.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f50"></a>

### F50. The Oymak–Gulcu description omits that their iterative characterization is a rigorous proportional-asymptotic result

**Importance:** Low · **Type:** presentation (literature description) · **State:** Open · **resolved?** no

**Location (d430d75):** related_work 20–21, 36–43 (Section 2.1, `subsec:st`, pp. 3–4).

**Finding and evidence (established):** "Oymak and Gulcu analyze confidence-thresholded averaging estimators, using fresh batches for iterative characterization", followed by "Closer to our proportional-asymptotic setting, Takahashi … Both works rely on non-rigorous replica calculations." Oymak–Gulcu Theorem 3.3 is a rigorous limit as $p\to\infty$ with $n/p$ and $u/p$ fixed ($\cot(\hat\beta,\mu)$ converges in probability to $F_u^\tau(\sqrt{n/p}/\sigma)$ for $\tau$ fresh-batch iterations). The current ordering implies that the only proportional-regime self-training analyses are non-rigorous.

**Consequence:** Local. The novelty claim is unaffected (fresh batches and a one-shot estimator); describing Oymak–Gulcu correctly sharpens the contribution (data reuse and gradient dynamics).

**Proposed repair and completion criterion:** Reword, e.g. "Oymak and Gulcu derive proportional-asymptotic characterizations of confidence-thresholded averaging estimators, using fresh batches at each iteration." Complete when the wording matches their Theorem 3.3.

**Dependencies:** F57 (the bibliography entry should cite the published, retitled version).

**Verification:** X06-02 (cross; confirmed, `X06.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f51"></a>

### F51. "Hard pseudo-labels" understates Takanami et al., who analyze soft labels with hard labels as a limit

**Importance:** Low · **Type:** inconsistency (source description) · **State:** Open · **resolved?** no

**Location (d430d75):** related_work 40–42 (Section 2.1, p. 4).

**Finding and evidence (established):** "Takanami et al. analyze repeated-data self-distillation with hard pseudo-labels and stagewise minimization, but without confidence selection." Takanami §3.2 defines pseudo-labels $\sigma(\beta^t(\cdot))$ with an inverse temperature: "In the limit $\beta^t\to\infty$, it becomes hard (0 or 1), whereas finite $\beta^t$ yields soft labels"; §5 compares soft and hard labels. "Repeated data", "stagewise", and "no selection" are accurate.

**Consequence:** Local only.

**Proposed repair and completion criterion:** "… with soft (temperature-controlled) and hard pseudo-labels and stagewise minimization, but without confidence selection." Complete when the wording matches their §3.2.

**Dependencies:** none.

**Verification:** X06-04 (cross; confirmed-with-changes, `X06.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f52"></a>

### F52. The closest rigorous proportional-regime analysis of iterated retraining with reused data (Javanmard et al. 2025) is not discussed

**Importance:** Low · **Type:** gap (literature) · **State:** Open · **resolved?** no

**Location (d430d75):** related_work 36–55 (Section 2.1, novelty claim at 53–55, pp. 3–4).

**Finding and evidence (established):** Javanmard, Das, Epasto, Mirrokni, "Self-Boost via Optimal Retraining: An Analysis via Approximate Message Passing" (arXiv:2505.15195) rigorously analyze multi-round retraining of a linear classifier on its own predicted labels in a Gaussian mixture and a GLM, using AMP state evolution (Theorems 3.1, 4.2) in the proportional regime with the data matrix fixed across iterations. Their setting differs (supervised with noisy labels, no unlabeled data; an AMP iteration rather than GD; Lipschitz aggregators; no confidence selection), so the qualified novelty claim stands, but the positioning omits the closest rigorous work. The search was not exhaustive.

**Consequence:** Local (positioning); the headline novelty is unaffected.

**Proposed repair and completion criterion:** Authors' decision, since a new bibliography entry needs authorization. Possible sentence: "Javanmard et al. analyze iterative retraining on predicted labels with reused data via AMP state evolution, in a supervised noisy-label setting without confidence selection." Complete when the characterization is checked against arXiv:2505.15195 §§2–3.

**Dependencies:** none.

**Verification:** X06-03 (cross; confirmed, `X06.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f53"></a>

### F53. The normalized alignment $\bar\alpha^t$ reuses the symbol of the projection coefficients

**Importance:** Low · **Type:** inconsistency (notation) · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 57–75, 145–153, 452–461 (Section 5.2, pp. 16, 19); proof-numerical (Appendix D); compare mean-field 194–298 (Definition 4.6, p. 11), proof-mean-field 20–22, 627–651, 737–738, 864–865 (pp. 26, 30).

**Finding and evidence (established):** $\bar\alpha^t:=\bar m^t/(\sigma\bar\tau^t)$ and its finite analogue $\alpha^t$ use the same letter, bar, and time index as the coefficient vectors $\bar\alpha^{[a]}_t=(\bar\alpha^{[a]}(t,s))_s$ and their finite versions $\alpha^{[w]}_t$, $\alpha^{[g]}_t$; the two differ only in sub/superscript placement and the $[a]$ tag, and both appear in Appendix D. Further $\alpha$'s appear as $\alpha_j$ (proof-finite-dim 330) and $\alpha_R$ (proof-long-time 707).

**Consequence:** Local; risk of misreading.

**Proposed repair and completion criterion:** Rename the Section 5 pair (about 11 occurrences in numerical.tex and proof-numerical.tex), e.g. $\bar a^t$, $a^t$ (and $\bar\beta^t$ correspondingly if desired). Complete when no untagged $\bar\alpha^t$ remains.

**Dependencies:** none.

**Verification:** X04-02 (cross; confirmed, `X04.low.md`); also N1-06 (1), X02-08 (4), X08-14 (single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f54"></a>

### F54. $\kappa$ denotes the threshold pair in Sections 3–4 and a positive scalar in Section 5

**Importance:** Low · **Type:** inconsistency (notation) · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 15–16 (Section 5.1, p. 15) and 426 (Proposition 5.3, `prop:zero-intercept-symmetry`, p. 18); compare setting 143 ($\kappa:=(\kappa_-,\kappa_+)$, p. 6).

**Finding and evidence (established):** Section 5 writes "$\kappa_-=-\kappa$ and $\kappa_+=\kappa$, where $\kappa>0$", redefining $\kappa$ as a scalar, while $S_\kappa$, $\psi_\kappa$, $C_\kappa$, $j_\kappa$, $\mathcal A_\kappa$ all use the pair. The captions already write $\kappa_\pm=\pm\log4$, so the scalar is unnecessary.

**Consequence:** Local only.

**Proposed repair and completion criterion:** Write "symmetric thresholds $\kappa_-=-\kappa_+$" at numerical 15–16 and "If $\kappa_-=-\kappa_+$ and $\bar b^0=0$" in Proposition 5.3. Complete when $\kappa$ never denotes a scalar.

**Dependencies:** none.

**Verification:** X04-03 (cross; confirmed, `X04.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f55"></a>

### F55. $z$ and $\xi$ denote both effective scalars and finite-dimensional Gaussian vectors, contrary to the stated tilde convention

**Importance:** Low · **Type:** inconsistency (notation) · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 671–676 (convention), 753–762, 880–889 (Proposition B.4, pp. 30–31), 2309–2318 vs 2383 (p. 41), 2683–2692 vs 2759 (p. 44), 1641 (p. 36); compare mean-field 129–138, 274–300 (Definition 4.6, pp. 10–11).

**Finding and evidence (established):** proof-mean-field 671–676 says effective random quantities are distinguished by tildes. The effective innovations $z_t^{[g]}$, $z_t^{[w]}$ and the processes $\xi_t^{[g]}$, $\xi_t^{[w]}$ carry no tilde, and Proposition B.4 uses $z_t^{[g]}\sim N(0,I_n)$ and $z_t^{[w]}\sim N(0,I_d)$ for the finite-dimensional vectors; both meanings appear within 70 lines (2313 vs 2383), the scalar one playing the role of $Z$ in Lemma B.6. $\xi$ is also reused as $\pi_KZ$ at line 1641.

**Consequence:** Local; obscures the Lemma B.6 limit.

**Proposed repair and completion criterion:** Write $\tilde z_t^{[g]}$, $\tilde z_t^{[w]}$, $\tilde\xi_t^{[g]}$, $\tilde\xi_t^{[w]}$ for the effective objects, or rename the finite vectors (e.g. a check accent, matching $\check U$), or state the exception at 671–676. Complete when each symbol has one meaning in Appendix B.

**Dependencies:** none.

**Verification:** X04-05 (cross; confirmed, `X04.low.md`); also M2-05 (1), M5-04 (1), M6-02 (1), M1-05 (6) (single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f56"></a>

### F56. External result pointers: the Kallenberg (3rd ed.) numbers are verified correct; the Ethier–Kurtz pointer remains unverified

**Importance:** Low · **Type:** unverified-source · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 1040, 1060, 1158, 1189, 1418, 1667, 1739, 1752, 1892, 2305, 2680, 3100 (Kallenberg 2021, pp. 32–46); 1413–1415 (Worm–Hille Proposition 2.2 and Ethier–Kurtz Ch. 3 Proposition 4.4, proof of Lemma B.6, p. 34).

**Finding and evidence (established):** Four auditors (M4, M5, M7, X05) could not obtain Kallenberg's third edition and reported its twelve result numbers as unconfirmed; X05 also queried whether Lemma 5.4 (used at 1418 and 3100) and Theorem 8.5 (used at 1752 and 1892) were each cited for two different facts. The gap task then read Chapters 5, 8, and 14 of the third edition: every Kallenberg number is correct and states what the paper uses it for, with hypotheses satisfied at each point of use. Lemma 5.4 states one fact (convergence in probability in a countable product iff coordinatewise), used correctly at both places; Theorem 8.5 ("conditional distributions, disintegration") gives existence, a.e. uniqueness, and the disintegration formula, supporting both 1752 and 1892. The Worm–Hille pointer is verified and states the exact fact used; its proof says it "follows from the proof of [Ethier–Kurtz, Proposition 3.4.4]", matching the paper's wording. The Ethier–Kurtz text itself could not be obtained (publisher returned 403, no preview, no local copy); the chapter outline confirms Ch. 3 §4 is "Separating and Convergence Determining Sets". Only that secondary pointer remains unverified; on $\mathbb R^{k+1}$ the fact is elementary.

**Consequence:** None; Worm–Hille alone supports the step. The Kallenberg part needs no change (verification-only disposition).

**Proposed repair and completion criterion:** Kallenberg: no change; this part can be closed on the gap-task evidence. Ethier–Kurtz: confirm Ch. 3 Proposition 4.4 against the book, or drop the clause "which follows from the proof of …". Complete when the pointer is checked against the book or removed.

**Dependencies:** Related: F10, F11 (which use Theorem 8.5), F17 (Villani pointers).

**Verification:** M4-04, M5-02, M7-06 (unit), X05-01 (cross) (each confirmed at the time that the numbers could not be checked; `M4.low.md`, `M5.low.md`, `M7.low.md`, `X05.low.md`); G1-02-02 (gap task, primary sources; confirmed, `G1-02.low.md`; Kallenberg and Villani verification in `runs/r1/reports/G1-02.cross.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f57"></a>

### F57. Cited preprints with published versions

**Importance:** Low · **Type:** inconsistency (bibliography metadata) · **State:** Open · **resolved?** no

**Location (d430d75):** references 1–10, 63–72, 846–855, 869–878, 879–888, 1015–1024 and the entries `oymak2020`, `dang2026`, `yang2022`, `arous2021online`, `arous2023highdimensional`, `paquette2022`, `wormhille2009ergodic` (printed bibliography pp. 19–21; cited at related_work 20, 141–183 and proof-mean-field 1413).

**Finding and evidence (established):** Published versions exist (checked via PMLR, JMLR, NeurIPS, Crossref): `oymak2020` is AISTATS 2021, PMLR 130:3601–3609, retitled "A Theoretical Characterization of Semi-supervised Learning with Self-training for Gaussian Mixture Models"; `dang2026` is ICML 2026, PMLR 306:22834–22895; `yang2022` is ICML 2021, PMLR 139:11727–11737 ("Tensor Programs IV: …"; the bib year 2022 reflects arXiv v3); `arous2021online` is JMLR 22(106):1–51; `arous2023highdimensional` is NeurIPS 35 (2022) and Comm. Pure Appl. Math. 77(3):2030–2080 (2024); `paquette2022` is Math. Program. 214(1–2):1–90; `wormhille2009ergodic` is Ergodic Theory Dynam. Systems 31(2):571–597 (2011), so the in-text pointer [Proposition 2.2] must be rechecked if the journal version is cited.

**Consequence:** Metadata only.

**Proposed repair and completion criterion:** Update the entries to their published versions, keeping the keys (authors' preference between conference and journal versions). Complete when the entries match the publisher records and in-text pointers are valid for the version cited.

**Dependencies:** F50, F58, F83 (capitalization).

**Verification:** X06-05 (cross; confirmed, `X06.low.md`); X07-11 (cross; confirmed-with-changes, `X07.low.md`); X12-06 (cross; confirmed, `X12.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f58"></a>

### F58. Bibliography metadata errors: Piccialli volume and year, Lecoiu title, Ben Arous sorting

**Importance:** Low · **Type:** error (bibliography metadata) · **State:** Open · **resolved?** no

**Location (d430d75):** references 856–868 (`piccialli2024`), 93–102 (`lecoiu2026`), 846–888 (`arous2021online`, `arous2023highdimensional`); printed bibliography [38], [27], [3], [4], pp. 19–20.

**Finding and evidence (established):** (a) `piccialli2024` gives volume 217 with "December 2024"; per Crossref, volume 217 is the May 2026 issue (online 19 December 2024), and the entry is formatted differently from the rest of the file. (b) `lecoiu2026` uses the arXiv v1 title; v2 (5 November 2026) is titled "Self-Distillation is Optimal Among Spectral Shrinkage Estimators". (c) "Gerard Ben Arous" is parsed with surname "Arous", so [3] and [4] sort under A while the text says "Ben Arous et al."; the plain style also lowercases "SGD" in the title of [4].

**Consequence:** Metadata only.

**Proposed repair and completion criterion:** (a) Year 2026, number 1–2, pages 79–121, the DOI, no month. (b) Update the title or cite v1 explicitly. (c) Use `{Ben Arous}, G{\'e}rard` and brace `{SGD}`. Complete when the rebuilt bibliography shows the corrections.

**Dependencies:** F57.

**Verification:** X07-12 (cross; confirmed, `X07.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f59"></a>

### F59. Labels: the model definition is unlabeled, item labels resolve to "B.4", one label is duplicated, and many labels are unreferenced

**Importance:** Low · **Type:** presentation (labels) · **State:** Open · **resolved?** no

**Location (d430d75):** setting 13–40 (Definition 3.1, p. 5); proof-mean-field 683 (`prop:conditional-law-U`) and 699–908 (`item:master-forward*`, `item:master-backward*`, Proposition B.4, pp. 30–31); all files (86 unreferenced non-section labels).

**Finding and evidence (established):** Definition 3.1 has no label; the model is referenced only as equation (4). The labels `item:master-forward` and `item:master-backward` sit in description items, so a reference would print "B.4". `prop:conditional-law-U` duplicates `proposition:master-recursion`. All 13 of these labels are unreferenced, so the fault is latent. More broadly, 86 non-section labels have no \ref or \eqref (list in `runs/r1/scratch/X08/unref-labels.txt`); they are harmless except where a used result goes uncited (F69) and where never-referenced numbered displays inflate the 147-equation count.

**Consequence:** None at present.

**Proposed repair and completion criterion:** Add `\label{def:gaussian-mixture-model}`; remove the duplicate and the item labels (or give items a forward/backward-specific label format); optionally use unnumbered displays for unreferenced appendix equations. Complete when every label's printed value matches its intended target and no reference is undefined after rebuild.

**Dependencies:** F66 (Proposition B.4 restatements).

**Verification:** X07-06 (cross; confirmed, `X07.low.md`); X08-16 (usage; single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f60"></a>

### F60. Streamlining: Assumption 4.4(3), $j(0)=j'(0)=0$, is used once and can be dropped

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** long-time-behavior 80 (Assumption 4.4, `assumption:long-time-loss-penalty`, item 3, p. 14); single use at proof-long-time 609–621 (proof of Lemma C.4, `lem:uniform-branch-curvature`, p. 51).

**Finding and evidence (established):** "Since $j(0)=j'(0)=0$ and $j''\ge m_j$, we have $j(u)\ge m_ju^2/2$", giving $\|w\|/\sqrt d\le W:=\sqrt{2C/(\lambda m_j)}$. This is the only use (search of all live files; the other occurrence of $j'(0)$ at proof-mean-field 353 is a general bound). The item is unnecessary: under Assumption 4.1(2) and $j''\ge m_j$, $j$ has a unique minimizer $u_0$ with $j(u)\ge\frac{m_j}2(u-u_0)^2$, so $\|w\|/\sqrt d\le|u_0|+\sqrt{2C/(\lambda m_j)}$, and the rest of Lemma C.4 uses $W$ only as an upper bound (lines 680–694). Also $j'(0)=0$ already follows from $j(0)=0$ and $j\ge0$. Item 3 is not a pure normalization: $j'(0)=0$ fixes the minimizer's location.

**Consequence:** Theorem 4.10 and Corollary 4.11 hold without item 3.

**Proposed repair and completion criterion:** Delete item 3 and replace proof-long-time 610–621 by the minimizer argument with $W:=|u_0|+\sqrt{2C/(\lambda m_j)}$; or keep it and shorten to "$j(0)=0$". Complete when $W$ enters lines 680–694 only as an upper bound and no live proof invokes $j(0)=0$ or $j'(0)=0$.

**Dependencies:** F61.

**Verification:** L1-03, L2-01 (unit), C2-03 (chain), X01-08 (cross), X08-01 (usage); all confirmed or confirmed-with-changes (`L1.low.md`, `L2.low.md`, `C2.low.md`, `X01.low.md`, `X08.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f61"></a>

### F61. Streamlining: Assumption 4.2 is implied by Assumption 4.1, and $L_\ell$, $L_j$ are introduced twice

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** mean-field 48–64 (Assumption 4.2, `assumption:regularity-of-loss-and-penalty`, p. 10); finite-dim 13–37 (Assumption 4.1, p. 7); long-time-behavior 60–82, 141–142 (Assumption 4.4, Theorem 4.10, p. 14).

**Finding and evidence (established):** Theorem 4.10 assumes the hypotheses of Theorem 4.7 (including Assumption 4.2) and Assumption 4.4 (which includes Assumption 4.1). From $C^2$ with $0<\ell''\le L_\ell$ and $0<j''\le L_j$, $\ell'$ and $j'$ are Lipschitz with these constants and $\ell'$ is strictly increasing, hence nonconstant: exactly Assumption 4.2. The two assumptions introduce $L_\ell$, $L_j$ with different stated meanings (second-derivative bounds versus first-derivative Lipschitz constants), and $\Lambda_d$ (13) and $\Lambda_{\rm bd}$ (46) must use the same ones. Assumption 4.4(2) also implies the coercivity and $j''>0$ clauses of Assumption 4.1(2), and $\kappa_-<0<\kappa_+$ is already standing from Section 3.

**Consequence:** None for correctness.

**Proposed repair and completion criterion:** After Assumption 4.4 add: "Assumption~\ref{assumption:finite-dim-loss-penalty} implies Assumption~\ref{assumption:regularity-of-loss-and-penalty} with the same constants $L_\ell$, $L_j$." Optionally state Theorem 4.10 under Assumptions 3.1, 4.3, and 4.4. Complete when $L_\ell$, $L_j$ have one meaning wherever both assumptions hold.

**Dependencies:** F18, F60.

**Verification:** X01-07 (cross; confirmed, `X01.low.md`); C2-03 and L1-03 (related parts; confirmed); X08-12 (usage; single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f62"></a>

### F62. Streamlining: the condition $\bar p\in(0,1)$ in Assumption 3.1 is used only in Section 5

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** setting 112 (Assumption 3.1, `assumption:asymptotic-regime`, p. 6); uses at proof-numerical 71 (p. 56) and numerical 96–160 (Proposition 5.1 and the regret definitions, p. 16).

**Finding and evidence (established):** "We assume $\bar p,\bar\rho\in(0,1)$." A search of every live use of $\bar p$, and all unit and chain usage ledgers, show that no proof in Appendices A–C uses $\bar p\in(0,1)$. Theorem 4.7 and Corollary 4.8 need only $p\to\bar p$ (the error formula is continuous in $\bar p$ on $[0,1]$; Lemma B.1 needs only one class with positive labeled mass); in Theorem 4.10 the condition is implied by $\bar p_{\mathcal L}\in(0,1)$ and $\bar\rho>0$. It is needed only where $\log(\bar p/(1-\bar p))$ appears (Proposition 5.1, $\beta_\star(\alpha;\bar p)$, the regret decomposition), and Proposition 5.1 states no assumption.

**Consequence:** Section 4 results carry an unneeded hypothesis; Proposition 5.1 omits the one it needs. Interacts with F01: citing Assumption 3.1 in Theorem 4.7 imports this unused condition.

**Proposed repair and completion criterion:** Optional: change setting 112 to "We assume $\bar\rho\in(0,1)$" and state "$\bar p\in(0,1)$" at the start of Section 5.2 (covering Proposition 5.1 and the regret decomposition). Complete when $\bar p\in(0,1)$ appears exactly where it is used.

**Dependencies:** F01, F28.

**Verification:** X01-06 (cross; confirmed-with-changes, `X01.low.md`); X08-03 (usage; confirmed, `X08.low.md`); C1-03 part 1 (chain; confirmed-with-changes, `C1.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f63"></a>

### F63. Streamlining: the limit $\nu_\mu\to\bar\nu_\mu$ in display (6) is implied by Assumption 4.3(1), and $\bar\nu_\mu$ is never used

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** setting 55–60, 97 (Assumption 3.1, display (6) `eq:finite-dim-limits`, p. 6); mean-field 81–88 (Assumption 4.3(1), `eq:backward-init`, p. 10).

**Finding and evidence (established):** Assumption 4.3(1) gives $W_2$ convergence of the joint law $\nu_{(\mu,w^{\rm init})}$; by Lemma E.5 the first marginal $\nu_\mu$ then converges to the first marginal of $\bar\nu_{(\mu,w^{\rm init})}$. The symbol $\bar\nu_\mu$ occurs only at setting 97; the effective process takes $\tilde\mu$ from $\bar\nu_{(\mu,w^{\rm init})}$, and the only consequence used, $\|\mu\|^2/d\to\bar s_\mu^2$ (proof-long-time 187, proof-numerical 71), comes from Assumption 4.3. Every result citing (6) except Proposition 5.1 also assumes Assumption 4.3. Uniqueness of $W_2$ limits forces $\bar\nu_\mu$ to equal that marginal, so this is a redundancy, not a missing condition.

**Consequence:** None mathematically.

**Proposed repair and completion criterion:** Optional: drop $\nu_\mu\to\bar\nu_\mu$ from (6) for results that assume Assumption 4.3, or add "where $\bar\nu_\mu$ is the first marginal of $\bar\nu_{(\mu,w^{\rm init})}$". Any streamlining must keep Proposition 5.1 supported (F28). Complete when no remaining use of $\bar\nu_\mu$ is unsupported.

**Dependencies:** F28.

**Verification:** M2-04 (unit; confirmed, `M2.low.md`); X08-02 (usage; confirmed, `X08.low.md`); C1-03 part 2 (chain; confirmed-with-changes, `C1.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f64"></a>

### F64. Streamlining: unused clauses in Propositions 4.1–4.3

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** finite-dim 68–116 (Proposition 4.1, `prop:ST-potential`), 155–172 (Proposition 4.2, `prop:configuration-branch-formulation`), 182–210 (Proposition 4.3, `prop:branch-convexity-coercivity`), p. 8; proofs proof-finite-dim 12–164 (pp. 22–23), in particular 36–43 and 82–94.

**Finding and evidence (established):** The parts used downstream are boundedness of $\Psi_\kappa$, continuity of $V$, the branch inequalities, finiteness of the configuration set, $G=\nabla L_{\mathfrak c}$ on branches, the positive definite Hessian, uniqueness of the minimizer, and coercivity of $V$ (Lemma A.2, Theorem 4.4, Appendix C; all live files searched). Unused: global Lipschitz continuity of $\Psi_\kappa$ (the two occurrences of "Lipschitz" in proof-long-time concern other functions), the identity $V=L_{\mathfrak c}+K_{\mathfrak c}$ on the branch closure ($K_{\mathfrak c}$ appears only at finite-dim 160–162 and proof-finite-dim 90–94), branch convexity, polyhedral closures (true, but the closure step needs a one-line segment argument), and $\Psi_\kappa\le0$. The descent bound (64) is proved from scalar Taylor bounds, not from $\nabla V=G$. Coercivity of $L_{\mathfrak c}$ should be kept (or the definition of $\theta^\star_{\mathfrak c}$ restricted to the identified branch).

**Consequence:** None; optional (the clauses have expository value).

**Proposed repair and completion criterion:** Optionally replace "bounded and globally Lipschitz" by "bounded and continuous" (dropping proof-finite-dim 36–43), and shorten Proposition 4.2 to the inequality description and the partition into at most $3^M$ regions (dropping proof-finite-dim 82–94). Complete when no Appendix A or C step invokes a removed clause.

**Dependencies:** F77 (Propositions 4.2–4.3 should be cited where used).

**Verification:** P1-02, P1-03 (unit; confirmed, `P1.low.md`); X08-07 (usage; confirmed-with-changes, `X08.low.md`). Also supported by X08-09 (usage; confirmed-with-changes, `X08.low.md`; Propositions 4.1–4.2 used without citation, primary entry F69).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f65"></a>

### F65. Streamlining: Remark A.3 and the closing lines of the proof of Theorem 4.4 are not used

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** proof-finite-dim 518–525 (end of proof of Theorem 4.4, `thm:st-convergence`) and 528–556 (Remark A.3, "Further consequences of descent", unlabeled), p. 25.

**Finding and evidence (established):** Remark A.3 records convergence of $V(\theta^t)$, an $O(1/T)$ bound on $\min_s\|P_d^{1/2}G(\theta^s)\|^2$, the coordinate form of the residual, validity without boundedness, and absence of periodic trajectories; the proof of Theorem 4.4 ends with $\|\theta^{t+1}-\theta^t\|_{P_d^{-1}}\le C(1+q)q^{t-t_0}$ and finite trajectory length. All assertions are correct (each re-derived from (65) and $\Delta\theta=-\eta P_dG$), but none is part of Theorem 4.4 and none is referenced or used anywhere (the remark has no label; Appendix C uses Lemma A.1 and $C_\kappa$ directly).

**Consequence:** Local only; about 35 source lines of unused material.

**Proposed repair and completion criterion:** Delete proof-finite-dim 518–525 and Remark A.3, or keep one sentence (e.g. that vanishing increments do not imply Cauchy) as a remark after Lemma A.1. Complete when no reference targets the deleted text and the proof still ends with the geometric-rate display.

**Dependencies:** F07.

**Verification:** P2-03 (unit; confirmed, `P2.low.md`); X08-06 (usage; confirmed, `X08.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f66"></a>

### F66. Streamlining: Proposition B.4 restates Lemma B.1, Lemma B.3, and Proposition B.8 inside its own statement

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 683–691 (preamble of Proposition B.4, `proposition:master-recursion`), 699–723 (item $(F_t)$(i): `eq:gaussian-decomposition`, `eq:conditional-expectation-formula`), 827–851 (item $(B_t)$(i): `eq:gaussian-decomposition-plus`, `eq:conditional-expectation-formula-plus`), pp. 30–31; duplicates at 571–590 (Lemma B.3, p. 29), 1772–1793 (Proposition B.8, `proposition:mf-proof-conditional-matrix`, p. 37); proof step 2059–2069 and 2079–2089 (p. 39).

**Finding and evidence (established):** The opening sentence ("The effective recursion is well defined at every finite time, its coordinates have finite second moments, and $\tilde r^t$ has an atomless distribution") is Lemma B.1 in weaker form. Items (i) restate word for word the measurability part of Lemma B.3 and the displays (106)–(109) of Proposition B.8, which is stated seven pages later and cited to prove them; $M_t^+$ is defined twice with ":=" (844–848, 1786–1788). The identities $M_t=\mathbb E[U\mid\mathcal F_t]$, $M_t^+=\mathbb E[U\mid\mathcal F_t^+]$ are proved (2029–2036) but never used (the half-step proofs use the explicit projector formulas), and the conditional law given $\mathcal F_T^+$ is never used. The induction carries forward only items (iv), and the forward step at time $t$ uses only $(F_{t-1})$ and $(B_{t-1})$, so ordinary induction suffices instead of "strong induction". Outside the proof, only `eq:master-backward-empirical-law`, `eq:master-forward-empirical-law`, and `eq:master-backward-macroscopic-convergence` are used; `prop:conditional-law-U` and several displays and item labels are never referenced. Item numbers are referenced by hard-coded text (2071, 2090, 2099, 2128, 2245, 2355, 2357, 2498, 2613, 2729, 2732, 2839), so renumbering is risky.

**Consequence:** None for correctness; about 45–50 source lines and four numbered displays could go.

**Proposed repair and completion criterion:** Optional, preferred minimal form: reduce each item (i) to a one-line pointer to Lemma B.3 and Proposition B.8 (keeping item numbers), replace the opening sentence by a reference to Lemma B.1, cite `eq:mf-proof-matrix-backward` and `eq:mf-proof-mean-backward` at 2625 and 2635, write "induction" for "strong induction", and optionally demote "$=\mathbb E[U\mid\mathcal F_t]$" to a remark. Complete when every reference still resolves and the proof of Theorem 4.7 and Appendix C find each cited item.

**Dependencies:** F59 (labels).

**Verification:** M2-02 (unit; confirmed-with-changes, `M2.low.md`); M4-03 (unit; confirmed, `M4.low.md`); M5-03 (unit; confirmed, `M5.low.md`); M6-01 (unit; confirmed, `M6.low.md`); C1-08 (chain; confirmed, `C1.low.md`); X08-08 (usage, Proposition B.4 part; confirmed, `X08.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f67"></a>

### F67. Streamlining: the value $0$ in the atomlessness display of Lemma B.1 is never used

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 54–58, 204–206 (Lemma B.1, `lemma:mf-proof-nondegeneracy`, statement and proof, pp. 26–27).

**Finding and evidence (established):** "$\tilde{\mathbb P}(\tilde r^t\in\{0,\kappa_-,\kappa_+\})=0$." Every later use concerns the thresholds only (proof-mean-field 2464–2467, 3003–3007; proof-long-time 65–68, 1078). $\operatorname{sign}(r)$ enters only multiplied by $S_\kappa(r)$, which vanishes near $0$ because $\kappa_-<0<\kappa_+$. The display also follows from the preceding clause (absolute continuity).

**Consequence:** Local only.

**Proposed repair and completion criterion:** Optional: replace $\{0,\kappa_-,\kappa_+\}$ by $\{\kappa_-,\kappa_+\}$ at 57 and 206 (or keep only absolute continuity); leaving it is also acceptable since it is true. Complete when no live proof invokes $\tilde{\mathbb P}(\tilde r^t=0)=0$.

**Dependencies:** none.

**Verification:** M1-04 (unit; confirmed, `M1.low.md`); X08-08 (usage, Lemma B.1 part; confirmed, `X08.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f68"></a>

### F68. Streamlining: unused conditions in the statements of Lemmas B.5–B.6

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 940–941 (Lemma B.5, `lemma:mf-proof-empirical-stability`, "a closed set $\mathcal X$", p. 31), 1238–1242, 1257 (Lemma B.6, `lemma:mf-proof-gaussian-extension`, p. 33).

**Finding and evidence (established):** Closedness of $\mathcal X$ is never used: the proof needs only that the rows and the limit law are carried by the Borel set $\mathcal X$ and continuity relative to it, since the limit law is assumed in $\mathscr P_2(\mathcal X)$ rather than obtained as a weak limit (the one nontrivial application, $\{0,1\}\times\mathbb R$, is closed anyway). In Lemma B.6 only $\mathcal G^{(m)}$-measurability of $H^{(m)}$ is used (steps 1 and 4); $c^{(m)}$, $v^{(m)}$ enter through Lemma B.5 part 2, which allows arbitrary dependence; the signs of $v^{(m)}$ and $\bar v$ play no role.

**Consequence:** None; the conditions hold in every application.

**Proposed repair and completion criterion:** Optional: replace "closed" by "Borel" and require measurability of $H^{(m)}$ only, or leave as is. Complete when the applications still satisfy the statements.

**Dependencies:** F13.

**Verification:** M3-06 (unit; confirmed, `M3.low.md`); X08-08 (usage, Lemmas B.5–B.6 part).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f69"></a>

### F69. Streamlining: Lemma E.5 and Corollary E.7 are never cited, their content is re-derived or duplicated, and Appendix E is more general than needed

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** mathematical-preliminaries 14–145, 62–66 (Definition E.2), 130–145 (Lemma E.5, `lemma:wasserstein-lipschitz-pushforward`), 178–219 (Corollary E.7, `corollary:wasserstein-empirical-observables`), pp. 58–60; re-derivations at proof-mean-field 969–990, 1076–1144 (Lemma B.5 part 1, pp. 31–32), 1465–1466 (p. 35), 2073–2076 (p. 39), 2866–2869 (p. 44); also proof-long-time 62–68, 240–264 (pp. 47–48).

**Finding and evidence (established):** Only four Appendix E labels are referenced in the paper (`subsec:wasserstein`, `subsec:empirical-measures`, `definition:empirical-measures`, and Proposition E.4 once). Lemma E.5 and Corollary E.7 are never cited. The projection property of Lemma E.5 is re-argued in words at 1465–1466, 2073–2076 (the column-discarding convention on which every subarray application in Proposition B.4 depends), and 2866–2869. Lemma B.5 part 1 duplicates Corollary E.7's moment and Gram-matrix claims (adding the random case and the pseudo-inverse), and Appendix B uses B.5 throughout; Corollary E.7's general claim is Proposition E.4(3) for empirical measures. Only $p=2$ is used; the completeness, separability, and density facts of Definition E.2 are used nowhere. Results used without citation at the points of use: Lemma E.5 (above), Corollary E.7 (proof-long-time 62–68, 240–245; and mean-field 475, see F15), Propositions 4.1–4.2 and the update identity (proof-long-time 240–264, 500–510, 867–877, 946–960; proof-finite-dim 357, 398–441).

**Consequence:** None for correctness; the appendix can be shortened or connected to the proofs.

**Proposed repair and completion criterion:** Either (a) cite Lemma E.5 at proof-mean-field 1465, 2073–2076, and 2866–2869 and Corollary E.7 at mean-field 475 and proof-long-time 62–68, 240–245 (and Propositions 4.1–4.2 where used), or (b) delete Lemma E.5 and Corollary E.7 (keeping a proved in-probability clause for F15), drop the unused sentences of Definition E.2, and specialize Appendix E to $p=2$. Complete when every remaining Appendix E statement is referenced at least once and no reference points to a removed label.

**Dependencies:** F15, F17.

**Verification:** M3-05 (unit; confirmed-with-changes, `M3.low.md`); M7-04 (unit; confirmed-with-changes, `M7.low.md`); C1-06 (chain; confirmed, `C1.low.md`); X05-04 (cross; confirmed-with-changes, `X05.low.md`); X08-11 (usage; confirmed, `X08.low.md`); X08-09 (usage; confirmed-with-changes as Presentation, `X08.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f70"></a>

### F70. Streamlining: limit (116) and several Appendix C symbols are unused, and Lemma C.5 re-derives recorded limits

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** proof-long-time 8–11 ($\tilde{\mathbb P}_{\mathcal L}$, $\tilde{\mathbb P}_{\mathcal U}$), 29–36 ($c_\kappa$), 53–64 ((116), `eq:long-time-score-distance-limit`), 74–90 ((118), $\mathcal H^{[g]}_{t+1}$), 493, 1058–1086 (Lemma C.5, `lem:effective-two-time-stability`, Step 4), pp. 46–47, 54.

**Finding and evidence (established):** Search of all live files: $\tilde{\mathbb P}_{\mathcal L}$ is never used; $c_\kappa$ is never used after its definition and duplicates (34); $\tilde{\mathbb P}_{\mathcal U}$ is already defined at long-time-behavior 175; (116) (unlabeled score distance, with $\tilde{\mathbb E}_{\mathcal U}$, which is undefined) is never referenced or used. Step 4 of Lemma C.5 re-derives (115) and uses a full-sample limit $(1/n)\|r^t-r^s\|^2\to\|\tilde r^t-\tilde r^s\|^2_{L^2(\tilde{\mathbb P})}$ that is not among the recorded limits. $r^t_{\mathcal U}$ is defined twice (61, 493); (118) repeats (72); $\mathcal H^{[g]}_{t+1}$ repeats proof-mean-field 167–172.

**Consequence:** None mathematically; one recorded limit is dead and one needed limit is derived twice.

**Proposed repair and completion criterion:** Replace (116) by the full-sample limit used in Lemma C.5 and cite (115)–(117) in Step 4; delete $\tilde{\mathbb P}_{\mathcal L}$, the duplicate $\tilde{\mathbb P}_{\mathcal U}$, and $c_\kappa$ (or use it to write $c_j^t=c_\kappa(r_j^t)$); in the proof of Proposition 4.9 cite (72) instead of re-deriving it. Complete when each recorded limit is cited at least once and no symbol defined in proof-long-time 1–69 is unused.

**Dependencies:** F23, F41.

**Verification:** L1-02, L3-04 (unit; confirmed, `L1.low.md`, `L3.low.md`); C2-04 (chain; confirmed, `C2.low.md`); X08-10 (usage; confirmed, `X08.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f71"></a>

### F71. Streamlining: quantities defined two or three times ($\bar\omega^t$, $\bar s_\mu$, $s_\mu$, $\mathcal H^{[g]}_{t+1}$, $\tilde{\mathbb P}_{\mathcal U}$, $f_c$, $c_\kappa$)

**Importance:** Low · **Type:** redundancy (notation) · **State:** Open · **resolved?** no

**Location (d430d75):** $\bar\omega^t$: mean-field 533–540 (Corollary 4.8, p. 13) and long-time-behavior 205–210 (Corollary 4.11, p. 15); $\bar s_\mu$: long-time-behavior 112–113 (`eq:s-mu-k-bar`, p. 14) and numerical 86–90 (p. 16); $s_\mu$: numerical 180 and proof-numerical 62–64; others at proof-long-time 10, 31, 75–79, 258–261, 315, proof-finite-dim 31; also setting 283–288 vs numerical 8–14 (logistic/ridge display (10)).

**Finding and evidence (established):** Each is introduced with ":=" as if new. All definitions agree (checked): the two $\bar\omega^t$ agree because $S_\kappa(\tilde r)=|\tilde{\mathfrak c}|$ (since $\kappa_-<0<\kappa_+$) and $\tilde{\mathbb P}(\tilde\Delta=0)=1-\bar\rho$, and the proof of Corollary 4.11 (1218–1225) rewrites one into the other; $\mathcal H^{[g]}_{t+1}$ matches Appendix B's $\mathcal H^{[g]}_t$ with the index shifted. The reader-facing case is mainly the ":=" redefinition of $\bar\omega^t$ in Corollary 4.11, which suggests a new quantity. ($C_\kappa$ at proof-long-time 258–261 is already introduced with "Recall".)

**Consequence:** None for correctness.

**Proposed repair and completion criterion:** Keep one definition of each and replace the others by "Recall …" with a reference (Corollary 4.11: "Recall $\bar\omega^t$ from Corollary~\ref{cor:mean-field-observables}; equivalently …"; "Recall $\bar s_\mu$ from \eqref{eq:s-mu-k-bar}"; cite (10) at numerical 8–14). Complete when each symbol has one defining ":=".

**Dependencies:** F70.

**Verification:** L3-03 (unit; confirmed, `L3.low.md`); X04-09 (cross; confirmed-with-changes, `X04.low.md`); X08-13 (usage; single-check); also X10-07 points 4–5, X02-08 (3), X13-04 (3), C2-06 (5).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f72"></a>

### F72. Streamlining: Proposition 5.2's sign hypothesis is needed only for $\tilde A^t\ge0$, and part (ii) partly restates Definition 4.6

**Importance:** Low · **Type:** redundancy · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 247–346 (Proposition 5.2, `prop:weighted-pseudo-label-contributions`, pp. 17–18), especially 250–262; proof at proof-numerical 76–212 (pp. 56–57), sign used at 85; prose at numerical 348–362.

**Finding and evidence (established):** "Suppose the hypotheses of Theorem 4.7 hold and, in addition, $-y\ell'(y,r)\ge0$ … Then the following identities hold." The proof uses the sign only once ("The sign assumption gives $\tilde A^t\ge0$"); the pointwise identity $|\tilde{\mathfrak c}^t|\ell'(\tilde{\mathfrak c}^t,\tilde r^t)=-\tilde{\mathfrak c}^t\tilde A^t$ (from $c^2=|c|$ for $c\in\{-1,0,1\}$) and identities (53)–(56) are sign free. The sign matters only for the interpretive prose at numerical 348–362 and for the "$\ge0$" asserted in the defining display of $\tilde A^t$ (258–262). In part (ii), `eq:statistical-intercept-drift` restates Definition 4.6 as a conclusion (the $\bar\zeta^t$, $\bar\chi^t$ expansions are introduced with "Writing"); only `eq:statistical-overlap-update` is derived. The hypotheses of Theorem 4.7 enter only through Lemma B.1, Lipschitz continuity of $\ell'$ and $j'$, and $\bar\rho<1$.

**Consequence:** Local; the proposition is true under a condition stronger than its identities need.

**Proposed repair and completion criterion:** Optional: state the identities under the hypotheses of Theorem 4.7 alone, define $\tilde A^t$ without "$\ge0$", and add "If, in addition, $-y\ell'(y,r)\ge0$ for all $y,r$ (e.g. under Assumption 4.1), then $\tilde A^t\ge0$"; present the intercept update as recalled from Definition 4.6. Complete when the prose at 348–362 still invokes $\tilde A^t\ge0$ where it draws sign conclusions.

**Dependencies:** none.

**Verification:** N1-04 (unit; confirmed-with-changes, `N1.low.md`); X08-05 (usage; confirmed, `X08.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f73"></a>

### F73. Streamlining: unused packages, macros, and environment in the preamble

**Importance:** Low · **Type:** redundancy (source) · **State:** Open · **resolved?** no

**Location (d430d75):** main 7, 9, 13–14, 17, 23 (comment), 27, 42–46, 50–64 (preamble; nonprinting).

**Finding and evidence (established):** Unused in live text: packages tikz (with its libraries), fancyhdr, bm, accents, cleveref, and no mathtools-specific command; macros `\R`, `\Nbb`, `\Pbb`, `\Ebb`, `\Id`, `\Var`, `\Cov`, `\sign`, `\diag`, `\tr`, `\1`; the `notation` environment. The text writes `\operatorname{sign}` six times (introduction 19, 26, 39; setting 154, 237; proof-finite-dim 334) and `\mathbf1` 29 times despite the macros. Two comments mislead: main 23 says links are black but `linkcolor=blue`; main 41–42 announce the definition style but the line is commented out (see F83).

**Consequence:** None in print.

**Proposed repair and completion criterion:** Remove the unused items or use the macros consistently, and fix the comments. Complete when the rebuild is clean and the PDF unchanged, checking that `\AtBeginEnvironment` (main 74) still resolves.

**Dependencies:** F83 (theorem style).

**Verification:** X07-05 (cross; confirmed-with-changes, `X07.low.md`); X08-15 (usage; single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f74"></a>

### F74. The eventual geometric rate of Theorem 4.4 is not uniform in $d$, which the paper never says

**Importance:** Presentation · **Type:** presentation · **State:** Open · **resolved?** no

**Location (d430d75):** finite-dim 273–280 (Theorem 4.4, p. 9); long-time-behavior 29–56 (Proposition 4.9, p. 13); introduction 108–113 (p. 3).

**Finding and evidence (established):** $t_0\ge T_{\rm id}$ in Theorem 4.4, and Proposition 4.9 gives $T_{\rm id}\to\infty$ in probability, so the geometric regime starts later as $d$ grows; the long-time simulation found $T_{\rm id}$ growing by about 12 iterations per doubling of $d$. The paper does not draw this connection.

**Consequence:** Local to how the contributions are read.

**Proposed repair and completion criterion:** One sentence after Proposition~\ref{prop:identification-time-divergence}: because $t_0\ge T_{\rm id}$ in Theorem~\ref{thm:st-convergence}, the onset of the geometric regime is not uniform in $d$. Complete when the sentence is present.

**Dependencies:** F07, F08, F42.

**Verification:** X10-03 (cross; confirmed-with-changes, recategorized to Presentation, `X10.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f75"></a>

### F75. The separate assumption counter duplicates printed numbers

**Importance:** Presentation · **Type:** presentation (format) · **State:** Open · **resolved?** no

**Location (d430d75):** main 44 (`\newtheorem{assumption}{Assumption}[section]`); affects pp. 5–14, 22.

**Finding and evidence (established):** The same printed number names two objects: Definition 3.1 and Assumption 3.1; Assumption 4.1 and Proposition 4.1; Assumptions 4.2–4.3 and Propositions 4.2–4.3; Assumption 4.4 and Theorem 4.4. For example, p. 22 reads "Assumption 4.1 holds … Proof of Proposition 4.1".

**Consequence:** Readability only.

**Proposed repair and completion criterion:** Use `\newtheorem{assumption}[theorem]{Assumption}`, or a visibly distinct numbering (e.g. `\renewcommand{\theassumption}{\Alph{assumption}}`). Complete when no printed number is shared by two objects and the rebuild is clean.

**Dependencies:** none.

**Verification:** X07-01 (cross; confirmed-with-changes, `X07.low.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f76"></a>

### F76. Notation clashes: the penalty $j$ and the index $j$, script $\mathcal H$, $W$, recycled letters, and symbols used before definition

**Importance:** Presentation · **Type:** presentation (notation) · **State:** Open · **resolved?** no

**Location (d430d75):** setting 141–156, 239–269 (pp. 6–7); proof-long-time 51–101, 349–354, 445–459, 522, 534, 620 (pp. 46–51); proof-mean-field 515, 911–916, 2877–2879 (pp. 29, 31, 44); introduction 11; setting 28; mean-field 444; proof-mean-field 531, 708, 1045, 1271; mathematical-preliminaries 8, 16–35; finite-dim 234; and the further locations listed in `runs/r1/reports/X04.cross.md` (X04-12).

**Finding and evidence (established, except item 6):**
1. The penalty $j$ (with $j'$, $j''$, $L_j$, $m_j$) and the unlabeled index $j\in I_{\mathcal U}$ meet in Algorithm 3.2 itself; Appendix C adds constants $j_-$, $j_+$, $j_\kappa$ inside $j$-indexed displays ($v_j^t:=j_-(\mathfrak c_j^t-\mathfrak c_j^{t+1})$). Rename the constants (e.g. $\varsigma_\pm$).
2. Script $\mathcal H$ is both the Hilbert space $\mathbb R\times L^2(\tilde{\mathbb P}^{[w]})$ and the $\sigma$-fields $\mathcal H^{[g]}_t$, $\mathcal H^{[w]}_t$ within 50 lines of Appendix C; $H$ also denotes $H_d$, a test function, and the arrays $H^{(m)}$. Rename the $\sigma$-fields.
3. $W$ is the Wasserstein distance, the weight-trajectory matrices ($W_2$ at $t=1$ in (104) reads $W_2(\nu(\mu,W_2,P_1),\dots)$), and a scalar bound in Lemma C.4.
4. Used before or without definition: $[\![1,n]\!]$; $\mathscr L(\cdot)$ for law; $\stackrel d=_{\mathcal F_t}$ (F09); the finite-dimensional $\Omega$; $\tilde{\mathbb E}_{\mathcal U}$; whether $\mathbb N$ contains $0$ ($\mathbb N_{\ge1}$ and $\mathbb N^*$ both used); $\lambda_{\max}$ next to the penalty coefficient $\lambda$.
5. Other recycled letters, worst within a single proof: $\mathcal A_\kappa$ beside $\mathcal A\in\{\mathcal L,\mathcal U\}$; $\eta$, $\xi$ redefined as $\pi_LZ$, $\pi_KZ$ in the proof of Lemma B.7; $\epsilon$ and $\varepsilon$ in one display; $p$ as class proportion, Wasserstein order, vectors $p^t$, and a dimension in Lemma B.5; $\pi$, $\mu$, $\nu$ as a coupling and measures in Definition E.1; $T$ as horizon, pushforward map, and branch map $T_{\mathfrak c}$.
6. (single-check, X08-14) the same clashes for $j$, $\bar\alpha$ (F53), $p$, $\pi$/$\mu$/$\nu$, and $T$.

**Consequence:** Readability only.

**Proposed repair and completion criterion:** Rename the clashes that occur within one proof or display (items 1–3 and the within-proof cases of item 5); add $[\![a,b]\!]$, $\mathscr L(X)$, and the convention for $\mathbb N$ to the opening of Section 3; define $\tilde{\mathbb E}_{\mathcal U}$ next to $\tilde{\mathbb P}_{\mathcal U}$. Complete when no proof uses one letter with two meanings.

**Dependencies:** F09, F53–F55.

**Verification:** X04-04, X04-08, X04-10, X04-12, X04-14 (cross; each confirmed-with-changes and recategorized to Presentation, `X04.low.md`); X08-14 (usage; single-check).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f77"></a>

### F77. Single-check presentation points: Sections 3–4.1 and Appendix A

**Importance:** Presentation · **Type:** presentation · **State:** Open · **resolved?** no

**Location (d430d75):** proof-finite-dim 6–7, 89, 186–192, 262–278, 412–448, 483–489 (pp. 22–25); finite-dim 68–116, 236–240 (pp. 8–9).

**Finding and evidence (single-check):** (1) proof-finite-dim 6–7 prints "in A.1, then establish global descent A.2.1, finite branch identification A.2.2, and convergence A.2.3" (bare references; see F82). (2) proof-finite-dim 89 "The explicit formula for $\Psi_\kappa$" should cite `eq:psi-kappa-formula`, otherwise unreferenced. (3) Lemma A.1 states (65) for $t\ge1$ although the proof gives every $t\ge0$. (4) Labels of (66)–(67) are unreferenced, the second sum of (66) is unused, and $\Delta\theta^t\to0$ is derived again at 408–409. (5) Proposition 4.1 defines $\psi_\kappa$, $\Psi_\kappa$, $V$, $V_{\mathcal U}$, $\mathcal S_\kappa$ inside its statement, then uses them as global notation. (6) proof-finite-dim 412–421, 435–441 use $G=\nabla L_{\mathfrak c}$ on $\Theta_{\mathfrak c}$ without citing Proposition 4.2 (`prop:configuration-branch-formulation`), and 447–448 use strict convexity and the unique minimizer without citing Proposition 4.3. (7) The upper Hessian bound (F05).

**Consequence:** None mathematically.

**Proposed repair and completion criterion:** Apply the listed edits (references by label, \eqref, optional $t\ge0$). Complete when each point is fixed or explicitly retained.

**Dependencies:** F05, F64, F82.

**Verification:** P1-05, P2-06 (unit; single-check; reports `P1.unit.md`, `P2.unit.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f78"></a>

### F78. Single-check presentation points: Section 4.2 and Appendices B and E

**Importance:** Presentation · **Type:** presentation · **State:** Open · **resolved?** no

**Location (d430d75):** mean-field 12, 141–422, 450–477, 542–545 (pp. 9–13); proof-mean-field 6–9, 414–926, 933–934, 1057–1061, 1188–1189, 1588–1764, 1850, 2046–2122, 2215–2428, 2608–2692, 2750–2767, 2848–2894, 3084 (pp. 25–46); mathematical-preliminaries 14–145 (pp. 58–59); proof-numerical 43 (p. 56).

**Finding and evidence (single-check):** Representative points (full numbered lists in the reports named below):
1. **Non-conformable formula:** proof-mean-field 1850 displays $M(W,G)=(UW)W^\dagger+(G^\top)^\dagger(U^\top G)-\Pi_G(UW)W^\dagger$; the middle term should be $(G^\top)^\dagger(U^\top G)^\top$ (equivalently $(G^\dagger)^\top G^\top U$); as printed it is $n\times k$ times $d\times k$. The measurability conclusion at 1852–1853 is unaffected.
2. **Definition 4.6 ordering and wording:** "these linear systems" precedes the systems (mean-field 181–183); the items are not in evaluation order (e.g. $\phi^{[w]}(t,\cdot)$ at 207–215 uses $\tilde p^u$ defined at 317–328); one sentence giving the construction order $\tilde w^t\to(\tilde q^t,\tilde r^t,\tilde g^t)\to(\tilde p^t,\tilde w^{t+1})$ would help; comma splice at 141–143; the convention $\ell'(0,r):=0$ and the factor $|\tilde c^t|$ in (35) do the same job.
3. **$r^T$:** Theorem 4.7(ii) uses $r^T$, but Algorithm 3.2 computes scores only for $t\le T-1$ (setting 229–236); add $r^t:=b^t\mathbf 1_n+Xw^t/\sqrt d$ for all $t\ge0$.
4. **Test law of Corollary 4.8:** $\mathcal E^t$ is written as an unconditional probability but described as conditional on the training data; the test-point law is given only in the proof (proof-mean-field 3028–3042).
5. **Undefined trajectory vectors:** $\tilde W_t$, $\tilde P_t$, $\tilde Q_t$, $\tilde G_t$, $\tilde R_t$ (proof-mean-field 785–915, 2094–2105, 2879, 2894); $S_i^t$, $\hat Y_i^t$ written for all $i$ in (76) though defined only for unlabeled $i$ (harmless).
6. **Lemma B.7 local symbols** collide with global notation ($T$, $X$, $Y$, $\eta$, $\pi$, $m$, $F$, $A$); "almost surely" at 1689–1692 holds surely; `\hspace{3pt}` patch at 1786.
7. **Proofs of Proposition B.4:** "the map defined in (`eq:residual-map`)" (2426–2428) points to a display that defines $g_i^t$, not a function of $(\rho,y,a,r)$; at $t=0$ only $\alpha^{[g]}_0$ is empty, not $\phi^{[g]}_0$ (2608–2609); "by construction" at 2759–2767 should point to Lemma B.1's one-step display (F14).
8. **Citations' wording:** the "coupling characterization" at 1057–1061 attributes to Villani what Kallenberg Theorem 5.31 supplies; Kallenberg titles Theorem 5.12 "$L^p$-convergence", not "Vitali"; Theorem 5.31 and Lemma 5.11(ii) are cited without naming them.
9. **Other wording:** "2-pseudo-Lipschitz" vs "pseudo-Lipschitz of order $p$"; "finite dimensional"; "For sufficiently large $d$" attached to the log-odds formula in proof-numerical 43, which holds for every $d$; $\mathscr P_2(\mathcal X)$ undefined (Appendix E defines only $\mathscr P_p(\mathbb R^r)$); the measure in "continuous at $(\bar\beta,\tilde H)$ almost surely" (1005–1006) is unnamed; "Assumptions~\ref" singular at 3084.

**Consequence:** None mathematically (item 1 is a typo in a measurability argument).

**Proposed repair and completion criterion:** Apply the listed edits; item 1 is confirmed by a dimension count. Complete when each point is fixed or explicitly retained.

**Dependencies:** F09, F14, F15, F55, F82.

**Verification:** M1-05, M2-05, M3-08, M4-05, M5-04, M6-02, M7-07 (unit), C1-09 (chain), G1-03-05, G1-02-04 (gap tasks), X05-06 (cross); all single-check (reports `M1.unit.md`–`M7.unit.md`, `C1.chain.md`, `G1-03.unit.md`, `G1-02.cross.md`, `X05.cross.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f79"></a>

### F79. Single-check presentation points: Section 4.3 and Appendix C

**Importance:** Presentation · **Type:** presentation · **State:** Open · **resolved?** no

**Location (d430d75):** long-time-behavior 31–49, 99, 139–252 (pp. 13–15); proof-long-time 55, 62–68, 74–79, 126–146, 167–181, 240–245, 294, 306–811, 813–1292 (pp. 46–55).

**Finding and evidence (single-check):** Representative points (full lists in the reports named below):
1. proof-long-time 74–79: "we have $\mathcal H^{[g]}_{t+1}:=\dots$" introduces a definition (write "define"; it duplicates proof-mean-field 167–175).
2. proof-long-time 126–131: four bare \ref's ("the branch Hessians C.1", "the mean-field limit C.2.1").
3. proof-long-time 139: "This gives us the following lemma" — Lemma C.1 does not follow from the choice of $\Lambda_*$; 143–146: quantify $\Lambda_*$ in the statement.
4. $Y_{\mathcal A}$, $U_{\mathcal A}$, $\tilde{\mathbb E}_{\mathcal U}$ used without definition in Appendix C (167–181, 55, 372–427).
5. proof-long-time 62–68, 240–245: cite Corollary E.7 and Lemma B.5 at the point of use; 294: "The preceding bounds imply $\mathbb P(\mathcal E_d)\to1$" also uses `eq:limiting-labeled-class-proportion` and $V(\theta^1)\to\bar V^1$.
6. Symbol reuse: jump magnitudes $j_\pm$, $j_\kappa$ (F76); direction $(h,u)$ reusing $h(s,t)$; $C$, $Q$, $Q_*$, $Q_{\mathcal L}$, $a$, $\gamma$, integration variable $s$; $\Delta\theta$ beside $\Delta$, $\tilde\Delta$; $e$ for three objects; constant $A$ and population index $\mathcal A$ in the same proof.
7. The bound `eq:configuration-switching-gaussian-bound` holds on $\mathcal R_d$ only for all sufficiently large $d$; the lead sentence omits this.
8. Scores converge in "$L^2(\tilde{\mathbb P})$" while $\mathcal H$ uses $L^2(\tilde{\mathbb P}^{[w]})$; naming $L^2(\tilde{\mathbb P}^{[g]})$ would show the two limit spaces differ; "the function $f$ from (128)" should be "the functions $f_{\mathfrak c}$" (837).
9. $\tilde{\mathbb P}_{\mathcal U}$ used before it is defined (long-time-behavior 168, 175); Proposition 4.9 "for every finite $t\ge1$" ("finite" redundant); the hyperparameter range for Proposition 4.9 is not stated.

**Consequence:** None mathematically.

**Proposed repair and completion criterion:** Apply the listed edits; a reader should be able to follow Appendix C without consulting Appendix B for notation. Complete when each point is fixed or explicitly retained.

**Dependencies:** F08, F21, F26, F70, F71, F76, F82.

**Verification:** L1-06, L2-03, L3-05 (unit), C2-06 (chain), G1-04-03 (gap task); all single-check (reports `L1.unit.md`, `L2.unit.md`, `L3.unit.md`, `C2.chain.md`, `G1-04.cross.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f80"></a>

### F80. Single-check presentation points: Section 5, Appendix D, figure captions, and code documentation

**Importance:** Presentation · **Type:** presentation · **State:** Open · **resolved?** no

**Location (d430d75):** numerical 26, 32–40, 57–117, 185–200, 224–225, 237, 256–263, 440 (pp. 15–18); proof-numerical 35–36, 43, 63, 227, 268–275 (pp. 56–57); mean-field 141–143, 185, 533–540; code `e823bf3`: `README.md` 20–28, 65, 184–187, 216–229; `docs/effective_process.md` 7.

**Finding and evidence (single-check):**
1. $\beta_\star(\alpha;p)$ (subscript star, a function) beside $\alpha^\star$, $\beta^\star$ (superscript star, numbers); mixed star and asterisk.
2. Section 5 never says where Propositions 5.1–5.3 are proved (`sec:proof-numerical` is never referenced).
3. proof-numerical 268–275: the last equality $\tilde r^{t,\sharp}=\bar b^t-\bar m^t\tilde Y-\sigma\tilde q^t=-\tilde r^t$ uses $\bar b^t=0$ silently.
4. Equality in law typeset as `\overset{ d}{=}` (proof-numerical 227) and `\overset{\mathrm d}{=}` (numerical 440).
5. numerical 237: "They propose" refers to the single-author Takahashi.
6. Captions omit the horizons (300 and 400) and seeds (42–61; 49); the Figure 1 caption could say that each run has an independent particle system.
7. Code documentation: README says `n_iterations=500` (the notebook and Figure 2 use 400); README clone and citation URLs use the old repository name `FeedbackDynamicsOfSelfTraining` while the paper's footnote uses `HighDimensionalDynamicsOfSelfTraining`; README describes only the macOS setup and says full configurations were not run (they now reproduce on Linux); no license; `docs/effective_process.md` cites a nonexistent manuscript section (F34).
8. Duplicate definitions and the $\bar\alpha^t$ clash (F53, F71); the Figure 1 versus Figure 2 configuration (F35).

**Consequence:** Presentation and reproducibility only.

**Proposed repair and completion criterion:** Apply the listed edits; for the code, update the README, align the URLs, and decide on a license. Complete when each point is fixed or explicitly retained.

**Dependencies:** F02, F32–F35, F53, F71.

**Verification:** N1-06 (unit), X02-08, X13-04, X09-07 (cross); all single-check (reports `N1.unit.md`, `X02.cross.md`, `X13.cross.md`, `X09.cross.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f81"></a>

### F81. Single-check presentation points: abstract, introduction, and related work

**Importance:** Presentation · **Type:** presentation · **State:** Open · **resolved?** no

**Location (d430d75):** main 95 (abstract, p. 1); introduction 10–29, 59–72, 133–141 (pp. 2–3); related_work 45–46, 81, 173, 180–183, 197–198 (pp. 4–5); numerical 218–219, 387–390 (pp. 17–18).

**Finding and evidence (single-check):**
1. introduction 133–136: missing "and" before the last item of the list of questions.
2. main 95 says "linear classifiers", introduction 14 "affine classifiers" (the model has an intercept).
3. introduction 59–72: $\mathcal L(\theta;\mathcal D_{\mathcal L},\mathcal P_t)$ hides that the pseudo-labeled term is weighted by $\pi$ and normalized by $M$, not by $\#\mathcal P_t$; point to `eq:ST-objective`.
4. $\mathcal D$ and $I_{\mathcal U}$ are defined in both the introduction and Section 3, and $\operatorname{sign}(0)=+1$ is stated only in the introduction (line 26) although setting 154 relies on it; the label `eq:def-classifier` is never referenced.
5. introduction 140–141: the Section 2 roadmap omits Section 2.3 (F39).
6. related_work 45–46: "these features" has as antecedent the prior works' features (fresh batches, stagewise minimization), which the paper does not incorporate.
7. Inconsistent author naming: "Wu et al." (related_work 81) vs "Wu, Yang, and Sun" (numerical 218–219).
8. related_work 173: "Rigorous AMP analysis relies on Gaussian conditioning" is overgeneral (suggest "For Gaussian matrices, …"); 180–183: "Yang's tensor programs" cites Yang and Hu; numerical 387–390: the long-time DMFT list omits Celentano et al. and the paper's own Theorem 4.10; 197–198: optionally attribute "finite-horizon" and "equilibrium" to the respective papers.

**Consequence:** Presentation only.

**Proposed repair and completion criterion:** Apply the listed edits. Complete when each point is fixed or explicitly retained.

**Dependencies:** F38–F43.

**Verification:** X03-06, X06-06, X12-07 (cross); all single-check (reports `X03.cross.md`, `X06.cross.md`, `X12.cross.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f82"></a>

### F82. Single-check presentation points: cross-reference style and typography across the paper

**Importance:** Presentation · **Type:** presentation · **State:** Open · **resolved?** no

**Location (d430d75):** proof-mean-field 6–9, 678, 933–934, 1588, 1592, 3084 (pp. 25, 30, 31, 36, 46); proof-finite-dim 6–7 (p. 22); proof-long-time 126–131 (p. 47); mean-field 185, 199–377 (p. 11); long-time-behavior 31–33 (p. 13); finite-dim 132; numerical 26, 440.

**Finding and evidence (single-check):**
1. About 20 bare \ref's print without an object name, e.g. "the effective process 4.6 is well defined in B.1" (p. 25), "lemma B.7", "histories B.8" (p. 36), "branch Hessians C.1" (p. 47). Because A.1, B.1–B.5, and C.1 are each both a section and a result number, these are ambiguous ("C.1" on p. 47 means Lemma C.1, "B.1" on p. 25 means Section B.1).
2. `\eqref{definition:empirical-measures}` (proof-mean-field 678) prints "(E.6)" as if an equation.
3. Double period "distribution.." at mean-field 185 (still present from the November 4 code-repository audit).
4. "Assumptions~\ref{assumption:asymptotic-regime}" (plural, one assumption) at proof-mean-field 3084.
5. Three typographical forms of equality in law; `\hat Y_j(\theta)` at finite-dim 132 vs `\widehat Y` elsewhere; "the trajectory theorem and its corollaries in B.5" (one corollary); Proposition 4.9 lists "Assumptions 3.1, 4.3, and 4.2" out of order.
6. Definition 4.6 uses manual negative spacing (`\\[-7pt]` eight times, `\vspace{-21pt}` three times); the footnote URL ends in `.git`.
7. All 536 displays were scanned; no missing terminal punctuation.

**Consequence:** Navigation and readability only.

**Proposed repair and completion criterion:** Prefix every cross-reference with its type (Section~, Appendix~, Lemma~, Definition~, or use `\cref`); replace the \eqref with Definition~\ref; fix items 3–6. Complete when no bare \ref remains in live text and the rebuilt pages show the corrections without overlaps.

**Dependencies:** F39, F77–F79.

**Verification:** X01-09, X04-11, X07-02, X07-09 (cross); all single-check (reports `X01.cross.md`, `X04.cross.md`, `X07.cross.md`). Also supported by X07-03 (single-check; "Section A" versus "Appendix B" style, primary entry F39).

**Actual changes:** None. **Author decision:** Pending.

<a id="issue-f83"></a>

### F83. Single-check presentation points: theorem style, source comments, figures, and BibTeX capitalization

**Importance:** Presentation · **Type:** presentation · **State:** Open · **resolved?** no

**Location (d430d75):** main 40–46 (theorem styles); finite-dim 54, 95, 114, 118, 125, 132, 157, 184, 189, 212, 258, 271, 283, 300 and proof-finite-dim 45, 92, 139, 173, 198, 231, 252, 326, 341, 395, 449, 503–505, 546 (`% CHANGE:` comments, nonprinting); numerical 28–42, 185–200 (Figures 1–2, pp. 15, 17); related_work 81, 162–163, 189–190; references (entries [4], [6], [18], [19], [32], [35], [44], [57]).

**Finding and evidence (single-check):**
1. `%\theoremstyle{definition}` (main 42) is commented out, so Assumptions, Definitions (including the long Definition 4.6), and Remarks print in italic, contrary to the comment on main 41.
2. 25 `% CHANGE:` revision notes and a "This explanation is retained" comment remain in the shared source; every change they describe was checked as in place and harmless; the note at finite-dim 125–127 says $S_\kappa$ is undefined, but it is defined at setting 152.
3. Both figures are 600 dpi RGBA PNGs scaled down (Figure 1 is 8829×4617 px at 0.43); printed tick labels are about 4.5–5 pt and the Figure 1 legend about 4 pt; `[H]` placement leaves about 8% of p. 16 blank.
4. Inconsistent author naming before numeric citations: "Celentano, Cheng, and Montanari [8]" vs "Celentano et al. [8]", and similarly for [51].
5. The plain style lowercases unprotected words: "sgd" ([4], [35]), "sherrington-kirkpatrick" ([6]), "langevin" and "bayes" ([18], [19]), "hilbert" ([32]), "gaussian" ([44]), and "a" after "?" ([57]).

**Consequence:** Typography and source hygiene only.

**Proposed repair and completion criterion:** (1) Uncomment main 42 (optionally `\theoremstyle{remark}` for remarks). (2) Delete the comment blocks once the authors have reviewed them (`grep -c 'CHANGE:'` returns 0). (3) Regenerate the figures at final size as vector PDFs in `figures/` with fonts of at least 7 pt, and use `[t]`/`[htbp]`. (4) Adopt one naming convention. (5) Brace-protect `{SGD}`, `{Sherrington--Kirkpatrick}`, `{Langevin}`, `{Bayes}`, `{Hilbert}`, `{Gaussian}`, `{A}`. Complete when the rebuild is clean with no new box warnings and the corrections appear.

**Dependencies:** F58, F73.

**Verification:** X07-04, X07-07, X07-08, X07-10, X07-13 (cross), X11-02 (regression check); all single-check (reports `X07.cross.md`, `X11.cross.md`).

**Actual changes:** None. **Author decision:** Pending.

<a id="scope-and-method"></a>

## Scope and method

**Version audited.** Overleaf commit `d430d75` (November 5, 2026) of the paper, frozen as a byte-identical snapshot and built in place (60 pages, no LaTeX or BibTeX warnings, no over/underfull boxes; printed page = PDF page), and the companion repository `HighDimensionalDynamicsOfSelfTraining` at commit `e823bf3` (November 5, 2026). In scope: everything input by `main.tex` (abstract, Sections 1–5, Appendices A–E), Figures 1–2, the cited bibliography entries, and the code as it bears on the paper. Out of scope: commented-out source, `mathematical_background.tex` (not input by `main.tex`), the earlier notes repository, and the older experiment PDFs in the shared folder. Auditors worked independently of earlier review records; only the regression item (X11) read the November 4, 2026 audit in the code repository and the `% CHANGE:` notes, as records.

**Items and models.** Run r1 used 32 audit items. Fable 5.2 (`claude-fable-5-2`) ran the 13 proof units, which partition every live proof (P1–P2: Section 4.1 and Appendix A; M1–M7: Section 4.2 and Appendices B and E; L1–L3: Section 4.3 and Appendix C; N1: Section 5 and Appendix D), the two chain audits (C1: Definition 4.6 → Lemma B.1 → Proposition B.4 → Theorem 4.7 → Corollary 4.8; C2: Sections 4.1–4.2 → Proposition 4.9, Theorem 4.10, Corollary 4.11), and one gap task (G1-03: Theorem 4.7 against rigorous GD/DMFT results and the $\pi=0$ reduction). Opus 5.5 (`claude-opus-5-5`) ran the cross-cutting items: statement–proof and hypothesis consistency (X01), interpretation and empirical claims against the figures (X02), front matter (X03), notation (X04), external mathematical results (X05), literature (X06, X12), build, cross-references, and bibliography metadata (X07), the usage and redundancy audit (X08), code and figure provenance (X09), a hostile referee (X10), the regression check (X11), an independent simulation written from the paper alone (X13), and three gap tasks proposed by the completeness critic (G1-01: simulation of the Section 5.3 intercept variants; G1-02: primary-source check of every numbered external pointer in Appendices B and E; G1-04: numerical check of the long-time regime). Opus also ran the Low-finding batch verifiers, the completeness critic, and this consolidation. In total about 93 agents ran before consolidation (32 auditors, 27 individual verifiers for the 13 findings reported Medium or higher, 32 batch verifiers, and the critic), with 21 Fable calls and no fallback from Fable to Opus.

**Verification.** Every finding reported Medium or higher received two independent verifiers (three for G1-01-01, reported High), on Fable for proof-unit and chain findings and on Opus for cross-cutting findings; Low findings received one Opus batch verifier per item; Presentation findings are single-check. Of 202 findings, 159 were confirmed (most with corrections, incorporated above), 41 are single-check Presentation findings, and 2 were rejected: M3-03 (the pseudo-inverse claim is covered by Lemma B.5 as stated, applied to the column subarray) and X02-07 (the Hessian display at finite-dim 236–240 sits under the standing $\lambda>0$ of setting 160). No finding remained unresolved, and no entry is Critical or High, so no post-consolidation spot-check is required.

**Figure reproduction and code.** Before the audit, both figure notebooks were executed unchanged on a separate Linux machine (CPython 3.9.25, the repository's pinned numpy and torch versions) and the test suite was run (154 passed). The regenerated `approximation_accuracy.png` and `statistical_behavior_comparison.png` are pixel-identical to the figures in the paper, so the stored results are the data behind Figures 1–2. X09 read the code line by line: the finite-dimensional code implements Algorithm 3.2 exactly, the particle effective process is an exact algebraic reformulation of Definition 4.6 (checked symbolically and by an independent transcription, agreement to $10^{-12}$), the observables match Corollaries 4.8 and 4.11 and the regret decomposition, and every caption parameter matches the notebooks. Its findings are F02 and F32–F34.

**Independent simulations.** X13 implemented Algorithm 3.2 and Definition 4.6 from the paper alone (without reading the code) and compared them over eight regimes, including Figure 1's and Figure 2's parameters, asymmetric thresholds, a nonzero initial intercept with $w^{\rm init}$ correlated with a non-Gaussian $\mu$, $\bar\delta=2$, $\sigma=1.5$, $\pi=0$, and $\lambda=1$, for $d=500$–$8000$ with 50,000–100,000 particles per side: Definition 4.6 is confirmed (finite-$d$ errors shrinking roughly like $d^{-1/2}$; two deliberately wrong readings fail clearly), and Proposition 5.3 is confirmed. G1-01 re-simulated the Section 5.3 claims (30 seeds at the Figure 2 configuration and 10 at the Figure 1 configuration, three intercept rules, cross-checked against the effective process); its results are in F03, F35, and F37. G1-04 checked the long-time regime up to $d=32000$ and $T=1500$ with up to $10^6$ particles: the hypotheses of Theorem 4.10 are nonvacuous for logistic loss with ridge penalty, the effective process stabilizes as Corollary 4.11 asserts, and $T_{\rm id}$ grows with $d$ as Proposition 4.9 predicts; non-stabilization appeared only when a hypothesis was removed ($\lambda=0$). G1-03 showed analytically that the projection-defined coefficients of Definition 4.6 are the DMFT response functions and that at $\pi=0$ (no intercept) Definition 4.6 coincides with the discrete systems of Gerbelot et al. and Celentano–Cheng–Montanari and with a discretization of Mignacco et al. (2021). Numerical agreement supports but does not prove the stated results.

**What remains unchecked or partly checked.** Ethier–Kurtz Ch. 3 Proposition 4.4 could not be obtained (F56; the operative Worm–Hille pointer is verified). Bolthausen (2014) has no result pointer to check. Fan et al. and the primary texts of Paquette et al. and Ben Arous et al. were not opened for the literature descriptions (their bibliography metadata were checked). Author lists of the NeurIPS bibliography entries were spot-checked only. The literature search for omitted work (F45, F52) was not exhaustive. The interchange of the limits $d\to\infty$ and $t\to\infty$ is not addressed by the paper and was not attempted (F27). Separate from these issue-level checks, this register does not certify a final paper-wide submission review.
