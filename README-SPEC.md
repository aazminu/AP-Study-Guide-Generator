[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/qAf3sQhg)
# Final Project - Exploring LLM Capabilities

## Learning Objectives 
1.	Learn prompt engineering
2.	Learn how to use prompt templates to automate LLM prompting
3.	Explore the capabilities and limits of LLMs
4.	Learn the design and implementation of metrics for empirical analysis


## Project 

In this project, you will team up with 2 other Artificial Intelligence students to form a group that will explore the limits of LLM. You will be provided with a GPT API end point which you will access via REST requests. You and your colleagues will collaborate in the same GIT repository, be sure to commit often so course staff can monitor your progress. Git commits will also be used as proof of collaboration, this is a group project so one student doing all the work is highly discouraged. 

Once you have a team, you will brainstorm on an idea that involves generating structured or unstructured text using an LLM. You are free to choose the discipline, it can be science, poetry, literature, language etc. Write a draft of the idea, providing details on the problem, the dataset that you will use and how you will evaluate the performance of the LLM. Submit a draft on gradescope, a course staff will be assigned to mentor your project.

There are many datasets available online, a good place to start your search is the huggingface dataset repository. You are also free to generate your own dataset. Large datasets require more compute, we recommend capping at 1000 entries. You will need to ensure that the subset of the dataset is balanced. 

Now that you have a balanced dataset, your team needs to come up with different ways to prompt a LLM using your dataset as input. Once you have a list of prompts, you will need to abstract the prompts such that you can iterate through your dataset using your code. We will refer to these prompt abstractions as Prompt Templates. You can review online prompt template repositories to get a good idea. It can be difficult to parse LLM response because of non-standard response, it is a good idea to manually prompt the LLM first to get a sense of what logic is needed to parse your LLM responses.

What makes a good, average or bad response? Your team will design an evaluation protocol to measure the performance of the LLM. Depending on your problem, a simple exact match may suffice, other cases may need relaxed or heuristic approaches. Some use cases may best be evaluated by humans, do consider that there is only 3 of you and probably 1000 data points. The evaluation protocol and your experiment results are the main output of this project. This is a paradigm shift from software-based outputs common for most courses you have taken so far. To be clear, you are not making a website or an application that uses an LLM, you are designing and implementing evaluation experiments to measure the performance of LLMs. Your mentors will be there to help with the design choices, but you will need to document what you considered and the justification for the evaluation protocol in your final report. Good luck, we can’t wait to read all the ideas that you will come up with.

## Important Dates 
| Date  | Milestone | Grade  |
| --------- | --------- | --------- |
| 03/03 | Group project details released. | -|
| 03/07 | Choose group members on git classroom. | -|
| 03/14 | Submit first draft of project idea. Note: Draft should be PDF, max 300 words. | 5% |
| 03/24 | Group mentor assigned. | - |
| 03/28 | Mentor provides project proposal feedback. | - |
| 04/04 | Mentor Checkpoint: (1)	Address mentor feedback on proposal (2)	Data cleaning and preprocessing (3)	Exploratory Data Analysis | 10% |
| 04/25 | Mentor Checkpoint: (1)	Sample generations from dataset (2)	Evaluation protocol | 10%|
| 05/07 | Submit code repository and report for final project. Report should be PDF, max 900 words.| 75%|

## Examples
* Generating SQL code from python panda code
* Generating sentences that rhyme but limited to a specific topic
* Generating a score for CVs given a job description
* Generating a summary of a 383 lecture

## Resources
API: https://platform.openai.com/docs/guides/text-generation

Huggingface Datasets: https://huggingface.co/datasets

Kaggle: https://www.kaggle.com/datasets

UCI Data Reposistory: https://archive.ics.uci.edu/datasets
