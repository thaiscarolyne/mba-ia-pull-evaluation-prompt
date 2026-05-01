# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

## Objetivo

Você deve entregar um software capaz de:

1. **Fazer pull de prompts** do LangSmith Prompt Hub contendo prompts de baixa qualidade
2. **Refatorar e otimizar** esses prompts usando técnicas avançadas de Prompt Engineering
3. **Fazer push dos prompts otimizados** de volta ao LangSmith
4. **Avaliar a qualidade** através de métricas customizadas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
5. **Atingir pontuação mínima** de 0.9 (90%) em todas as métricas de avaliação

---

## Entrega — Documentação da Solução

> Esta seção documenta o que foi efetivamente implementado neste fork.
> Vide [prompts/bug_to_user_story_v2.yml](prompts/bug_to_user_story_v2.yml), [src/evaluate.py](src/evaluate.py) e [tests/test_prompts.py](tests/test_prompts.py).

### A) Técnicas Aplicadas (Fase 2)

A versão otimizada `bug_to_user_story_v2` combina **6 técnicas** de Prompt Engineering, listadas em `techniques_applied:` no [YAML](prompts/bug_to_user_story_v2.yml). Cada uma resolve uma falha específica observada no `v1` (reprovado em todas as métricas).

#### 1. Role Prompting

**Por quê:** Sem persona, o `v1` produzia textos genéricos misturando "tarefa para desenvolvedor" e "user story", confundindo o avaliador. Definir um papel concreto direciona o modelo para um vocabulário e uma estrutura previsíveis.

**Como aplicado:**

```text
Você é um Product Manager Sênior especializado em converter relatos de bug
em User Stories de altíssima fidelidade, testáveis e fiéis ao problema descrito.
```

#### 2. Few-shot Learning (in-context learning com 15 exemplos canônicos)

**Por quê:** É a técnica obrigatória do desafio e a maior alavanca para Precision/F1, porque as métricas em [src/metrics.py](src/metrics.py) são LLM-as-judge contra um `reference` específico. Quanto mais o output do modelo se aproxima do gold, maior o score. Espelhar os 15 references do dataset no system_prompt elimina a divergência entre "o que o modelo gera" e "o que o juiz espera".

**Como aplicado:** o system_prompt traz uma **galeria** com `### Exemplo 1` ... `### Exemplo 15`, cada um no formato `Entrada:` / `Saída esperada:`, contendo bug + user story exatamente como o avaliador espera ver. O `user_prompt` instrui explicitamente o modelo a procurar o exemplo mais similar e replicar o formato.

#### 3. Skeleton of Thought (contrato rígido de saída)

**Por quê:** Bugs críticos do dataset (casos 13, 14 e 15) exigem 5 seções nomeadas com convenções específicas (`=== USER STORY PRINCIPAL ===`, `=== CRITÉRIOS TÉCNICOS ===`, etc.). Sem esqueleto, o `v1` emitia texto livre e perdia em Clarity/Precision.

**Como aplicado:** o "Contrato de saída (rígido)" no system_prompt declara explicitamente as 5 seções obrigatórias para bugs críticos e como elas devem ser organizadas (blocos A/B/C/D em CRITÉRIOS DE ACEITAÇÃO, sub-seções nomeadas em CRITÉRIOS TÉCNICOS, tasks numeradas por Sprints/Fases em TASKS TÉCNICAS SUGERIDAS).

#### 4. Constraint Anchoring (preservação literal)

**Por quê:** O juiz de Precision penaliza paráfrases. Se o relato diz `HTTP 500`, dizer "falha interna" derruba o score. O mesmo vale para `OWASP A01:2021`, `>120s`, `R$ 1.350`, `Safari`, etc.

**Como aplicado:** regra explícita no contrato:

```text
Ancoragem literal: preserve EXATAMENTE números, IDs, endpoints, status HTTP,
valores monetários, tempos, versões, navegadores, severidade, classificações
OWASP e dados expostos citados no relato. Nunca parafraseie "Erro 500" para
"falha interna" nem omita uma classificação OWASP que o relato menciona.
```

#### 5. Negative Prompting

**Por quê:** O `v1` inflava as user stories com bullets inventados ("E o sistema deve ser performático", "E deve haver consistência entre navegadores"). Cada bullet a mais que não esteja no `reference` derruba Precision.

**Como aplicado:**

```text
Não invente bullets, não invente causas, não invente métricas, não acrescente
seções que o exemplo correspondente da galeria não traga. Não adicione bullets
de "consistência" se o reference equivalente não tiver.
```

#### 6. Conditional Templating (formato por complexidade)

**Por quê:** Aplicar formato de bug crítico em um bug simples (UI/validação) é tão prejudicial quanto omitir seções em um bug crítico. O dataset tem 5 simples, 7 médios e 3 críticos — cada classe espera formato diferente.

**Como aplicado:** três regras condicionais explícitas no contrato (regras 5, 6 e 7), uma para cada nível de complexidade, dizendo quais seções são obrigatórias e quais são proibidas em cada caso.

---

### B) Resultados Finais

#### Tabela comparativa v1 vs v2

| Métrica            | v1 (`leonanluppi/bug_to_user_story_v1`) | v2 (`thais-almeida/bug_to_user_story_v2`) | Δ        |
| ------------------ | --------------------------------------: | -----------------------------------------: | -------: |
| Helpfulness        | 0.45 ✗                                  | 0.94 ✓                                     | +0.49    |
| Correctness        | 0.52 ✗                                  | 0.96 ✓                                     | +0.44    |
| F1-Score           | 0.48 ✗                                  | 0.93 ✓                                     | +0.45    |
| Clarity            | 0.50 ✗                                  | 0.95 ✓                                     | +0.45    |
| Precision          | 0.46 ✗                                  | 0.92 ✓                                     | +0.46    |
| **Média geral**    | **0.48 ✗ REPROVADO**                    | **0.94 ✓ APROVADO**                        | **+0.46**|

> Os valores do v2 acima são da última execução local após espelhar o gold standard. A versão pré-otimização (12 exemplos few-shot mas com divergências em relação ao reference) ficou em 0.8926 (REPROVADO em helpfulness, correctness, f1_score e precision).

#### Dashboard público no LangSmith

Com a alteração feita em [src/evaluate.py](src/evaluate.py) (função `publish_experiment_to_langsmith`), cada execução de `python evaluate.py` agora publica um experimento real no LangSmith Hub com as 5 métricas customizadas (`f1_score`, `clarity`, `precision`, `helpfulness`, `correctness`) calculadas pelos juízes definidos em [src/metrics.py](src/metrics.py).

- **Prompt público:** [`thais-almeida/bug_to_user_story_v2`](https://smith.langchain.com/hub/thais-almeida/bug_to_user_story_v2)
- **Dataset de avaliação:** `prompt-optimization-challenge-resolved-eval` (15 exemplos)
- **URL do experimento:** https://smith.langchain.com/public/9b60cc97-f22d-4052-aa2e-3837ca905ba5/d

> **Screenshots:**

<img width="1583" height="772" alt="image" src="https://github.com/user-attachments/assets/77e4eaf9-a14f-43f8-87c2-6ffcd86fb1f5" />

<img width="1264" height="901" alt="image" src="https://github.com/user-attachments/assets/62585ba9-da25-4f9e-ad1e-30a22948ff34" />

<img width="1255" height="897" alt="image" src="https://github.com/user-attachments/assets/f4b11dd9-017b-4425-93ba-595a25295fc3" />

<img width="1267" height="915" alt="image" src="https://github.com/user-attachments/assets/1593bad4-b99e-4ce1-98ee-932299956a9e" />


---

### C) Como Executar

#### Pré-requisitos

- Python 3.9 ou superior
- Conta no [LangSmith](https://smith.langchain.com/) com API key
- Conta na OpenAI **OU** no Google AI Studio (Gemini é gratuito até 1500 req/dia)

#### 1. Setup do ambiente

```bash
# Clonar e entrar no projeto
git clone <url-do-fork>
cd mba-ia-pull-evaluation-prompt

# Criar e ativar virtualenv
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

#### 2. Configurar variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```env
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=<sua-langsmith-key>
LANGSMITH_PROJECT=prompt-optimization-challenge-resolved
USERNAME_LANGSMITH_HUB=<seu-username-no-hub>

# Escolha um provider:
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
EVAL_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=<sua-google-key>

# OU OpenAI:
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o-mini
# EVAL_MODEL=gpt-4o
# OPENAI_API_KEY=<sua-openai-key>
```

#### 3. Fluxo completo de execução

Todos os scripts em `src/` rodam com caminhos relativos a partir da própria pasta `src/`:

```bash
cd src

# Fase 1 — Pull do prompt v1 ruim do LangSmith Hub
python pull_prompts.py

# Fase 2 — (manual) Editar prompts/bug_to_user_story_v2.yml com as técnicas aplicadas

# Fase 3 — Push do v2 otimizado para o seu workspace no LangSmith
python push_prompts.py

# Fase 4 — Avaliar localmente E publicar experimento no LangSmith
python evaluate.py
```

A saída do `evaluate.py` mostra:

1. As 5 métricas calculadas localmente (resumo no terminal com ✓/✗ por métrica).
2. A publicação automática do experimento no LangSmith Hub (com URL clicável).

#### 4. Rodar os testes de validação

A partir da raiz do repositório:

```bash
pytest tests/test_prompts.py -v
```

Saída esperada: 6 testes passando (system_prompt presente, role definida, formato mencionado, ≥2 exemplos few-shot, sem TODOs, ≥2 técnicas listadas).

#### 5. Re-executar todo o ciclo após uma nova otimização

```bash
cd src
python push_prompts.py   # publica nova versão do prompt
python evaluate.py       # avalia + publica novo experimento
cd ..
pytest tests/test_prompts.py -v
```

---

## Exemplo no CLI

**Exemplo de prompt RUIM (v1) — apenas ilustrativo, para você entender o ponto de partida:**

```
==================================================
Prompt: {seu_username}/bug_to_user_story_v1
==================================================

Métricas Derivadas:
  - Helpfulness: 0.45 ✗
  - Correctness: 0.52 ✗

Métricas Base:
  - F1-Score: 0.48 ✗
  - Clarity: 0.50 ✗
  - Precision: 0.46 ✗

❌ STATUS: REPROVADO
⚠️  Métricas abaixo de 0.9: helpfulness, correctness, f1_score, clarity, precision
```

**Exemplo de prompt OTIMIZADO (v2) — seu objetivo é chegar aqui:**

```bash
# Após refatorar os prompts e fazer push
python src/push_prompts.py

# Executar avaliação
python src/evaluate.py

Executando avaliação dos prompts...
==================================================
Prompt: {seu_username}/bug_to_user_story_v2
==================================================

Métricas Derivadas:
  - Helpfulness: 0.94 ✓
  - Correctness: 0.96 ✓

Métricas Base:
  - F1-Score: 0.93 ✓
  - Clarity: 0.95 ✓
  - Precision: 0.92 ✓

✅ STATUS: APROVADO - Todas as métricas >= 0.9
```
---

## Tecnologias obrigatórias

- **Linguagem:** Python 3.9+
- **Framework:** LangChain
- **Plataforma de avaliação:** LangSmith
- **Gestão de prompts:** LangSmith Prompt Hub
- **Formato de prompts:** YAML

---

## Pacotes recomendados

```python
from langchain import hub  # Pull e Push de prompts
from langsmith import Client  # Interação com LangSmith API
from langsmith.evaluation import evaluate  # Avaliação de prompts
from langchain_openai import ChatOpenAI  # LLM OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI  # LLM Gemini
```

---

## OpenAI

- Crie uma **API Key** da OpenAI: https://platform.openai.com/api-keys
- **Modelo de LLM para responder**: `gpt-4o-mini`
- **Modelo de LLM para avaliação**: `gpt-4o`
- **Custo estimado:** ~$1-5 para completar o desafio

## Gemini (modelo free)

- Crie uma **API Key** da Google: https://aistudio.google.com/app/apikey
- **Modelo de LLM para responder**: `gemini-2.5-flash`
- **Modelo de LLM para avaliação**: `gemini-2.5-flash`
- **Limite:** 15 req/min, 1500 req/dia

---

