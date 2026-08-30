# VAR / VECM

**Version:** 2.3.0

VAR lag selection uses the **training window only** (`train_end`). Full-sample lag shopping is a leak. Impulse responses are an own-shock AR(1) diagnostic, not a companion-matrix IRF. VECM here is an Engle-Granger error-correction representation, not Johansen rank.
