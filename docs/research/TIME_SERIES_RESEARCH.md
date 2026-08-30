# Time-Series Research

**Version:** 2.3.0

OLS, HAC, ACF/PACF, Ljung-Box, and AIC helpers live in `quantlab.econometrics.linalg`. Small samples return `None` rather than fabricated statistics. HAC reuses Newey-West on the estimation window only.
