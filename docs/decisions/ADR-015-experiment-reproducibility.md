# ADR-015 — Experiment reproducibility

## Context
Prompt 02 success criterion 12: reproduce the same experiment.

## Problem
Random experiment IDs must not change metrics. Undeclared seeds must not exist.

## Options
1. Trust notebooks
2. Ledger stores hyperparameters, dataset version, cost model, seed; slice is pure given those
3. MLflow immediately

## Decision
Option 2. Two runs with the same inputs must match metrics exactly. IDs may differ.

## Consequences
- Synthetic provider is deterministic
- Integrity + metrics are part of the record
