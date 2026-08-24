# Legal Tech Class

The aim of this project is to create a collaboratively built textbook for teaching law school classes about legal technology.

[Quinten Steenhuis](https://nonprofittechy.com) is the author and editor of almost all of the content as of 2020, so the material
reflects his interests and biases. However, he hopes to encourage collaboration from many sources, and the material will
start to become a centralized library reflecting many overlapping goals. Several people have contributed thoughts and ideas
on [this Trello board](https://trello.com/b/Fz9PIm2g/project-materials).

All content is released under a Creative Commons [Non-commercial Attribution/Share-alike license](https://creativecommons.org/licenses/by-nc-sa/2.0/).

The website itself is a series of Markdown files presented via [Docusaurus](https://v2.docusaurus.io/).

It now includes:

* Practical exercises and assignments for teaching the [Docassemble](https://docassemble.org) platform
* Practical guides to building document assembly and expert systems using Docassemble
* Reading lists for different legal technology topics
* Information and essays about the access to justice problem
* Essays and synopses on other software development and broad legal tech topics, such as the future of the legal profession
* Hierarchies and taxonomies of legal technology
* Syllabi that can help professors create their own legal tech classes

The goal is to also cover related systems, including:

* QnA Markup
* A2J Author
* Hotdocs

## Architecture note

The operating posture for the DPO workflow is to achieve institutional-grade controls and auditability through a lean operating layer rather than by adopting a heavy CRM too early. The current workflow engine provides deterministic queue writes, metadata propagation, replayable history, and ledger-backed observability. That foundation supports content-driven outreach, Docassemble-based list and document generation, and provider-ready outbound execution while preserving the control plane needed for later institutional systems such as Apache/Fineract-style customer and account management.
