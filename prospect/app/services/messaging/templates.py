from string import Template


# ──────────────────────────────────────────────
# Templates de mensagem por nicho.
#
# Variáveis disponíveis:
#   $nome_empresa  → nome da empresa do lead
#   $cidade        → cidade da empresa
#
# Para adicionar um novo nicho, basta incluir
# uma nova entrada no dicionário TEMPLATES.
# ──────────────────────────────────────────────

TEMPLATES: dict[str, str] = {
    "contabilidade": (
        "Olá! Vi que a *$nome_empresa* atua na área contábil em $cidade.\n\n"
        "Trabalho com automação de prospecção B2B e achei que poderia "
        "fazer sentido pra vocês.\n\n"
        "Posso te explicar em 2 minutos como funciona?"
    ),
    "advocacia": (
        "Olá! Identifiquei o escritório *$nome_empresa* em $cidade.\n\n"
        "Tenho uma solução que automatiza a prospecção de clientes para "
        "escritórios de advocacia.\n\n"
        "Faz sentido conversar?"
    ),
    "clinica": (
        "Olá! Vi que a *$nome_empresa* está em $cidade.\n\n"
        "Ajudo clínicas a automatizar a captação de novos pacientes pelo WhatsApp.\n\n"
        "Posso te mostrar como funciona?"
    ),
    "default": (
        "Olá! Vi que a *$nome_empresa* está em $cidade.\n\n"
        "Tenho uma solução que pode ajudar o seu negócio a crescer "
        "com menos esforço.\n\n"
        "Posso te apresentar em 2 minutos?"
    ),
}


def montar_mensagem(nicho: str, nome_empresa: str, cidade: str = "") -> str:
    """
    Retorna a mensagem formatada para o nicho informado.
    Usa o template 'default' se o nicho não existir.

    Uso:
        texto = montar_mensagem("contabilidade", "ABC Contabilidade", "Ribeirão Preto")
    """
    template_str = TEMPLATES.get(nicho.lower(), TEMPLATES["default"])
    template = Template(template_str)

    return template.safe_substitute(
        nome_empresa=nome_empresa,
        cidade=cidade or "sua cidade",
    )