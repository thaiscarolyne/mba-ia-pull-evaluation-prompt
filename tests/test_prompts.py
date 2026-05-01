"""
Testes automatizados para validação de prompts.

Cobrem os 6 cenários obrigatórios da Fase 5:

1. test_prompt_has_system_prompt
2. test_prompt_has_role_definition
3. test_prompt_mentions_format
4. test_prompt_has_few_shot_examples
5. test_prompt_no_todos
6. test_minimum_techniques

Como rodar:
    pytest tests/test_prompts.py -v
"""
import re
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str) -> dict:
    """Carrega prompts do arquivo YAML."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data() -> dict:
    """Carrega o bloco do prompt v2 uma vez por módulo de teste."""
    if not PROMPT_FILE.exists():
        pytest.fail(f"Arquivo de prompt não encontrado: {PROMPT_FILE}")

    raw = load_prompts(str(PROMPT_FILE))
    if PROMPT_KEY not in raw:
        pytest.fail(
            f"Chave '{PROMPT_KEY}' ausente em {PROMPT_FILE}. "
            f"Encontradas: {list(raw.keys())}"
        )
    return raw[PROMPT_KEY]


class TestPrompts:
    """Suite de validação estrutural do prompt otimizado v2."""

    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, (
            "Campo 'system_prompt' está ausente no YAML"
        )
        system_prompt = prompt_data["system_prompt"]
        assert isinstance(system_prompt, str), (
            f"'system_prompt' deveria ser string, é {type(system_prompt).__name__}"
        )
        assert system_prompt.strip(), "'system_prompt' está vazio"
        assert len(system_prompt.strip()) >= 100, (
            "'system_prompt' suspeitamente curto (< 100 chars) — provavelmente incompleto"
        )

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (role prompting).

        Aceita variações comuns em pt-BR/en para a abertura de um Role Prompt:
        'Você é um/uma...', 'Você é o/a...', 'Aja como...', 'You are...'.
        """
        system_prompt = prompt_data.get("system_prompt", "")

        role_patterns = [
            r"voc[êe]\s+[ée]\s+(?:um|uma|o|a)\s+",
            r"aja\s+como\s+(?:um|uma|o|a)?\s*",
            r"atue\s+como\s+(?:um|uma|o|a)?\s*",
            r"\byou\s+are\s+(?:an?|the)\s+",
        ]
        matched = any(
            re.search(pat, system_prompt, flags=re.IGNORECASE) for pat in role_patterns
        )
        assert matched, (
            "Persona não encontrada no system_prompt. "
            "Esperado algo como 'Você é um Product Manager...' ou 'Aja como ...'."
        )

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão.

        Considera-se 'menciona o formato' se o system_prompt referencia
        explicitamente a estrutura de User Story (Como/Eu quero/Para que ou
        Critérios de Aceitação) ou marcadores Markdown (===, ###, headers).
        """
        system_prompt = prompt_data.get("system_prompt", "").lower()

        user_story_signals = [
            "como um",
            "como o",
            "como uma",
            "eu quero",
            "para que",
            "critérios de aceitação",
            "user story",
        ]
        markdown_signals = ["===", "###", "## "]

        has_user_story_format = any(s in system_prompt for s in user_story_signals)
        has_markdown_format = any(s in system_prompt for s in markdown_signals)

        assert has_user_story_format or has_markdown_format, (
            "system_prompt não menciona o formato esperado "
            "(User Story padrão ou marcadores Markdown)."
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (Few-shot).

        Considera-se Few-shot se o system_prompt traz pelo menos 2 blocos
        identificáveis como 'Exemplo' OU pelo menos 2 pares 'Entrada/Saída'.
        """
        system_prompt = prompt_data.get("system_prompt", "")

        example_headers = re.findall(
            r"(?:^|\n)\s*(?:###\s*)?Exemplo\s*\d+", system_prompt, flags=re.IGNORECASE
        )
        entrada_blocks = re.findall(r"\bEntrada\s*:", system_prompt, flags=re.IGNORECASE)
        saida_blocks = re.findall(
            r"\bSa[íi]da(?:\s+esperada)?\s*:", system_prompt, flags=re.IGNORECASE
        )

        assert len(example_headers) >= 2 or (
            len(entrada_blocks) >= 2 and len(saida_blocks) >= 2
        ), (
            "Few-shot não detectado: esperado >= 2 blocos 'Exemplo N' "
            "OU >= 2 pares 'Entrada:'/'Saída:' no system_prompt. "
            f"Encontrados: example_headers={len(example_headers)}, "
            f"entrada_blocks={len(entrada_blocks)}, saida_blocks={len(saida_blocks)}"
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que nenhum [TODO] / TODO / FIXME ficou esquecido no texto."""
        suspicious_patterns = [
            r"\[\s*TODO\s*\]",
            r"\bTODO\b",
            r"\bFIXME\b",
            r"\[\s*PREENCHER\s*\]",
            r"\.{3}\s*completar",
        ]

        fields_to_check = {
            "description": prompt_data.get("description", ""),
            "system_prompt": prompt_data.get("system_prompt", ""),
            "user_prompt": prompt_data.get("user_prompt", ""),
        }

        leftovers = []
        for field, value in fields_to_check.items():
            if not isinstance(value, str):
                continue
            for pat in suspicious_patterns:
                if re.search(pat, value):
                    leftovers.append(f"{field} contém '{pat}'")

        assert not leftovers, "Marcadores não resolvidos encontrados: " + "; ".join(
            leftovers
        )

    def test_minimum_techniques(self, prompt_data):
        """Verifica via metadados do YAML se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])

        assert isinstance(techniques, list), (
            f"'techniques_applied' deveria ser uma lista, é {type(techniques).__name__}"
        )
        assert len(techniques) >= 2, (
            f"Esperado pelo menos 2 técnicas em 'techniques_applied'. "
            f"Encontradas: {len(techniques)} ({techniques!r})"
        )

        non_empty = [t for t in techniques if isinstance(t, str) and t.strip()]
        assert len(non_empty) >= 2, (
            "Pelo menos 2 técnicas precisam ser strings não vazias. "
            f"Lista atual: {techniques!r}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
