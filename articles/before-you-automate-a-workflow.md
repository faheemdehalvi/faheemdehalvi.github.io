---
title: Before you automate a workflow, write down four things
slug: before-you-automate-a-workflow
description: An illustrative invoice workflow explains how to define inputs, outputs, failure handling and checks before choosing an AI tool.
---

# Before you automate a workflow, write down four things

This article uses a made-up example. The business, the invoices and the numbers below are invented to show a way of thinking. None of it is a client case or a test I ran.

## The example

Picture a five-person plumbing supplies business. Supplier invoices arrive by email as PDFs, mostly, and sometimes as phone photos. Every Friday one person opens each invoice and types the supplier name, invoice date and total into a spreadsheet that the bookkeeper uses on Monday. It takes the afternoon. The owner reads about AI extraction tools and asks: can we just automate this?

Probably, in part. But it helps to define the workflow before choosing the tool. Before choosing one, write down four things.

## 1. Scope: what is in and what is out

Decide what the automation does and does not touch. For the example: it reads invoices from one shared inbox and fills three columns. It does not pay anything, does not email suppliers and does not edit anyone's existing rows.

Small scope is a feature. Every extra thing the automation can do is another place it can be wrong without anyone noticing.

## 2. Inputs: what actually arrives

List what shows up, not what should show up. In the example: PDFs with selectable text, scanned PDFs, phone photos, invoices with several pages, credit notes that look like invoices, and the occasional email with no attachment.

Pull a real batch from the past and sort it into those groups. The groups you find tell you what the tool has to cope with, and which ones you'd rather keep manual at first.

## 3. Outputs: exactly what "done" looks like

Write the columns, the formats and the rules. Date as day, month, year. Total including tax, as a number, with no currency symbol. Supplier name matching the name already in the spreadsheet, not whatever the PDF header says.

If you can't describe a correct row precisely, you can't check one either.

## 4. Failures: what happens when it's wrong or unsure

This section is easy to skip, and it's the one I'd spend the most time on. Take three failure types and decide what happens to each:

- **It can't read the file.** The invoice goes to a person, with the original attached, and the row is left blank.
- **It reads the file but isn't sure.** Same route. The tool marks the row as uncertain and a person confirms it.
- **It reads the file confidently and is wrong.** This needs checks beyond the model reporting its own confidence: a person spot-checks a few rows every week, or the totals are compared with the supplier statement at month end.

The third type is why review has to be designed, not hoped for. A mistyped total that reaches the bookkeeper looks exactly like a correct one.

## How you would measure it

Before you switch anything on, build a small answer key. Take a batch of past invoices where a person has already entered the right figures. Run the tool on them. For each column, count how many it got exactly right out of the batch.

For the example, say you take 30 invoices. The 30 is a number I picked for this article, not a rule, and you should pick a batch that includes your awkward cases, not only the clean ones. A score like "27 of 30 totals exactly right, and the 3 misses were all phone photos" tells you something useful. "Mostly works" tells you nothing.

Write down the date, the tool and its version, and the settings. Tools change, and a result from last month may not hold for this one. Keep the answer key so you can check for regressions after changes. Also reserve separate examples that you do not use to adjust the workflow; repeatedly tuning against the same examples can hide weaknesses.

Be honest about what the score means. One batch from one inbox is a starting point. It's not a benchmark and it says nothing about anyone else's invoices.

## What I would do in the first fortnight

1. Run the tool in parallel with the manual process. Nobody relies on its output yet.
2. Compare its rows with the person's rows every week and log each difference.
3. Sort the differences by type. If most are one type, such as phone photos, decide whether to fix it or keep that type manual.
4. Before relying on the first pass, set acceptance criteria for accuracy, review effort and missed exceptions. Keep human review of flagged items and sample apparently successful ones as well.

That order is slower than "turn it on". It gives you a chance to find errors before someone relies on the output.

## Where I would stop

If the invoices arrive in formats you can't sort into groups, or nobody has time to review, don't automate this workflow yet. Fix the process first. A tidy manual process is easier to automate than a messy one.

Pick one workflow you've been meaning to automate and fill in the four sections in plain sentences. Which one is hardest to write?
