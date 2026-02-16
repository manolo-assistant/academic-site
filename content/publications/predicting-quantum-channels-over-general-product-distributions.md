---
title: "Predicting quantum channels over general product distributions"
date: 2024-09-05
params:
  authors: "Sitan Chen, Jaume de Dios Pont, Jun-Ting Hsieh, Hsin-Yuan Huang, Jane Lange, Jerry Li"
  journal: "Preprint (2024)"
  arxiv: "https://arxiv.org/abs/2409.03684"
  pdf: "https://arxiv.org/pdf/2409.03684"
  description: "We study how to efficiently predict the output of unknown quantum channels, extending the surprising sample-efficiency results of Huang, Chen, and Preskill to general product input distributions."
---

**Sitan Chen, Jaume de Dios Pont, Jun-Ting Hsieh, Hsin-Yuan Huang, Jane Lange, Jerry Li**

*Preprint (2024)*

We study how to efficiently predict the output of unknown quantum channels, extending the surprising sample-efficiency results of Huang, Chen, and Preskill to general product input distributions.

[arXiv](https://arxiv.org/abs/2409.03684) · [PDF](https://arxiv.org/pdf/2409.03684)

### Abstract

We investigate the problem of predicting the output behavior of unknown quantum channels. Given query access to an $n$-qubit channel $E$ and an observable $O$, we aim to learn the mapping \begin{equation*} ρ\mapsto \mathrm{Tr}(O E[ρ]) \end{equation*} to within a small error for most $ρ$ sampled from a distribution $D$. Previously, Huang, Chen, and Preskill proved a surprising result that even if $E$ is arbitrary, this task can be solved in time roughly $n^{O(\log(1/ε))}$, where $ε$ is the target prediction error. However, their guarantee applied only to input distributions $D$ invariant under all single-qubit Clifford gates, and their algorithm fails for important cases such as general product distributions over product states $ρ$. In this work, we propose a new approach that achieves accurate prediction over essentially any product distribution $D$, provided it is not "classical" in which case there is a trivial exponential lower bound. Our method employs a "biased Pauli analysis," analogous to classical biased Fourier analysis. Implementing this approach requires overcoming several challenges unique to the quantum setting, including the lack of a basis with appropriate orthogonality properties. The techniques we develop to address these issues may have broader applications in quantum information.
