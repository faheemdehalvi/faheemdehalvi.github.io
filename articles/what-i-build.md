---
title: What I build and why I'm writing about it
slug: what-i-build
published: 2026-11-11
description: Forward Deployed GTM Engineer Faheem Dehalvi introduces his projects and practical writing on AI workflows, context and integrations.
---

# What I build and why I'm writing about it

I want AI advice that leaves me knowing what to do next. Which part of a task could I automate? What would I need to check? When is the simpler setup enough?

Those are the questions I want this site to answer.

I'm Faheem Dehalvi, a Forward Deployed GTM Engineer based in Melbourne. I work part-time at [Intelligent Resourcing](https://intelligentresourcing.co/about-us), building automations and agents, while completing a Master of Data Science at RMIT. I expect to graduate in June 2027.

Outside work, I work on tools for connecting AI assistants, organising context and getting useful work done across applications. This site is where I'll explain those projects and the decisions behind them.

## Three projects you can inspect

The first is [FD CODE](https://github.com/faheemdehalvi/fd-code), a customised version of [T3 Code](https://github.com/pingdotgg/t3code). It brings together coding agents with additions around local context, provider handoffs and creative tools.

The underlying application comes from T3 Code's authors. The work in this fork builds on that foundation. What interests me is continuity: how an assistant finds the relevant decisions, what happens when a session changes, and how the person using it stays in control. Those questions give me useful things to investigate and write about.

The second is [ARTsie](https://github.com/faheemdehalvi/artsie), a local Mac workspace and integration layer around [ArtCraft's creative applications](https://getartcraft.com/apps). It includes a hub, shared workspace, command-line access and a gateway for AI assistants to use the applications' tools.

The creative editors are ArtCraft's work. ARTsie connects them into a workflow. That distinction matters because building a useful integration involves different decisions from building a photo editor or a video engine. I want to show the contribution clearly enough that another builder can understand it.

The third is a [local document question-answering skill](https://github.com/faheemdehalvi/rag-skill) for Claude Code. It uses [RAG-Anything](https://github.com/HKUDS/RAG-Anything), LightRAG and MinerU. Its configuration supports local models through Ollama.

The retrieval and parsing systems come from those upstream projects. The skill provides a way to set them up and use them in a working environment. It raises practical questions I want to explore: which documents are worth indexing, how to check an answer against its source, and whether a retrieval system is needed for a particular task at all.

Each repository has its own setup instructions and limitations. Start with those before installing anything. A project description explains the intended behaviour; a useful evaluation needs a defined task and observed results.

## What I want to make useful

A tool name is only part of a decision. The rest includes the information it needs, the output someone will rely on, the cost of an error and the work of maintaining it.

Take an invoice workflow. Extracting a total is one step. Deciding what happens to a duplicate invoice, an unreadable scan or an incorrect total is part of the same design. I'll use examples like that to explain the decisions in ordinary language.

When I publish an experiment, I'll describe the task, inputs, versions and result. When I publish a design proposal, I'll explain the assumptions. You should be able to tell which kind of article you are reading.

## What you'll find here

I'll write practical guides for choosing a setup, walkthroughs of things I build, and reality checks on specific AI claims. Some pieces will be useful to engineers. Others will help someone who simply wants to understand which part of their work could become easier.

I also want to teach people how to use their tools with more confidence. For now, I'm starting with clear explanations and work people can inspect. The questions readers bring will help shape what comes next.

If you have an AI decision you're stuck on, you can find me on [LinkedIn](https://www.linkedin.com/in/faheem-dehalvi/). Describe the task you are trying to complete and the part that is confusing. That's a much better starting point than a shopping list of tools.
