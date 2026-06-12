from app.database import SessionLocal
from app.models import Campaign
from app.pipeline import rodar_pipeline
from app.services.messaging.templates import TEMPLATES  # import correto
from app.models import Lead
#python -m scripts.tests.pipe__1


def deletar_todas_campanhas():
    db = SessionLocal()
    try:
        campanhas = db.query(Campaign).all()
        if not campanhas:
            print("Nenhuma campanha para deletar.")
            return
        for campanha in campanhas:
            # Deleta leads associados
            db.query(Lead).filter(Lead.campaign_id == campanha.id).delete()
            # Deleta a campanha
            db.delete(campanha)
        db.commit()
        print(f"{len(campanhas)} campanhas e seus leads deletados.")
    finally:
        db.close()

def criar_campanha(name: str, query: str, nicho: str = "default") -> Campaign:
    db = SessionLocal()
    try:
        campanha = Campaign(name=name, query=query, nicho=nicho, status="PENDING")
        db.add(campanha)
        db.commit()
        db.refresh(campanha)
        print(f"Campanha '{name}' criada com ID {campanha.id}.")
        return campanha
    finally:
        db.close()


def adicionar_template_centrus():
    TEMPLATES["centris_prospect"] = (
        "Olá! Vi que a empresa *$nome_empresa* está em $cidade.\n\n"
        "Aqui na Centris (centris.netlify.app) oferecemos soluções completas de tecnologia para o seu negócio.\n\n"
        "Gostaria de saber mais e como podemos ajudar?"
    )
    print("Template para 'centris_prospect' adicionado.")


def main():
    # 1. Apaga todas as campanhas anteriores
    deletar_todas_campanhas()

    # 2. Adiciona o template customizado
    adicionar_template_centrus()

    # 3. Define uma query combinando nicho + região (exemplo)
    query = 'Imobiliárias em "Santos"'

    # 4. Cria a nova campanha com essa query
    campanha = criar_campanha(
        name="centris_prospect",
        query=query,
        nicho="centris_prospect"
    )

    # 5. Executa pipeline para a nova campanha
    rodar_pipeline(campanha.id, "teste_local")


if __name__ == "__main__":
    main()
