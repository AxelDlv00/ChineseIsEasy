# 🐉 ChineseIsEasy — Tools to Learn Chinese Efficiently

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![GitHub Repo](https://img.shields.io/badge/Repo-ChineseIsEasy-brightgreen.svg)](https://github.com/AxelDlv00/ChineseIsEasy)

I’m a French learner of Mandarin, and I created **ChineseIsEasy** as a collection of small, practical tools to help me learn Chinese more efficiently. These tools were originally designed for personal use, but I’ve decided to make some of them open source to help others who share the same journey.

Each tool focuses on a different aspect of language learning — vocabulary building, conversation practice, or translation refinement.  
Most scripts are optimized for **French → Chinese** learning, but can easily be adapted to other language pairs by changing datasets or prompts, which is why I provide the source code. 

> ⚠️ I do not guarantee perfect accuracy of translations or code maintenance.  
> These tools are meant for experimentation and self-study.

## Repositories

### [RandomConversation](./RandomConversations/) — Practice "French → Chinese" Translation with Real Dialogues

`RandomConversation` is a lightweight Python script that displays **random French conversation snippets** from large dialogue datasets such as [OpenSubtitles](https://opus.nlpl.eu/OpenSubtitles-v2024.php).

It’s a fun way to **simulate real-life situations** and practice both translation and creativity. The idea is simple: use authentic French dialogues as raw material, then progressively turn them into vivid Chinese conversations.

#### How I Use It to Learn Chinese

1. **Generate** a natural French conversation on a random topic  
2. **Expand and refine** it with a Large Language Model (e.g. GPT-5) to make it more coherent or expressive. The prompt I use for my LLM-agent is in the file [LLMAgentForImprovingConversation.txt](./RandomConversations/LLMAgentForImprovingConversation.txt)
3. **Translate it yourself into Chinese** — focusing on fluency, idiomatic expressions, and tone  
4. **Ask the LLM to correct and comment** on your translation to get detailed feedback  

This process helps improve:
- Vocabulary recall and sentence fluidity  
- Grammar intuition through guided rewriting  
- Cultural and idiomatic awareness in both languages  

#### Example Workflow

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
*Dans un salon de famille un peu désordonné, la tension monte. Trois générations sont réunies pour une discussion qui a pris une tournure inatt
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


### [AnkiWords](./AnkiWords/) - Anki FlashCard by Word Frequency 

A complete pipeline to **automatically generate and export Chinese vocabulary decks for Anki**.
It uses open datasets like [**SUBTLEX-CH**](https://openlexicon.fr/datasets-info/SUBTLEX-CH/README-subtlex-ch.html) and **CCCEDICT**, enhanced by GPT-based generation for examples, explanations, and categories.

This tool was originally built to help me structure my Mandarin learning through **interactive flashcards** in French, but can easily be adapted for other languages or datasets.

**Main features:**

* Automatically creates a deck with **15 000 of the most frequent Chinese words**, you can download it directly as [`DictWords.apkg`](./AnkiWords/DictWords.apkg) without understanding the code.
* Includes **simplified/traditional forms**, **pinyin with tones**, **French explanations**, **example sentences**, and **stroke animations**

**Quick use (no coding required):**

1. Install [Anki](https://apps.ankiweb.net/)
2. Download the ready-made deck [`DictWords.apkg`](./AnkiWords/DictWords.apkg)
3. In Anki, go to **File → Import...**, select the file, and start learning 

<p align="center">
  <img src="./AnkiWords/assets/anki_categories.jpg" alt="Anki categories preview" width="280" style="margin-right:10px;"/>
  <img src="./AnkiWords/assets/anki_example.gif" alt="Anki card example" width="280"/>
</p>

<p align="center"><em>Left: deck organized by category — Right: sample card with stroke animation</em></p>

## License

Released under the [**MIT License**](./LICENSE).  
Free for educational, research, and personal use.

## Author

**Axel Delaval (陈安思)**