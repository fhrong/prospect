from app.services.lead_finder import buscar_empresas, criar_driver
from app.services.enrichment import buscar_cnpj, buscar_dados_receita


QUERY = 'Escritório de Contabilidade "Ribeirão Preto"'


def main():
    driver = criar_driver()

    try:
        # ── 1. Lead Finder ─────────────────────────────────────────────
        print("Buscando empresas...")
        nomes = buscar_empresas(driver, QUERY)
        print(f"\nEmpresas encontradas ({len(nomes)}):")
        for nome in nomes:
            print(f"  • {nome}")

        # ── 2. Enrichment ──────────────────────────────────────────────
        leads = []

        for nome in nomes:
            print(f"\nEnriquecendo: {nome}")

            cnpj = buscar_cnpj(driver, nome)
            if not cnpj:
                leads.append({"nome_original": nome})
                continue

            dados = buscar_dados_receita(cnpj, nome_fallback=nome)
            if not dados:
                leads.append({"nome_original": nome, "cnpj": cnpj})
                continue

            leads.append({"nome_original": nome, **dados})

        # ── 3. Resultado ───────────────────────────────────────────────
        print("\n\n" + "=" * 60)
        print("RESULTADO FINAL")
        print("=" * 60)

        for lead in leads:
            print(f"Nome Original : {lead.get('nome_original')}")
            print(f"Nome Oficial  : {lead.get('nome_oficial')}")
            print(f"CNPJ          : {lead.get('cnpj')}")
            print(f"Telefone      : {lead.get('telefone')}")
            print(f"Email         : {lead.get('email')}")
            print(f"Cidade        : {lead.get('cidade')}")
            print(f"UF            : {lead.get('uf')}")
            print("-" * 60)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()