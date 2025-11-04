# 🐉 ChineseIsEasy – RandomConversation

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](./../LICENSE)
[![GitHub Repo](https://img.shields.io/badge/Repo-ChineseIsEasy-brightgreen.svg)](https://github.com/AxelDlv00/ChineseIsEasy)

I’m a French learner of Mandarin. To make my learning more efficient, I built several small tools — gathered under the project **ChineseIsEasy**.  
This repository is one of them: a simple yet powerful script to generate **random conversations** for translation and language practice.

## Table of Contents

- [🐉 ChineseIsEasy – RandomConversation](#-chineseiseasy--randomconversation)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Required Setup](#required-setup)
    - [Python Environment](#python-environment)
    - [Data Preparation (Required !)](#data-preparation-required-)
  - [Usage](#usage)
    - [How I Use It to Learn Chinese](#how-i-use-it-to-learn-chinese)
    - [Example Workflow](#example-workflow)
  - [License](#license)
  - [Author](#author)

## Overview

`RandomConversation` is a lightweight Python tool that displays **random dialogues**  
(*$N$ consecutive lines*) from large text corpora such as [OpenSubtitles](https://opus.nlpl.eu/OpenSubtitles-v2024.php).

It’s useful for:
- Language learners who want to practice translation or comprehension  
- NLP researchers exploring dialogue datasets  
- Anyone studying conversational patterns in natural text  

## Required Setup

### Python Environment

I use a conda environment for managing dependencies, here you only need `os`, `random`, and `argparse` which are included in the Python standard library.

For instance : 

```bash
conda create -n random_conversations python=3.10 -y
conda activate random_conversations # You need this to use the command `python` afterwards
```

### Data Preparation (Required !)

```bash
mkdir -p data
cd data

# Download the French subtitles dataset (e.g. from OpenSubtitles)
wget https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2024/mono/fr.txt.gz

# Decompress it
gunzip fr.txt.gz

# Optionally keep only the first 2 million lines (faster to handle)
head -n 2000000 fr.txt > fr_subset.txt
mv fr_subset.txt fr.txt
```

## Usage

Display a random snippet (5 lines by default):

```bash
python RandomConversation.py
```

Or specify your own file and snippet length:

```bash
python RandomConversation.py --file data/fr.txt --n 10
```

### How I Use It to Learn Chinese

1. **Generate** a natural French conversation on a random topic  
2. **Expand and refine** it with a Large Language Model (e.g. GPT-5) to make it more coherent or expressive. The prompt I use for my LLM-agent is in the file [LLMAgentForImprovingConversation.txt](./LLMAgentForImprovingConversation.txt)
3. **Translate it yourself into Chinese** — focusing on fluency, idiomatic expressions, and tone  
4. **Ask the LLM to correct and comment** on your translation to get detailed feedback  

This process helps improve:
- Vocabulary recall and sentence fluidity  
- Grammar intuition through guided rewriting  
- Cultural and idiomatic awareness in both languages  

### Example Workflow

**1. Generate a random snippet**

```bash
$ python RandomConversation.py -n 7

--- Random snippet starting at line 1,840,809 ---

Papa, en vérité c'est lui, le père.
Attendez !
Je ne suis pas le père.
Je me fiche de savoir qui est le père.
Je suis le grand-père.
Ce n'est pas vous ?
Non.

--- End of snippet ---
````

**2. Expand it into a natural French dialogue**

```
*Dans un salon de famille un peu désordonné, la tension monte. Trois générations sont réunies pour une discussion qui a pris une tournure inattendue.*

**Fils :** (d’une voix tremblante) Papa… en vérité, c’est lui… le père.  
**Père :** (abasourdi) Attends une seconde ! Quoi ?! Je ne suis pas le père !  
**Mère :** (exaspérée, levant les yeux au ciel) Franchement, à ce stade, je me fiche bien de savoir qui est le père…  
**Grand-père :** (fièrement, se redressant dans son fauteuil) Eh bien, moi je peux vous le dire : je suis le grand-père.  
**Père :** (se tourne vers lui, interloqué) Ce n’est pas vous ?  
**Grand-père :** (souriant malicieusement) Non, pas cette fois.
```

**3. Translate it into Chinese**

```
在一个有点乱的客厅里，气氛紧张。三代人齐聚一堂，一场原本普通的谈话似乎变得越来越离谱。  
儿子：(声音有点颤抖) 爸爸，其实，是他——他才是爸爸。  
父亲：(震惊地) 等一下！什么？！我才不是爸爸！  
母亲：(无奈地，翻着白眼) 说真的，到这个时候，我已经不在乎谁是爸爸了……  
爷爷：(得意地，从沙发上挺直腰) 哼，我可以告诉你们：我是爷爷。  
父亲：(疑惑地) 不是你吗？  
爷爷：(坏笑着) 不，这次不是我。
```

**4. Ask a LLM to correct and comment**

> It can explain grammatical issues, propose smoother alternatives,
> and point out differences in tone, register, or word choice — just like a native teacher.

## License

Released under the **MIT License**. Free for educational, research, and personal use.

## Author

**Axel Delaval (陈安思)**