---
title: "Query lower bounds for log-concave sampling"
date: 2023-04-05
params:
  authors: "Sinho Chewi, Jaume de Dios Pont, Jerry Li, Chen Lu, Shyam Narayanan"
  journal: "Journal of the ACM, Vol. 71, Issue 4. FOCS 2023"
  arxiv: "https://arxiv.org/abs/2304.02599"
  pdf: "https://arxiv.org/pdf/2304.02599"
  description: "We establish the first unconditional lower bounds on the query complexity of sampling from log-concave distributions, proving that existing algorithms are near-optimal in low dimensions."
---

**Sinho Chewi, Jaume de Dios Pont, Jerry Li, Chen Lu, Shyam Narayanan**

*Journal of the ACM, Vol. 71, Issue 4. FOCS 2023*

We establish the first unconditional lower bounds on the query complexity of sampling from log-concave distributions, proving that existing algorithms are near-optimal in low dimensions.

[arXiv](https://arxiv.org/abs/2304.02599) · [PDF](https://arxiv.org/pdf/2304.02599)

### Abstract

Log-concave sampling has witnessed remarkable algorithmic advances in recent years, but the corresponding problem of proving lower bounds for this task has remained elusive, with lower bounds previously known only in dimension one. In this work, we establish the following query lower bounds: (1) sampling from strongly log-concave and log-smooth distributions in dimension $d\ge 2$ requires $Ω(\log κ)$ queries, which is sharp in any constant dimension, and (2) sampling from Gaussians in dimension $d$ (hence also from general log-concave and log-smooth distributions in dimension $d$) requires $\widetilde Ω(\min(\sqrtκ\log d, d))$ queries, which is nearly sharp for the class of Gaussians. Here $κ$ denotes the condition number of the target distribution. Our proofs rely upon (1) a multiscale construction inspired by work on the Kakeya conjecture in geometric measure theory, and (2) a novel reduction that demonstrates that block Krylov algorithms are optimal for this problem, as well as connections to lower bound techniques based on Wishart matrices developed in the matrix-vector query literature.
