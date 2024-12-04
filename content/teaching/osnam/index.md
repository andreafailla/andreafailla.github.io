---
title: Online Social Network Analysis and Mining
summary: OSNAM module of the ML course at UCBL, Lyon, France
date: 2024-10-24
type: docs
math: false
tags:
  - OSNAM
image:
  caption: 
---

This is the page for the Online Social Network Analysis and Mining (OSNAM) module of the Machine Learning course at UCBL, Lyon, France.

### Course Description
This module will cover the following Network Science topics, with a specific focus on applications related to social media.
- Link Prediction
- Community Detection
- Dynamics of Networks
- Dynamics on Networks


### Lecture 1: Link Prediction

Synopsis: This lecture will introduce the problem of link prediction in social networks, and will cover some of the most popular methods to solve it.
Then, we will move to performance evaluation and discuss some key challenges in this task.


Slides: [here](../../../uploads/slides/OSNAM-1.pdf) (adapted from Prof. [Giulio Rossetti](https://giuliorossetti.github.io/)'s material)

Introductory Networkx Notebook: [here](../../../uploads/notebooks/networkx.ipynb)

Practicals: [here](../../../uploads/TP_OSNAM1_LinkPred.pdf)
(some) Practicals solutions: [here](../../../uploads/notebooks/linkpred.ipynb)

Suggested Readings (freely available):
- Liben‐Nowell, David, and Jon Kleinberg. "The link‐prediction problem for social networks." Journal of the American society for information science and technology 58.7 (2007): 1019-1031.
- Coscia, Michele, "The Atlas of the Aspiring Network Scientist" (2019), ch. 20 and 22.


### Lecture 2: Community Detection

Synopsis: This lecture introduces community detection in networks, focusing on identifying meso-scale structures using various algorithms. It discusses the challenges of defining and evaluating communities due to the ill-posed nature of the problem, highlighting approaches like modularity-based methods, bridge detection, and feature-based clustering. The lecture emphasizes the importance of community discovery for understanding functional modules in complex systems and concludes with tools and benchmarks for evaluation, referencing key readings and a Python library for practical application.


Slides: [here](../../../uploads/slides/OSNAM-2.pdf) (adapted from Prof. [Giulio Rossetti](https://giuliorossetti.github.io/)'s material)

Practicals: [here](../../../uploads/TP_OSNAM2_CD.pdf)

Practicals solutions: [here](../../../uploads/notebooks/osnam_cd.ipynb)


Suggested Readings (freely available):
- Fortunato, Santo. "Community detection in graphs." Physics reports 486.3-5 (2010): 75-174.
- Coscia, Michele, "The Atlas of the Aspiring Network Scientist" (2019), ch. 31, 32, 33, and 34.


### Lecture 3: Dynamics of Networks

Synopsis: In this lecture, we will see why it's important to take into account the temporal dimension when working with network data. We will discuss the difference between relations and interactions, and see how we can model dynamic topologies. Finally, we will build on top of the previous lecture to study communities as they evolve through time.


Slides: [here](../../../uploads/slides/OSNAM-3.pdf) 

Practicals: [here](../../../uploads/TP_OSNAM3_DCD.pdf)


Suggested Readings (freely available):
- Holme, Petter, and Jari Saramäki. "Temporal networks." Physics reports 519.3 (2012): 97-125.
- Rossetti, Giulio, and Rémy Cazabet. "Community discovery in dynamic networks: a survey." ACM computing surveys (CSUR) 51.2 (2018): 1-37.

### Lecture 4: Dynamics on Networks

Synopsis: In this lecture we will go over some ways of studying moving "objects" in a network, e.g., diseases, opinions, innovations, etc.


Slides: [here](../../../uploads/slides/OSNAM-4.pdf) 

Practicals: [here](../../../uploads/notebooks/osnam_dm_practical.ipynb)

If you want to play and generate GIFs of diffusion processes on networks,you can use this tool I made [here](https://diff2gif.streamlit.app/#diff2gif).

Suggested Readings (freely available):
- Coscia, Michele, "The Atlas of the Aspiring Network Scientist" (2019), ch. 17
- Sîrbu, Alina, et al. "Opinion dynamics: models, extensions and external effects." Participatory sensing, opinions and collective awareness (2017): 363-401.


#### Feedback
I am looking for ways to improve my teaching skills, and I welcome any feedback from the students. 
I'd really appreciate if you could answer two short questions anonymously [here](https://forms.gle/eyywUUHtaKvm1beS9) (should take less than 5 minutes).