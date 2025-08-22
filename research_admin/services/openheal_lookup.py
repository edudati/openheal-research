from django.db import connections

def get_openheal_id_by_email(email: str) -> str | None:
    """
    Busca o Id na tabela pública "UsersData" do Postgres externo pelo e-mail.
    Retorna o Id como string ou None se não encontrar.
    """
    email = (email or "").strip()
    if not email:
        return None

    # Use uma conexão somente leitura
    with connections["openheal_ext"].cursor() as cur:
        # Case-insensitive; ajuste o nome da coluna/tabela se preciso
        cur.execute('SELECT "Id" FROM "UsersData" WHERE "Email" ILIKE %s LIMIT 1', [email])
        row = cur.fetchone()
        return row[0] if row else None
