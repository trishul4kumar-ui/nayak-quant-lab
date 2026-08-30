# Model Risk Management

**Version:** 2.3.0  
**Package:** `quantlab.certification`  
**ADR:** [ADR-037](../decisions/ADR-037-model-risk-validation-certification.md)

Model risk is assessed across conceptual, data, implementation, parameter, estimation, overfitting, regime, liquidity, execution, operational, software, dependency, monitoring, and governance categories. Severity is `LOW|MEDIUM|HIGH|CRITICAL|NOT_ASSESSED` with no hidden default. `NOT_ASSESSED` is honest; it is not LOW.
