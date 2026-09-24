# LinguaSpark

**LinguaSpark** is an AI-powered Anki deck builder for Python. Paste a plain
list of words and a language model does the rest: definitions, phonetics,
example sentences, translations, and memory mnemonics — packaged into a
standard `.apkg` file ready for Anki, AnkiMobile, or AnkiWeb.

![LinguaSpark workflow](docs/workflow.svg)

## Features

- **Zero-friction ingestion.** Paste words or load a `.txt` file, one term per
  line. No rigid formatting required.
- **Deep linguistic enrichment.** Each term gets a part of speech, target
  definition, IPA / native phonetics, a contextual example sentence with
  translation, and a vivid mnemonic.
- **Interactive review table.** Inspect and edit every card before exporting.
  Right-click a row to regenerate a single card or delete it.
- **Dual-engine flexibility.** Switch between hosted LLMs (OpenAI, Anthropic,
  Gemini) or run 100% offline with a local Ollama instance.
- **Native `.apkg` export.** Generates standard Anki packages with clean,
  modern card styling via `genanki`.

## Workflow

1. **Input** — type or paste a list of words into the input area.
2. **Configure** — set the deck name, the **input language** (for your
   words + the generated example sentences) and **output language** (for
   definitions, translations, and mnemonics on the back of each card),
   the AI provider, and the model.
3. **Enrich** — click **Process Vocabulary**. Cards stream into the table as
   they're generated; the UI stays responsive.
4. **Review** — tweak any field inline, right-click rows to regenerate or
   delete.
5. **Export** — click **Export to Anki** to write a `.apkg` file you can
   import directly into Anki.

## Installation

```bash
git clone https://github.com/andreipirone/Anki-Deck-Generator.git
cd Anki-Deck-Generator
pip install -r requirements.txt
```

**Runtime:** Python 3.9+ on Windows, macOS, or Linux.

## Usage

```bash
python main.py
```

On first launch:

1. Pick a provider from the dropdown. For cloud providers (OpenAI, Anthropic,
   Gemini), enter your API key and click **Save**. The key is stored locally
   in your OS user settings and auto-loaded on subsequent runs. Use **Forget**
   to remove it at any time.
2. For Ollama, make sure a local Ollama server is running
   (`ollama serve`) and that your desired model is pulled
   (`ollama pull llama3.1`). The default URL `http://localhost:11434` is
   pre-filled.
3. Paste your words, hit **Process Vocabulary**, review the table, then
   **Export to Anki**.

### Supported providers

LinguaSpark does **not** supply default model names per provider — you must
enter a model in the **Model** field before processing. This avoids silently
hitting an unexpected (and potentially costly) endpoint.

| Provider        | API key required | Example models                          |
|-----------------|------------------|------------------------------------------|
| OpenAI          | yes              | `gpt-4o-mini`, `gpt-4o`, `o1-mini`       |
| Anthropic       | yes              | `claude-3-5-sonnet-latest`, `claude-3-5-haiku-latest` |
| Gemini          | yes              | `gemini-1.5-flash`, `gemini-1.5-pro`     |
| Ollama (Local)  | no               | `llama3.1`, `mistral`, `qwen2.5:7b`      |
| Ollama Cloud    | yes              | `gemma3:cloud`, `gemma4:31b`             |

#### Ollama Cloud

For hosted Ollama models (no local install required):

1. Create an API key at <https://ollama.com/settings/keys>.
2. In LinguaSpark, select **Ollama Cloud** from the provider dropdown.
3. Paste your key, click **Save**.
4. Type any cloud model name into the **Model** field (browse the catalog at
   <https://ollama.com/search?c=cloud>). Requests go to
   `https://ollama.com/api/chat` with `Authorization: Bearer <key>`.

## Card template

Every card is generated from this 9-field schema:

| Field               | Purpose                                                       |
|---------------------|---------------------------------------------------------------|
| Term                | The vocabulary word.                                          |
| Translation         | Direct translation of the term into the **output language** (learner's language). The primary answer on the back. |
| POS                 | Part of speech (noun, transitive verb, …).                    |
| Phonetics           | IPA or native syllabary where applicable.                     |
| Definition          | Concise, learner-friendly definition (secondary).             |
| Example             | Native-level example sentence.                                |
| Example Translation | Output-language translation of the example sentence.          |
| Mnemonic            | High-retention visual or phonetic association.                |
| Language            | Input language label (the language of the term + example).     |

The card front shows the **term only**. The back reveals POS + language
badges, phonetics, **direct translation in the output language** (the
headline answer), and then — secondary — the definition, example +
translation, and a highlighted mnemonic callout. All back-of-card text
is written in the output language you select; the term + example
sentence are in the input language.

### Card themes

A **Deck Theme** dropdown lives in the action row, next to the Export
button. The two options bake different CSS into the resulting `.apkg`
— the layout and field set are identical, only the colors change.

- **Light** (default) — white background, dark text.
- **Dark** — navy background (`#0b1020`), light text. Matches the
  LinguaSpark GUI's dark mode.

Your choice is persisted in `QSettings` and restores on every launch.

### Multi-word entries

One vocabulary entry per line. Multi-word phrases such as
`to evaluate`, `to be`, or `at once` stay intact on the same line —
LinguaSpark splits only on newlines. Inline commas, semicolons, and pipes
still split within a line (e.g. `apple, banana; cherry` becomes three
entries).

## Project layout

```
Anki-Deck-Generator/
├── main.py                      # Entry point
├── requirements.txt
├── README.md
└── linguaspark/
    ├── config.py                # Constants, deck/model IDs, defaults
    ├── models/card.py           # Pydantic VocabCard + BatchResponse
    ├── llm/                     # OpenAI / Anthropic / Gemini / Ollama providers
    ├── anki/                    # genanki builder + HTML/CSS templates
    ├── workers/enrich_worker.py # QThread background enrichment
    ├── ui/                      # InputPanel, ReviewTable, MainWindow
    └── utils/parsers.py         # Word-list parsing + chunking
```

## Troubleshooting

- **"Model required"** — the Model field is empty. Enter the exact model
  name your provider expects (e.g. `gpt-4o-mini`, `gemma3:cloud`,
  `llama3.1`). LinguaSpark never auto-fills defaults.
- **"API key required"** — save a key for the selected provider. OpenAI,
  Anthropic, Gemini, and Ollama Cloud all require one; local Ollama does not.
- **Ollama (local) fails immediately** — confirm `ollama serve` is running and
  that your model is pulled (`ollama list`).
- **Ollama Cloud returns 401** — your key is invalid or expired; generate a
  new one at <https://ollama.com/settings/keys>.
- **JSON parse error from the LLM** — LinguaSpark retries once with a
  corrective message. If a word still fails it shows up as a row with a
  red error message; right-click → regenerate to retry.
- **Export produces an empty deck** — your review table is empty; process
  some words first.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

- Built with [PySide6](https://wiki.qt.io/Qt_for_Python) (Qt for Python).
- Uses [genanki](https://github.com/kerrickstaley/genanki) for `.apkg` output.
- Anki is a trademark of Ankitects Pty Ltd.
