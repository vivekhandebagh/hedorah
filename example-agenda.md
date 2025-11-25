# Mechanistic Interpretability Research Agenda

## Current Focus
I'm trying to understand how features emerge and interact in transformer language models.
Specifically interested in:
- The "features as directions" hypothesis
- Whether superposition is inevitable or an artifact of training dynamics
- How attention heads coordinate to implement algorithms

## What I'm Looking For
- Novel probing techniques beyond linear probes
- Experiments that reveal feature geometry in activation space
- Connections between information theory and representation learning
- Papers that challenge conventional interpretability wisdom

## Constraints
- Single RTX 3090 (24GB VRAM)
- Experiments should be completable in < 8 hours
- Prefer working with GPT-2 scale models or smaller
- No access to training compute - working with pretrained models only

## Questions I'm Trying to Answer
1. Can we predict which features will be superimposed based on training data statistics?
2. Is there a phase transition in feature formation during training?
3. Do attention heads specialize before or after MLPs develop features?
4. What's the relationship between polysemanticity and model capability?

## Not Interested In
- Scaling laws (already well-studied)
- RLHF and preference learning
- Deployment safety and red-teaming
- Benchmarking / eval-focused work
- Pure prompt engineering

## Current Hunches
I suspect attention heads are doing something like "soft clustering" of features
in residual stream, and MLP layers perform the actual computation on these clusters.

There might be a connection between the lottery ticket hypothesis and feature
superposition - maybe "winning tickets" are just features that avoided superposition?

The fact that SAEs work suggests features ARE linearly represented, but the
reconstruction loss suggests we're missing something about how they combine.
