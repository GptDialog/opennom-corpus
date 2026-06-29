# OpenNom Corpus — открытый параллельный корпус бурятского языка

**bur → rus → eng**, собираемый вживую носителями бурятского языка.

Бурятский внесён в [Атлас языков мира под угрозой исчезновения ЮНЕСКО](https://unesdoc.unesco.org/ark:/48223/pf0000187026) (Moseley, UNESCO Publishing, 2010) как **severely endangered**. Решающий критерий угрозы по ЮНЕСКО — не число носителей, а передача языка между поколениями. Бурятского почти нет в цифре: нет машинного перевода, нет обучающего корпуса. Этот репозиторий — попытка закрыть дыру: открытый нативный корпус как фундамент.

Проект вписывается в [Международное десятилетие языков коренных народов ООН 2022–2032](https://undocs.org/A/RES/74/135) (резолюция A/RES/74/135; ведущее агентство — ЮНЕСКО).

## Принцип №1: бурятское содержимое — только от носителей

**Бурятское поле (`bur`) заполняет только носитель языка.** ИИ-генерация бурятского в корпус запрещена — это защищённый актив, ради него весь проект. ИИ используется только для русского/английского каркаса и обвязки. Валидатор грубо ловит контаминацию латиницей; смысловую выверку делает носитель (поле `verified_by`, `status=verified`).

## Структура

```
opennom-corpus/
├── corpus/
│   ├── text/family.csv        # пример темы «семья» (строки-плейсхолдеры)
│   ├── text/_TEMPLATE.csv     # пустой шаблон для переводчиков (по примеру на каждый type)
│   ├── audio/manifest.csv     # audio_id, file, speaker, dialect, theme, source, consent
│   ├── audio/files/           # аудиофайлы носителей
│   └── schema.md              # описание всех полей и enum-значений
├── scripts/validate.py        # валидатор схемы
├── scripts/counts.py          # счётчик прогресса -> counts.json
├── counts.json                # публичный счётчик (читает питч-сайт)
├── README.md
└── LICENSE                    # CC BY 4.0
```

Схема полей и enum-значений — в [`corpus/schema.md`](corpus/schema.md). Кодировка везде строго **UTF-8** (буквы Һ Ү Ө Э нельзя терять).

## Лицензия

[CC BY 4.0](LICENSE). Используя корпус, указывай авторство:
«OpenNom Buryat Parallel Corpus, CC BY 4.0, contributors».

## Как контрибьютить

1. Возьми [`corpus/text/_TEMPLATE.csv`](corpus/text/_TEMPLATE.csv) (или импортируй в Google Sheets).
2. Заполняй построчно. Обязательные поля: `id`, `bur`, `rus`, `type`, `theme`.
   - `bur` заполняет носитель. Строго кириллица + Һ Ү Ө.
   - `type` ∈ `word, phrase, sentence, idiom, proverb, yorol, text`.
   - `register` ∈ `neutral, colloquial, formal, ritual, archaic`.
   - `status` ∈ `draft, translated, verified, published`.
   - для `idiom`/`proverb`/`yorol` заполняй `literal_rus` (буквальный разбор).
3. Выверенную носителем строку переводи в `status=verified` и заполняй `verified_by`.
4. Аудио: положи файл в `corpus/audio/files/`, добавь строку в `corpus/audio/manifest.csv`, проставь `audio_id` в текстовой строке.
5. Прогони валидатор и пересчитай счётчик (см. ниже). Открой PR.

Только строки со `status=verified` попадают в публичные продукты (питч-сайт, релизы датасета).

## Валидация и счётчик

```bash
pip install pandas
python scripts/validate.py    # проверка схемы; ненулевой код выхода при ошибках
python scripts/counts.py      # пересчитать counts.json
```

Валидатор проверяет: обязательные поля непусты; `id` уникальны во всём корпусе; `type`/`register`/`status` в enum; `bur` непусто и не латиница; каждый непустой `audio_id` есть в `manifest.csv` и файл лежит в `audio/files/`.

CI (GitHub Actions) гоняет `validate.py` на каждый push и pull request и падает, если `counts.json` устарел.

## Загрузка данных

CSV грузятся без преобразований:

```python
import pandas as pd
df = pd.read_csv("corpus/text/family.csv", encoding="utf-8")

# HuggingFace datasets
from datasets import load_dataset
ds = load_dataset("csv", data_files="corpus/text/family.csv")
```
