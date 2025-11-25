---
title: "Circuit-Level Mechanisms of GCMC Emergence in Recurrent Neural Networks"
created: 2025-11-24T22:08:45.145661
tags:
  - experiment
  - proposal
source_paper: "Neural Manifold Capacity Captures Representation Geometry, Correlations, and Task-Efficiency Across Species and Behaviors"
experiment_id: "circuit_gcmc_emergence"
difficulty: "hard"
status: "proposed"
---

# Circuit-Level Mechanisms of GCMC Emergence in Recurrent Neural Networks

## Research Context
**Source Paper:** [[Neural Manifold Capacity Captures Representation Geometry, Correlations, and Task-Efficiency Across Species and Behaviors]]
**Status:** Proposed | **Difficulty:** hard | **Est. Time:** 2-3 weeks

### Motivation
Understanding how GCMC measures emerge from specific neural circuit properties is crucial for predicting how interventions or pathologies might affect representational geometry. This experiment addresses the mechanistic gap by systematically varying circuit parameters and observing their effects on GCMC.

### Hypothesis
GCMC measures will systematically vary with specific circuit properties: (1) recurrent connection strength will modulate manifold dimensionality, (2) inhibitory balance will affect correlation structure, and (3) network depth will influence task-relevant geometry. We expect to find characteristic relationships that can predict GCMC from circuit parameters.

### Source Insights
- Lack of mechanistic understanding of how GCMC measures emerge from underlying neural circuit dynamics

## Experimental Design

### Objective
Establish causal relationships between circuit-level parameters and GCMC measures to enable prediction and control of representational geometry

### Variables
| Type | Variables |
|------|-----------|
| Independent (manipulate) | recurrent_connection_strength, inhibitory_balance, network_depth, connection_sparsity |
| Dependent (measure) | manifold_dimension, correlation_structure, readout_efficiency, task_performance |
| Controlled | input_dimensionality, training_procedure, task_complexity, network_size |

## Parameters
| Parameter | Type | Description | Default/Range |
|-----------|------|-------------|---------------|
| recurrent_strength_range | list[float] | Range of recurrent connection strengths to test | [0.1, 0.5, 1.0, 1.5, 2.0] |
| inhibitory_fractions | list[float] | Proportion of inhibitory neurons in the network | [0.1, 0.2, 0.3, 0.4] |
| network_depths | list[int] | Number of hidden layers in the network | [2, 4, 6, 8] |
| n_trials | int | Number of random initializations per condition | 20 |
| task_types | list[str] | Types of tasks to evaluate | ['classification', 'regression', 'working_memory'] |

## Procedure

### 1. Network Construction
- [ ] Generate network architectures with varying circuit parameters
- [ ] Initialize weights according to specified connectivity patterns
- [ ] Implement balanced excitatory-inhibitory dynamics

```
for each parameter combination:
    network = RNN(recurrent_strength, inhibitory_balance, depth)
    networks.append(network)
```

### 2. Training and Activity Recording
- [ ] Train networks on standardized tasks until convergence
- [ ] Record neural activity during task performance
- [ ] Extract population activity patterns across all conditions

```
for network in networks:
    train(network, task)
    activity = record_population_activity(network, test_stimuli)
    activities[network_params] = activity
```

### 3. GCMC Analysis
- [ ] Compute GCMC measures for each network configuration
- [ ] Calculate manifold dimensionality, correlation structure, and readout efficiency
- [ ] Perform statistical analysis linking circuit parameters to GCMC measures

```
for activity in activities:
    gcmc_measures = compute_gcmc(activity)
    correlations = correlate(circuit_params, gcmc_measures)
    statistical_models = fit_regression(circuit_params, gcmc_measures)
```

## Expected Results
| Result | Type | What it tells us |
|--------|------|------------------|
| parameter_gcmc_correlations | dict[str, dict[str, float]] | Correlation coefficients between circuit parameters and GCMC measures |
| predictive_models | dict[str, object] | Regression models that can predict GCMC measures from circuit parameters |
| mechanistic_principles | list[dict[str, str]] | Identified principles linking circuit structure to representational geometry |

## Implementation Notes
**Suggested Tools:** PyTorch, NumPy, scikit-learn, matplotlib, seaborn
**Prerequisites:** Neural network implementation framework, GCMC computation algorithms, Statistical analysis tools

---
*Implementation notes and results go below*
