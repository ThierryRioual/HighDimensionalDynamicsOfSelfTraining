# Manuscript revision: selected stabilization wording and F59–F83

This records changes applied to the current working sources, preserving the author's intervening edits. The original Fable register describes its frozen audited version and was not rewritten or treated as a new certification.

The main contributions remain threefold. Section 5 remains supporting numerical/statistical interpretation. The shortened order-two mathematical preliminaries are retained. The limiting-configuration identity remains under the full measure, with the author's explicit labeled-observation extension.

## Changes

Line numbers below refer to the revised source at the time this report was generated.

| Item | Disposition | Revised location | Change |
| --- | --- | --- | --- |
| Selected stabilization wording | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/introduction.tex:132` | Uses parameter and score processes, states the order of limits, and describes eventual stabilization of selection and the assigned label when selected. |
| F59 | Applied / already present | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-mean-field.tex:720` | Removed the unused duplicate proposition label and all unused master-item labels; retained the model label already added by the author. |
| F60 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/long-time-behavior.tex:80` | Reduced the normalization to j(0)=0; the proof derives j'(0)=0 from differentiability and nonnegativity. |
| F61 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/long-time-behavior.tex:84` | States that the stronger curvature assumptions imply the finite-horizon regularity assumptions with the same constants. |
| F62 | Retained | `latex/High_Dimensional_Dynamics_of_Self_Training/setting.tex:113` | Kept the intended interior class-proportion condition. |
| F63 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/mean-field.tex:113` | Identifies the limiting signal law as the first marginal of the joint initialization law. |
| F64 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-finite-dim.tex:86` | Added the segment argument for the branch-closure description; retained useful geometric conclusions. |
| F65 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-finite-dim.tex:567` | Removed the unreferenced further-consequences remark; retained the finite-length conclusion. |
| F66 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-mean-field.tex:726` | Replaced repeated master-recursion conditional-law displays by references, redirected their later uses, and used ordinary induction. |
| F67 | Retained | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-mean-field.tex:61` | Kept the short, correct atomlessness consequence, including zero. |
| F68 | Retained | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-mean-field.tex:948` | Kept the sufficient technical conditions in the empirical-law lemmas. |
| F69 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/mathematical-preliminaries.tex:91` | Restored the Lipschitz pushforward lemma for W2, proved it directly by pushing couplings forward, and cited it at the projection steps. Added a short proof of the empirical-observable corollary. |
| F70 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-long-time.tex:55` | Recorded the full-sample score-distance limit and reused it in the two-time stability argument. |
| F71 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/long-time-behavior.tex:218` | Replaced repeated definitions by reminders; defined selected-error probability before its first convergence statement; retained the author's full-P extension. |
| F72 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/numerical.tex:305` | Explained the role of the sign condition and identified the intercept recursion as recalled from Definition 4.6. |
| F73 | Applied / retained | `latex/High_Dimensional_Dynamics_of_Self_Training/main.tex:23` | Removed the misleading link-color comment. Kept packages and macros. |
| F74 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/long-time-behavior.tex:54` | Clarified the nonuniform onset of the geometric estimate, without claiming a noncommutation theorem. |
| F75 | Retained | `latex/High_Dimensional_Dynamics_of_Self_Training/main.tex:44` | Kept separate assumption numbering. |
| F76 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/introduction.tex:10` | Defined basic notation, renamed threshold jump constants to varsigma, distinguished Hilbert space and histories, and removed unused conditional-population notation. |
| F77 | Applied / already present | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-finite-dim.tex:6` | Added typed roadmap references and the potential-formula citation; cited the branch-gradient proposition. The author's F07 proof already contains the remaining convergence citations. |
| F78 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-mean-field.tex:1849` | Corrected the transpose, defined terminal scores and effective trajectory vectors, made test-error conditioning explicit, defined the residual map, and corrected the t=0 coefficient wording and continuity notation. |
| F79 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-long-time.tex:150` | Moved the conditional law notation before first use, clarified the deterministic curvature parameter and eventual-d bounds, reused history definitions, and distinguished the sample-side L2 space. |
| F80 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/numerical.tex:4` | Added proof pointers, explicit use of b=0, consistent equality-in-law typography, horizons/seeds in captions, and corrected README metadata. Kept license status unchanged. |
| F81 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/main.tex:96` | Used affine-classifier wording, clarified surrogate normalization and sign ties, improved source attribution, and replaced an overly broad long-time methodological claim with a precise open question. |
| F82 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/proof-mean-field.tex:6` | Corrected reference types, singular/plural wording, and the repository URL; retained manually tuned spacing after visual review. |
| F83 | Applied | `latex/High_Dimensional_Dynamics_of_Self_Training/main.tex:43` | Used roman definition/assumption bodies and remark style, removed obsolete CHANGE comments, protected bibliography capitalization, switched to vector figures with final-size fonts, and allowed normal figure floats. |

## Mathematical preliminaries

The new pushforward lemma is restricted to W2, matching the shortened appendix and all its applications. It has a direct coupling proof. The standard Wasserstein characterization remains sourced to the references already supplied by the author; only the elementary pseudo-Lipschitz bridge and random-measure subsequence argument are proved locally. The empirical-observable corollary now explicitly invokes continuity and the continuous mapping theorem. The unnecessary, previously unverified Ethier–Kurtz secondary pointer was removed; the verified Worm–Hille proposition remains.

The impossible sentence `kappa_-=-kappa_+>0` was corrected to `kappa_-=-kappa_+<0`, consistently with the standing threshold assumptions.

## Verification

- Existing Python test suite: **187 passed**.
- Static source checks: no missing references, duplicate labels, missing citation keys, or unmatched LaTeX environments in the live manuscript.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` succeeds and produces a **61-page** PDF.
- No undefined-reference or citation warnings; no overfull boxes. One underfull paragraph warning (badness 2310) is present in both the before and after builds.
- All pages were rendered for a layout overview; affected theorem/definition pages, figures, and the shortened preliminaries were also inspected at higher resolution. No clipping or overlaps were observed in these renders.
- Figure 1 vector export uses the preserved corrected 20-run trajectories from `outputs/f02_comparison/results.pkl`.
- Figure 2 was rerun with the exact notebook configuration. Before typography changes, its regenerated PNG is **pixel-identical** to the original `pdfs/statistical_behavior_comparison.png`.
- The original PNGs and historical simulation results were preserved. Both notebooks now export PDFs as well as their existing PNGs.

## Review artifacts

- Rebuilt manuscript: `latex/High_Dimensional_Dynamics_of_Self_Training/main.pdf`.
- Manuscript figure PDFs: `approximation_accuracy.pdf` and `statistical_behavior_comparison.pdf` in the same folder; copies are exported to `pdfs/`.
- This turn's source diff: `outputs/f59_f83_revision/source_changes.diff`.
- Figure 2 raw trajectories: `outputs/f59_f83_revision/statistical_behavior_results.pkl`.
- Figure previews and the Figure 2 reproduction PNG: `outputs/f59_f83_revision/`.

This was an implementation and targeted consistency review of the selected revisions, not a fresh line-by-line independent audit of every proof or a verification of every external book pointer. Findings outside the selected scope were not automatically marked resolved. The numerical recursion and the author's existing convention-refactor work were not changed in this turn.
