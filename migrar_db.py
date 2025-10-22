import sqlite3
from datetime import datetime, date


def migrar_banco():
    """Migra o banco de dados para o novo formato"""
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()

    # Backup das tabelas existentes
    cursor.execute("ALTER TABLE lancamentos RENAME TO lancamentos_old")

    # Criar nova tabela de lançamentos com suporte a parcelamento
    cursor.execute(
        """
        CREATE TABLE lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            conta_id INTEGER,
            responsavel_id INTEGER,
            categoria_id INTEGER,
            metodo_pagamento_id INTEGER,
            tipo TEXT CHECK(tipo IN ('receita', 'despesa')),
            valor REAL NOT NULL,
            descricao TEXT,
            data_lancamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_referencia DATE DEFAULT CURRENT_DATE,
            parcela_atual INTEGER DEFAULT NULL,
            total_parcelas INTEGER DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES usuarios (user_id),
            FOREIGN KEY (conta_id) REFERENCES contas (id),
            FOREIGN KEY (responsavel_id) REFERENCES responsaveis (id),
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (metodo_pagamento_id) REFERENCES metodos_pagamento (id)
        )
    """
    )

    # Migrar dados antigos
    cursor.execute(
        """
        INSERT INTO lancamentos (
            user_id, conta_id, responsavel_id, categoria_id,
            metodo_pagamento_id, tipo, valor, descricao,
            data_lancamento, data_referencia
        )
        SELECT 
            user_id, conta_id, responsavel_id, categoria_id,
            metodo_pagamento_id, tipo, valor, descricao,
            data_lancamento, date(data_lancamento)
        FROM lancamentos_old
    """
    )

    # Criar tabela de relatórios mensais
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS relatorios_mensais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mes INTEGER NOT NULL,
            ano INTEGER NOT NULL,
            arquivo_path TEXT NOT NULL,
            data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
        )
    """
    )

    # Commit e fechar conexão
    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("Iniciando migração do banco de dados...")
    migrar_banco()
    print("Migração concluída com sucesso!")
