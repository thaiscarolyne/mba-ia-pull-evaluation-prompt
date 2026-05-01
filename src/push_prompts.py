"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    errors = []

    required_fields = ["system_prompt", "user_prompt"]

    for field in required_fields:
        if field not in prompt_data or not prompt_data[field].strip():
            errors.append(f"Campo obrigatório ausente: {field}")

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    try:
        print(f"Enviando prompt: {prompt_name}")

        # Cria ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"])
        ])

        # Push público
        hub.push(prompt_name, object=prompt)

        print(f"Prompt publicado: {prompt_name}")
        return True

    except Exception as e:
        print(f"Erro ao enviar prompt: {e}")
        return False


def main():
    print_section_header("Push de Prompts para LangSmith")

    check_env_vars(["LANGSMITH_API_KEY"])

    try:
        prompts = load_yaml("../prompts/bug_to_user_story_v2.yml")

        success = True

        for name, data in prompts.items():
            is_valid, errors = validate_prompt(data)

            if not is_valid:
                print(f"Prompt inválido: {name}")
                for err in errors:
                    print(f"  - {err}")
                success = False
                continue

            full_name = name

            result = push_prompt_to_langsmith(full_name, data)

            if not result:
                success = False

        return 0 if success else 1

    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())