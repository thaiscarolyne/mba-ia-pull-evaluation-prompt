"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Converte para formato YAML legível (custom do projeto)
4. Salva localmente em prompts/bug_to_user_story_v1.yml
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


# -----------------------------
# Helpers
# -----------------------------
def extract_message_content(msg):
    """
    Extrai conteúdo de mensagens do LangChain de forma robusta,
    independente da versão/estrutura interna.
    """

    # Caso clássico (PromptTemplate dentro da mensagem)
    if hasattr(msg, "prompt") and hasattr(msg.prompt, "template"):
        return msg.prompt.template

    # Alguns casos usam diretamente content
    if hasattr(msg, "content") and msg.content:
        return msg.content

    # Fallback (string completa do objeto)
    try:
        return str(msg)
    except Exception:
        return ""


def convert_langchain_prompt_to_custom(prompt_obj, prompt_name: str) -> dict:
    """
    Converte usando format_messages (forma mais confiável)
    """

    try:
        # Injeta variável fake só pra renderizar
        formatted_messages = prompt_obj.format_messages(
            bug_report="__TEST__"
        )

        system_prompt = ""
        user_prompt = ""

        for msg in formatted_messages:
            if msg.type == "system":
                system_prompt = msg.content.replace("__TEST__", "{bug_report}")

            elif msg.type in ["human", "user"]:
                user_prompt = msg.content.replace("__TEST__", "{bug_report}")

        if not system_prompt and not user_prompt:
            raise ValueError("Não foi possível extrair conteúdo do prompt.")

        return {
            prompt_name: {
                "description": "Prompt para converter relatos de bugs em User Stories",
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "version": "v1",
                "source": "langsmith",
            }
        }

    except Exception as e:
        raise ValueError(f"Erro ao converter prompt: {e}")

# -----------------------------
# Main logic
# -----------------------------
def pull_prompts_from_langsmith():
    """
    Faz pull do prompt e salva localmente
    """

    print_section_header("Pulling prompts from LangSmith")

    # Valida env
    check_env_vars(["LANGSMITH_API_KEY"])

    try:
        prompt_id = "leonanluppi/bug_to_user_story_v1"

        print(f"Pulling prompt: {prompt_id}")

        # Pull do LangSmith Hub
        prompt_obj = hub.pull(prompt_id)

        if not prompt_obj:
            raise ValueError(f"Prompt '{prompt_id}' não encontrado")

        print("Convertendo prompt...")

        # Converte para formato custom
        prompt_dict = convert_langchain_prompt_to_custom(prompt_obj, prompt_id)

        # Caminho de saída
        output_path = Path("../prompts/bug_to_user_story_v1.yml")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Salva YAML
        save_yaml(prompt_dict, output_path)

        print(f"Prompt salvo em: {output_path}")

        return 0

    except Exception as e:
        print(f"Erro ao fazer pull do prompt: {e}")
        return 1


def main():
    print_section_header("LangSmith Prompt Pull Script")

    result = pull_prompts_from_langsmith()

    if result == 0:
        print("\nProcesso concluído com sucesso!")
    else:
        print("\nProcesso finalizado com erros.")

    return result


if __name__ == "__main__":
    sys.exit(main())