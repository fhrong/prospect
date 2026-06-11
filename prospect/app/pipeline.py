"""
pipeline.py — orquestra LeadFinder + Enrichment + Messaging

Este é o script que roda uma campanha completa.
Recebe um campaign_id já criado via API e executa o pipeline.

Uso:
    python -m app.pipeline <campaign_id>

Exemplo:
    python -m app.pipeline 1
"""
import sys
from app.database import SessionLocal
from app.models import Campaign, Lead
from app.services.lead_finder import buscar_empresas, criar_driver
from app.services.enrichment import buscar_cnpj, buscar_dados_receita
from app.services.messaging import enviar_mensagem, montar_mensagem, verificar_numero


def rodar_pipeline(campaign_id: int):
    db = SessionLocal()

    try:
        # ── Busca a campanha no banco ──────────────────────────
        campanha = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campanha:
            print(f"Campanha {campaign_id} não encontrada.")
            return

        print(f"\nIniciando campanha: {campanha.name}")
        campanha.status = "RUNNING"
        db.commit()

        driver = criar_driver()

        try:
            # ── 1. LeadFinder ──────────────────────────────────
            print("\nBuscando empresas...")
            nomes = buscar_empresas(driver, campanha.query)
            print(f"{len(nomes)} empresas encontradas.")

            for nome in nomes:

                # Evita duplicatas na mesma campanha
                ja_existe = db.query(Lead).filter(
                    Lead.campaign_id == campaign_id,
                    Lead.nome_original == nome,
                ).first()

                if ja_existe:
                    print(f"  Pulando (já existe): {nome}")
                    continue

                # Cria o lead como NEW
                lead = Lead(campaign_id=campaign_id, nome_original=nome, status="NEW")
                db.add(lead)
                db.commit()
                db.refresh(lead)

                # ── 2. Enrichment ──────────────────────────────
                print(f"\nEnriquecendo: {nome}")
                cnpj = buscar_cnpj(driver, nome)

                if not cnpj:
                    continue

                dados = buscar_dados_receita(cnpj, nome_fallback=nome)
                if not dados:
                    continue

                lead.nome_oficial = dados.get("nome_oficial")
                lead.cnpj         = dados.get("cnpj")
                lead.telefone     = dados.get("telefone")
                lead.email        = dados.get("email")
                lead.cidade       = dados.get("cidade")
                lead.uf           = dados.get("uf")
                lead.status       = "ENRICHED"
                db.commit()

                # ── 3. Messaging (só se o plano incluir) ───────
                # Por enquanto está habilitado para todos.
                # Futuramente: checar campanha.plano antes de enviar.
                if not lead.telefone:
                    print(f"  Sem telefone: {nome}")
                    continue

                tem_whatsapp = verificar_numero("teste_local", lead.telefone)
                if not tem_whatsapp:
                    print(f"  Sem WhatsApp: {lead.telefone}")
                    continue

                texto = montar_mensagem(
                    campanha.nicho,
                    lead.nome_oficial or nome,
                    lead.cidade or "",
                )

                enviar_mensagem("teste_local", lead.telefone, texto)

                lead.status         = "CONTACTED"
                lead.ultima_mensagem = texto
                db.commit()

                print(f"  ✓ Mensagem enviada: {lead.nome_oficial}")

        finally:
            driver.quit()

        campanha.status = "DONE"
        db.commit()
        print(f"\nCampanha {campanha.name} finalizada.")

    except Exception as e:
        print(f"Erro no pipeline: {e}")
        campanha.status = "FAILED"
        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m app.pipeline <campaign_id>")
        sys.exit(1)

    campaign_id = int(sys.argv[1])
    rodar_pipeline(campaign_id)