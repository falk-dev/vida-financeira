# Bot de Vida Financeira - Telegram
# Sistema inteligente para controle financeiro pessoal

import os
import sqlite3
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Tuple
import re
import csv
import json
import calendar
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
)

# Configuração de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_database_connection():
    """Retorna conexão com o banco de dados"""
    return sqlite3.connect("financeiro.db")


def gerar_relatorio_mensal(user_id: int, mes: int, ano: int) -> str:
    """Gera relatório mensal em CSV"""
    conn = get_database_connection()
    cursor = conn.cursor()

    os.makedirs("relatorios", exist_ok=True)
    filepath = os.path.join("relatorios", f"relatorio_{mes:02d}_{ano}.csv")

    cursor.execute(
        """
        SELECT l.*, c.nome as categoria, r.nome as responsavel, m.nome as metodo
        FROM lancamentos l
        LEFT JOIN categorias c ON l.categoria_id = c.id
        LEFT JOIN responsaveis r ON l.responsavel_id = r.id
        LEFT JOIN metodos_pagamento m ON l.metodo_pagamento_id = m.id
        WHERE l.user_id = ? 
        AND strftime('%m', l.data_referencia) = ?
        AND strftime('%Y', l.data_referencia) = ?
    """,
        (user_id, f"{mes:02d}", str(ano)),
    )

    lancamentos = cursor.fetchall()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Data",
                "Tipo",
                "Valor",
                "Categoria",
                "Descrição",
                "Responsável",
                "Método",
                "Parcela",
            ]
        )

        for l in lancamentos:
            parcela_info = (
                f"[{l['parcela_atual']}/{l['total_parcelas']}]"
                if l["parcela_atual"]
                else ""
            )
            writer.writerow(
                [
                    l["data_lancamento"],
                    l["tipo"],
                    l["valor"],
                    l["categoria"],
                    l["descricao"],
                    l["responsavel"],
                    l["metodo"],
                    parcela_info,
                ]
            )

    conn.close()
    return filepath


class ParsingInteligente:
    """Classe responsável pelo parsing inteligente dos comandos"""

    def __init__(self):
        # Adiciona campo para parcelamentos
        self.padrao_parcelas = re.compile(r"\[(\d+)/(\d+)\]")
        # Palavras-chave para identificar tipos de transação
        self.palavras_receita = [
            "receita",
            "salário",
            "salario",
            "renda",
            "entrada",
            "ganho",
            "bônus",
            "bonus",
            "freelance",
            "venda",
            "investimento",
            "dividendos",
            "juros",
            "reembolso",
        ]

        self.palavras_despesa = [
            "despesa",
            "gasto",
            "compra",
            "pagamento",
            "conta",
            "aluguel",
            "supermercado",
            "combustível",
            "combustivel",
            "gasolina",
            "transporte",
            "alimentação",
            "alimentacao",
            "lanche",
            "jantar",
            "almoço",
            "almoco",
            "café",
            "cafe",
            "farmácia",
            "farmacia",
            "medicamento",
            "roupa",
            "calçado",
            "calcado",
            "lazer",
            "cinema",
            "teatro",
            "restaurante",
            "bar",
            "shopping",
            "internet",
            "telefone",
            "energia",
            "água",
            "agua",
        ]

        # Categorias comuns
        self.categorias_comuns = {
            "alimentação": [
                "alimentação",
                "alimentacao",
                "comida",
                "lanche",
                "jantar",
                "almoço",
                "almoco",
                "café",
                "cafe",
                "restaurante",
                "bar",
            ],
            "transporte": [
                "transporte",
                "combustível",
                "combustivel",
                "gasolina",
                "uber",
                "taxi",
                "ônibus",
                "onibus",
                "metro",
            ],
            "saúde": [
                "saúde",
                "saude",
                "farmácia",
                "farmacia",
                "medicamento",
                "médico",
                "medico",
                "hospital",
                "terapia",
            ],
            "lazer": [
                "lazer",
                "cinema",
                "teatro",
                "shopping",
                "viagem",
                "férias",
                "ferias",
            ],
            "casa": [
                "casa",
                "aluguel",
                "energia",
                "água",
                "agua",
                "internet",
                "telefone",
            ],
            "roupas": [
                "roupa",
                "calçado",
                "calcado",
                "vestuário",
                "vestuario",
            ],
            "educação": [
                "educação",
                "educacao",
                "curso",
                "livro",
                "escola",
                "faculdade",
            ],
            "investimentos": [
                "investimento",
                "poupança",
                "poupanca",
                "ações",
                "acoes",
                "fundos",
            ],
        }

        # Padrões regex para extrair informações
        self.padrao_valor = re.compile(r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)")
        self.padrao_data = re.compile(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})")

        # Palavras-chave para métodos de pagamento
        self.metodos_pagamento = {
            "dinheiro": [
                "dinheiro",
                "cash",
                "especie",
                "espécie",
            ],
            "pix": [
                "pix",
            ],
            "cartao": [
                "cartão",
                "cartao",
                "credito",
                "crédito",
                "debito",
                "débito",
                "visa",
                "mastercard",
            ],
            "transferencia": [
                "transferencia",
                "transferência",
                "ted",
                "doc",
            ],
            "conta": [
                "conta",
                "corrente",
                "poupança",
                "poupanca",
                "nubank",
                "itau",
                "bradesco",
                "caixa",
            ],
        }

    def parse_comando_add(self, texto: str) -> Dict:
        """
        Faz parsing inteligente do comando /add
        Exemplo: /add alimentação despesa 25,50 almoço no araujo
        """
        # Remove o comando /add do início
        texto = texto.replace("/add", "").strip()

        resultado = {
            "categoria": None,
            "tipo": None,
            "valor": None,
            "descricao": None,
            "responsavel": None,
            "metodo_pagamento": None,
            "erro": None,
        }

        try:
            # 1. Extrair valor (número com vírgula ou ponto)
            valores_encontrados = self.padrao_valor.findall(texto)
            if valores_encontrados:
                valor_str = valores_encontrados[0]
                # Converter vírgula para ponto e remover separadores de milhares
                valor_str = valor_str.replace(",", ".").replace(
                    ".", "", valor_str.count(".") - 1
                )
                resultado["valor"] = float(valor_str)
                # Remove o valor do texto para facilitar parsing do resto
                texto = texto.replace(valores_encontrados[0], "").strip()

            # 2. Identificar tipo (receita ou despesa)
            texto_lower = texto.lower()
            for palavra in self.palavras_receita:
                if palavra in texto_lower:
                    resultado["tipo"] = "receita"
                    break

            if not resultado["tipo"]:
                for palavra in self.palavras_despesa:
                    if palavra in texto_lower:
                        resultado["tipo"] = "despesa"
                        break

            # Se não encontrou tipo específico, assume despesa por padrão
            if not resultado["tipo"]:
                resultado["tipo"] = "despesa"

            # 3. Identificar categoria
            categoria_encontrada = None
            for categoria, palavras in self.categorias_comuns.items():
                for palavra in palavras:
                    if palavra in texto_lower:
                        categoria_encontrada = categoria
                        break
                if categoria_encontrada:
                    break

            resultado["categoria"] = categoria_encontrada or "outros"

            # 4. Identificar método de pagamento
            metodo_encontrado = None
            for metodo, palavras in self.metodos_pagamento.items():
                for palavra in palavras:
                    if palavra in texto_lower:
                        metodo_encontrado = metodo
                        break
                if metodo_encontrado:
                    break

            resultado["metodo_pagamento"] = metodo_encontrado or "dinheiro"

            # 5. Responsável será definido pelo usuário que enviou a mensagem
            # (será passado como parâmetro na função add_lancamento)
            resultado["responsavel"] = None  # Será definido pelo nome do usuário

            # 6. Descrição é o que sobrou do texto
            resultado["descricao"] = texto.strip()

            # Validações
            if not resultado["valor"]:
                resultado["erro"] = "Valor não encontrado. Use formato: 25,50 ou 25.50"
            elif resultado["valor"] <= 0:
                resultado["erro"] = "Valor deve ser maior que zero"

        except Exception as e:
            resultado["erro"] = f"Erro no parsing: {str(e)}"

        return resultado

    def parse_comando_meta(self, texto: str) -> Dict:
        """
        Faz parsing inteligente do comando /meta
        Exemplo: /meta Viagem de Casamento 20000 30-03-26
        """
        # Remove o comando /meta do início
        texto = texto.replace("/meta", "").strip()

        resultado = {"nome": None, "valor": None, "data_limite": None, "erro": None}

        try:
            # 1. Extrair valor
            valores_encontrados = self.padrao_valor.findall(texto)
            if valores_encontrados:
                valor_str = valores_encontrados[0]
                valor_str = valor_str.replace(",", ".").replace(
                    ".", "", valor_str.count(".") - 1
                )
                resultado["valor"] = float(valor_str)
                # Remove o valor do texto
                texto = texto.replace(valores_encontrados[0], "").strip()

            # 2. Extrair data
            datas_encontradas = self.padrao_data.findall(texto)
            if datas_encontradas:
                data_str = datas_encontradas[0]
                resultado["data_limite"] = self.parse_data(data_str)
                # Remove a data do texto
                texto = texto.replace(datas_encontradas[0], "").strip()

            # 3. Nome é o que sobrou
            resultado["nome"] = texto.strip()

            # Validações
            if not resultado["nome"]:
                resultado["erro"] = "Nome da meta não encontrado"
            elif not resultado["valor"]:
                resultado["erro"] = "Valor da meta não encontrado"
            elif resultado["valor"] <= 0:
                resultado["erro"] = "Valor da meta deve ser maior que zero"

        except Exception as e:
            resultado["erro"] = f"Erro no parsing: {str(e)}"

        return resultado

    def parse_data(self, data_str: str) -> str:
        """Converte string de data para formato YYYY-MM-DD"""
        try:
            # Remove caracteres não numéricos exceto separadores
            data_limpa = re.sub(r"[^\d/-]", "", data_str)

            # Tenta diferentes formatos
            formatos = ["%d-%m-%y", "%d/%m/%y", "%d-%m-%Y", "%d/%m/%Y"]

            for formato in formatos:
                try:
                    data_obj = datetime.strptime(data_limpa, formato)
                    return data_obj.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # Se não conseguiu parsear, retorna como está
            return data_str

        except Exception:
            return data_str


class VidaFinanceiraBot:
    def generate_monthly_report(self) -> None:
        """Gera o relatório CSV mensal e zera os gastos mantendo o saldo."""
        hoje = date.today()
        mes_anterior = hoje.replace(day=1) - timedelta(days=1)

        # Conecta ao banco de dados
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Busca todos os usuários
        cursor.execute("SELECT user_id FROM usuarios")
        usuarios = cursor.fetchall()

        for (user_id,) in usuarios:
            # Calcula o saldo atual
            cursor.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE -valor END), 0)
                FROM lancamentos
                WHERE user_id = ? AND strftime('%Y-%m', data_referencia) = ?
            """,
                (user_id, mes_anterior.strftime("%Y-%m")),
            )
            saldo = cursor.fetchone()[0]

            # Gera o nome do arquivo CSV
            csv_filename = (
                f"relatorios/relatorio_{user_id}_{mes_anterior.strftime('%Y_%m')}.csv"
            )
            os.makedirs("relatorios", exist_ok=True)

            # Busca todos os lançamentos do mês
            cursor.execute(
                """
                SELECT l.tipo, l.valor, l.descricao, c.nome as categoria, r.nome as responsavel,
                       m.nome as metodo_pagamento, l.parcela_atual, l.total_parcelas,
                       l.data_referencia
                FROM lancamentos l
                LEFT JOIN categorias c ON l.categoria_id = c.id
                LEFT JOIN responsaveis r ON l.responsavel_id = r.id
                LEFT JOIN metodos_pagamento m ON l.metodo_pagamento_id = m.id
                WHERE l.user_id = ? AND strftime('%Y-%m', l.data_referencia) = ?
                ORDER BY l.data_referencia, l.tipo
            """,
                (user_id, mes_anterior.strftime("%Y-%m")),
            )

            lancamentos = cursor.fetchall()

            # Gera o arquivo CSV
            with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Tipo",
                        "Valor",
                        "Descrição",
                        "Categoria",
                        "Responsável",
                        "Método de Pagamento",
                        "Parcela",
                        "Data",
                    ]
                )

                for l in lancamentos:
                    parcela_info = f"[{l[6]}/{l[7]}]" if l[6] and l[7] else ""
                    writer.writerow(
                        [l[0], l[1], l[2], l[3], l[4], l[5], parcela_info, l[8]]
                    )

                # Adiciona linha com o saldo final
                writer.writerow(["", "", "", "", "", "", ""])
                writer.writerow(["Saldo Final", saldo])

            # Registra o relatório no banco de dados
            cursor.execute(
                """
                INSERT INTO relatorios_mensais (user_id, mes, ano, arquivo_path)
                VALUES (?, ?, ?, ?)
            """,
                (user_id, mes_anterior.month, mes_anterior.year, csv_filename),
            )

            # Zera os gastos do mês mantendo o saldo
            if saldo > 0:
                # Adiciona o saldo como receita inicial do novo mês
                cursor.execute(
                    """
                    INSERT INTO lancamentos (user_id, tipo, valor, descricao, data_referencia)
                    VALUES (?, 'receita', ?, 'Saldo do mês anterior', ?)
                """,
                    (user_id, saldo, hoje),
                )

        conn.commit()
        conn.close()

    def __init__(self, token: str):
        """Inicializa o bot de vida financeira"""
        self.token = token
        self.db_path = "financeiro.db"
        self.parser = ParsingInteligente()
        # Configura o scheduler para gerar relatório mensal
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            self.generate_monthly_report, "cron", day="1", hour="0", minute="0"
        )
        self.scheduler.start()
        self.init_database()

    def init_database(self):
        """Inicializa o banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabela de usuários
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Tabela de contas
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                nome TEXT NOT NULL,
                saldo REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
            )
        """
        )

        # Tabela de responsáveis
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS responsaveis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                nome TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
            )
        """
        )

        # Tabela de categorias
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                nome TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('receita', 'despesa')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
            )
        """
        )

        # Tabela de lançamentos
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lancamentos (
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

        # Tabela de relatórios mensais
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

        # Tabela de metas
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                nome TEXT NOT NULL,
                valor_meta REAL NOT NULL,
                valor_atual REAL DEFAULT 0,
                data_limite DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
            )
        """
        )

        # Tabela de métodos de pagamento
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metodos_pagamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                nome TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('conta', 'cartao', 'dinheiro', 'pix', 'transferencia')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
            )
        """
        )

        # Tabela de relatórios mensais
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

        # Tabela de limites de gastos
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS limites_gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                categoria_id INTEGER,
                valor_limite REAL NOT NULL,
                periodo TEXT DEFAULT 'mensal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (user_id),
                FOREIGN KEY (categoria_id) REFERENCES categorias (id)
            )
        """
        )

        conn.commit()
        conn.close()

        logger.info("Banco de dados inicializado com sucesso!")

    def registrar_usuario(self, user_id: int, username: str, first_name: str):
        """Registra ou atualiza usuário no banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO usuarios (user_id, username, first_name)
            VALUES (?, ?, ?)
        """,
            (user_id, username, first_name),
        )

        conn.commit()
        conn.close()

    def criar_conta_padrao(self, user_id: int):
        """Cria conta padrão para o usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verifica se já existe conta padrão
        cursor.execute(
            "SELECT id FROM contas WHERE user_id = ? AND nome = ?",
            (user_id, "Conta Principal"),
        )

        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO contas (user_id, nome, saldo)
                VALUES (?, ?, ?)
            """,
                (user_id, "Conta Principal", 0),
            )

        conn.commit()
        conn.close()

    def criar_responsavel_padrao(self, user_id: int, nome: str):
        """Cria responsável padrão para o usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verifica se já existe responsável padrão
        cursor.execute(
            "SELECT id FROM responsaveis WHERE user_id = ? AND nome = ?",
            (user_id, nome),
        )

        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO responsaveis (user_id, nome)
                VALUES (?, ?)
            """,
                (user_id, nome),
            )

        conn.commit()
        conn.close()

    def criar_metodo_pagamento_padrao(self, user_id: int):
        """Cria métodos de pagamento padrão para o usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        metodos_padrao = [
            ("Dinheiro", "dinheiro"),
            ("PIX", "pix"),
            ("Cartão de Crédito", "cartao"),
            ("Cartão de Débito", "cartao"),
            ("Transferência", "transferencia"),
        ]

        for nome, tipo in metodos_padrao:
            # Verifica se já existe
            cursor.execute(
                "SELECT id FROM metodos_pagamento WHERE user_id = ? AND nome = ?",
                (user_id, nome),
            )

            if not cursor.fetchone():
                cursor.execute(
                    """
                    INSERT INTO metodos_pagamento (user_id, nome, tipo)
                    VALUES (?, ?, ?)
                """,
                    (user_id, nome, tipo),
                )

        conn.commit()
        conn.close()

    def obter_ou_criar_responsavel(self, user_id: int, nome_responsavel: str) -> int:
        """Obtém ou cria responsável e retorna o ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Busca responsável existente
        cursor.execute(
            """
            SELECT id FROM responsaveis 
            WHERE user_id = ? AND nome = ?
        """,
            (user_id, nome_responsavel),
        )

        resultado = cursor.fetchone()

        if resultado:
            responsavel_id = resultado[0]
        else:
            # Cria novo responsável
            cursor.execute(
                """
                INSERT INTO responsaveis (user_id, nome)
                VALUES (?, ?)
            """,
                (user_id, nome_responsavel),
            )
            responsavel_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return responsavel_id

    def obter_ou_criar_metodo_pagamento(self, user_id: int, nome_metodo: str) -> int:
        """Obtém ou cria método de pagamento e retorna o ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Busca método existente
        cursor.execute(
            """
            SELECT id FROM metodos_pagamento 
            WHERE user_id = ? AND nome = ?
        """,
            (user_id, nome_metodo),
        )

        resultado = cursor.fetchone()

        if resultado:
            metodo_id = resultado[0]
        else:
            # Determina tipo baseado no nome
            nome_lower = nome_metodo.lower()
            if (
                "cartão" in nome_lower
                or "cartao" in nome_lower
                or "credito" in nome_lower
                or "debito" in nome_lower
            ):
                tipo = "cartao"
            elif "pix" in nome_lower:
                tipo = "pix"
            elif "dinheiro" in nome_lower or "cash" in nome_lower:
                tipo = "dinheiro"
            elif "transferencia" in nome_lower or "ted" in nome_lower:
                tipo = "transferencia"
            else:
                tipo = "conta"

            # Cria novo método
            cursor.execute(
                """
                INSERT INTO metodos_pagamento (user_id, nome, tipo)
                VALUES (?, ?, ?)
            """,
                (user_id, nome_metodo, tipo),
            )
            metodo_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return metodo_id

    def obter_ou_criar_categoria(
        self, user_id: int, nome_categoria: str, tipo: str
    ) -> int:
        """Obtém ou cria categoria e retorna o ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Busca categoria existente
        cursor.execute(
            """
            SELECT id FROM categorias 
            WHERE user_id = ? AND nome = ? AND tipo = ?
        """,
            (user_id, nome_categoria, tipo),
        )

        resultado = cursor.fetchone()

        if resultado:
            categoria_id = resultado[0]
        else:
            # Cria nova categoria
            cursor.execute(
                """
                INSERT INTO categorias (user_id, nome, tipo)
                VALUES (?, ?, ?)
            """,
                (user_id, nome_categoria, tipo),
            )
            categoria_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return categoria_id

    def adicionar_lancamento(
        self,
        user_id: int,
        categoria: str,
        tipo: str,
        valor: float,
        descricao: str,
        responsavel: str = None,
        metodo_pagamento: str = None,
    ) -> bool:
        """Adiciona lançamento ao banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Obtém conta padrão
            cursor.execute(
                "SELECT id FROM contas WHERE user_id = ? AND nome = ?",
                (user_id, "Conta Principal"),
            )
            conta_id = cursor.fetchone()[0]

            # Obtém ou cria responsável
            responsavel_id = self.obter_ou_criar_responsavel(
                user_id, responsavel or "Eu"
            )

            # Obtém ou cria categoria
            categoria_id = self.obter_ou_criar_categoria(user_id, categoria, tipo)

            # Obtém ou cria método de pagamento
            metodo_pagamento_id = self.obter_ou_criar_metodo_pagamento(
                user_id, metodo_pagamento or "Dinheiro"
            )

            # Adiciona lançamento
            cursor.execute(
                """
                INSERT INTO lancamentos (user_id, conta_id, responsavel_id, categoria_id, 
                                       metodo_pagamento_id, tipo, valor, descricao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    conta_id,
                    responsavel_id,
                    categoria_id,
                    metodo_pagamento_id,
                    tipo,
                    valor,
                    descricao,
                ),
            )

            # Atualiza saldo da conta
            if tipo == "receita":
                cursor.execute(
                    """
                    UPDATE contas SET saldo = saldo + ? WHERE id = ?
                """,
                    (valor, conta_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE contas SET saldo = saldo - ? WHERE id = ?
                """,
                    (valor, conta_id),
                )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar lançamento: {e}")
            return False

    def obter_saldo(self, user_id: int) -> float:
        """Obtém saldo atual do casal (todos os usuários)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Busca saldo de todos os usuários (casal compartilhado)
        cursor.execute("SELECT SUM(saldo) FROM contas")
        resultado = cursor.fetchone()

        conn.close()
        return resultado[0] if resultado[0] else 0.0

    def adicionar_meta(
        self, user_id: int, nome: str, valor_meta: float, data_limite: str = None
    ) -> bool:
        """Adiciona meta ao banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO metas (user_id, nome, valor_meta, data_limite)
                VALUES (?, ?, ?, ?)
            """,
                (user_id, nome, valor_meta, data_limite),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar meta: {e}")
            return False

    def listar_metas(self, user_id: int) -> List[Dict]:
        """Lista todas as metas do usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, nome, valor_meta, valor_atual, data_limite, created_at
            FROM metas WHERE user_id = ?
            ORDER BY created_at DESC
        """,
            (user_id,),
        )

        metas = []
        for row in cursor.fetchall():
            metas.append(
                {
                    "id": row[0],
                    "nome": row[1],
                    "valor_meta": row[2],
                    "valor_atual": row[3],
                    "data_limite": row[4],
                    "created_at": row[5],
                }
            )

        conn.close()
        return metas

    def obter_lancamentos_por_periodo(
        self, user_id: int, periodo: str = None
    ) -> List[Dict]:
        """Obtém lançamentos por período (casal compartilhado)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if periodo:
            # Implementar filtro por período (mês atual por padrão)
            cursor.execute(
                """
                SELECT l.id, l.tipo, l.valor, l.descricao, l.data_lancamento, c.nome as categoria, r.nome as responsavel
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                JOIN responsaveis r ON l.responsavel_id = r.id
                WHERE strftime('%Y-%m', l.data_lancamento) = strftime('%Y-%m', 'now')
                ORDER BY l.data_lancamento DESC
            """
            )
        else:
            cursor.execute(
                """
                SELECT l.id, l.tipo, l.valor, l.descricao, l.data_lancamento, c.nome as categoria, r.nome as responsavel
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                JOIN responsaveis r ON l.responsavel_id = r.id
                ORDER BY l.data_lancamento DESC
            """
            )

        lancamentos = []
        for row in cursor.fetchall():
            lancamentos.append(
                {
                    "id": row[0],
                    "tipo": row[1],
                    "valor": row[2],
                    "descricao": row[3],
                    "data_lancamento": row[4],
                    "categoria": row[5],
                    "responsavel": row[6],
                }
            )

        conn.close()
        return lancamentos

    def obter_resumo_por_categoria(self, user_id: int, periodo: str = None) -> Dict:
        """Obtém resumo de gastos por categoria (casal compartilhado)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if periodo:
            cursor.execute(
                """
                SELECT c.nome, l.tipo, SUM(l.valor) as total
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                WHERE strftime('%Y-%m', l.data_lancamento) = strftime('%Y-%m', 'now')
                GROUP BY c.nome, l.tipo
                ORDER BY total DESC
            """
            )
        else:
            cursor.execute(
                """
                SELECT c.nome, l.tipo, SUM(l.valor) as total
                FROM lancamentos l
                JOIN categorias c ON l.categoria_id = c.id
                GROUP BY c.nome, l.tipo
                ORDER BY total DESC
            """
            )

        resumo = {}
        for row in cursor.fetchall():
            categoria = row[0]
            tipo = row[1]
            total = row[2]

            if categoria not in resumo:
                resumo[categoria] = {"receita": 0, "despesa": 0}

            resumo[categoria][tipo] = total

        conn.close()
        return resumo

    def criar_grafico_gastos(self, user_id: int) -> str:
        """Cria gráfico de gastos por categoria (versão simplificada)"""
        try:
            resumo = self.obter_resumo_por_categoria(user_id)

            # Filtrar apenas despesas
            categorias = []
            valores = []

            for categoria, dados in resumo.items():
                if dados["despesa"] > 0:
                    categorias.append(categoria)
                    valores.append(dados["despesa"])

            if not categorias:
                return "📊 Nenhum gasto encontrado para criar gráfico."

            # Criar gráfico simples em texto
            total = sum(valores)
            grafico_texto = "📊 **Gráfico de Gastos por Categoria**\n\n"

            for i, (categoria, valor) in enumerate(zip(categorias, valores)):
                percentual = (valor / total) * 100
                barra = "█" * int(percentual / 2)  # Barra visual simples
                grafico_texto += f"{categoria}: {percentual:.1f}%\n"
                grafico_texto += f"`{barra}` R$ {valor:.2f}\n\n"

            return grafico_texto

        except Exception as e:
            logger.error(f"Erro ao criar gráfico: {e}")
            return None

    def exportar_csv(self, user_id: int) -> str:
        """Exporta dados para CSV (versão simplificada)"""
        try:
            lancamentos = self.obter_lancamentos_por_periodo(user_id)

            if not lancamentos:
                return None

            # Salvar CSV usando biblioteca nativa
            filename = f"dados_financeiros_{user_id}.csv"

            with open(filename, "w", newline="", encoding="utf-8-sig") as csvfile:
                fieldnames = [
                    "id",
                    "tipo",
                    "valor",
                    "descricao",
                    "data_lancamento",
                    "categoria",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for lancamento in lancamentos:
                    # Formatar data
                    try:
                        data_obj = datetime.fromisoformat(
                            lancamento["data_lancamento"].replace("Z", "+00:00")
                        )
                        lancamento["data_lancamento"] = data_obj.strftime(
                            "%d/%m/%Y %H:%M"
                        )
                    except:
                        # Se não conseguir parsear, manter como está
                        pass
                    writer.writerow(lancamento)

            return filename

        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            return None

    def adicionar_limite_gasto(
        self, user_id: int, categoria: str, valor_limite: float
    ) -> bool:
        """Adiciona limite de gasto para categoria"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Obtém categoria
            cursor.execute(
                """
                SELECT id FROM categorias 
                WHERE user_id = ? AND nome = ? AND tipo = 'despesa'
            """,
                (user_id, categoria),
            )

            resultado = cursor.fetchone()
            if not resultado:
                # Cria categoria se não existir
                categoria_id = self.obter_ou_criar_categoria(
                    user_id, categoria, "despesa"
                )
            else:
                categoria_id = resultado[0]

            # Adiciona limite
            cursor.execute(
                """
                INSERT OR REPLACE INTO limites_gastos (user_id, categoria_id, valor_limite)
                VALUES (?, ?, ?)
            """,
                (user_id, categoria_id, valor_limite),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar limite: {e}")
            return False

    def verificar_limites(self, user_id: int) -> List[Dict]:
        """Verifica se algum limite foi ultrapassado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT c.nome, lg.valor_limite, COALESCE(SUM(l.valor), 0) as gasto_atual
            FROM limites_gastos lg
            JOIN categorias c ON lg.categoria_id = c.id
            LEFT JOIN lancamentos l ON l.categoria_id = c.id 
                AND l.user_id = ? 
                AND l.tipo = 'despesa'
                AND strftime('%Y-%m', l.data_lancamento) = strftime('%Y-%m', 'now')
            WHERE lg.user_id = ?
            GROUP BY c.nome, lg.valor_limite
            HAVING gasto_atual > lg.valor_limite
        """,
            (user_id, user_id),
        )

        limites_ultrapassados = []
        for row in cursor.fetchall():
            limites_ultrapassados.append(
                {
                    "categoria": row[0],
                    "limite": row[1],
                    "gasto_atual": row[2],
                    "excesso": row[2] - row[1],
                }
            )

        conn.close()
        return limites_ultrapassados

    def resetar_dados(self, user_id: int) -> bool:
        """Resetar todos os dados do usuário"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Deletar dados do usuário
            cursor.execute("DELETE FROM lancamentos WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM metas WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM limites_gastos WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM categorias WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM responsaveis WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM contas WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM usuarios WHERE user_id = ?", (user_id,))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Erro ao resetar dados: {e}")
            return False


def main():
    """Função principal para iniciar o bot"""
    # Token do bot (você precisa criar um bot no @BotFather do Telegram)
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not BOT_TOKEN:
        print("❌ Erro: Token do bot não encontrado!")
        print("📝 Para criar um bot:")
        print("1. Acesse @BotFather no Telegram")
        print("2. Digite /newbot")
        print("3. Escolha um nome para seu bot")
        print("4. Escolha um username (deve terminar com 'bot')")
        print("5. Copie o token e defina como variável de ambiente TELEGRAM_BOT_TOKEN")
        return

    # Criar instância do bot
    bot = VidaFinanceiraBot(BOT_TOKEN)

    # Criar updater e dispatcher
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Armazenar instância do bot para uso nos handlers
    dispatcher.bot_data["bot_instance"] = bot

    # Adicionar handlers de comandos
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("add", add_lancamento_command))
    dispatcher.add_handler(CommandHandler("saldo", saldo_command))
    dispatcher.add_handler(CommandHandler("meta", meta_command))
    dispatcher.add_handler(CommandHandler("metas", listar_metas_command))
    dispatcher.add_handler(CommandHandler("relatorio", relatorio_command))
    dispatcher.add_handler(CommandHandler("grafico", grafico_command))
    dispatcher.add_handler(CommandHandler("exportar", exportar_command))
    dispatcher.add_handler(CommandHandler("limite", limite_command))
    dispatcher.add_handler(CommandHandler("limites", listar_limites_command))
    dispatcher.add_handler(CommandHandler("reset", reset_command))
    dispatcher.add_handler(CommandHandler("mes", mes_command))
    dispatcher.add_handler(CommandHandler("resetar_mes", resetar_mes_command))
    dispatcher.add_handler(CommandHandler("resetar_tudo", resetar_tudo_command))
    dispatcher.add_handler(CommandHandler("fixo", fixo_command))
    dispatcher.add_handler(CommandHandler("apagar", apagar_command))

    # Handler para botões inline
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # Iniciar o bot
    print("🚀 Bot iniciado! Pressione Ctrl+C para parar.")
    updater.start_polling()


# Handlers de comandos (serão implementados)
def start_command(update: Update, context: CallbackContext):
    """Comando /start - Boas-vindas"""
    user = update.effective_user
    update.message.reply_text(
        f"👋 Olá {user.first_name}!\n\n"
        "🎯 Bem-vindo ao seu Bot de Vida Financeira!\n\n"
        "📋 Comandos disponíveis:\n"
        "/help - Ver todos os comandos\n"
        "/add - Adicionar lançamento\n"
        "/saldo - Ver saldo atual\n"
        "/meta - Criar meta\n"
        "/metas - Listar metas\n\n"
        "💡 Exemplo: /add alimentação despesa 25,50 almoço no araujo"
    )


def resetar_mes_command(update: Update, context: CallbackContext):
    """Comando /resetar_mes - Zera os gastos do mês mantendo o saldo"""
    user = update.effective_user
    bot_instance = context.bot_data.get("bot_instance")

    if not bot_instance:
        update.message.reply_text("❌ Erro interno: bot_instance não encontrado")
        return

    # Calcula o saldo atual
    conn = sqlite3.connect(bot_instance.db_path)
    cursor = conn.cursor()

    hoje = date.today()
    mes_atual = hoje.strftime("%Y-%m")

    # Calcula saldo do mês
    cursor.execute(
        """
        SELECT COALESCE(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE -valor END), 0)
        FROM lancamentos
        WHERE user_id = ? AND strftime('%Y-%m', data_referencia) = ?
    """,
        (user.id, mes_atual),
    )

    saldo = cursor.fetchone()[0]

    # Backup dos lançamentos antes de apagar
    cursor.execute(
        """
        SELECT * FROM lancamentos
        WHERE user_id = ? AND strftime('%Y-%m', data_referencia) = ?
    """,
        (user.id, mes_atual),
    )

    backup = cursor.fetchall()

    # Apaga todos os lançamentos do mês
    cursor.execute(
        """
        DELETE FROM lancamentos
        WHERE user_id = ? AND strftime('%Y-%m', data_referencia) = ?
    """,
        (user.id, mes_atual),
    )

    # Se houver saldo positivo, cria um novo lançamento
    if saldo > 0:
        cursor.execute(
            """
            INSERT INTO lancamentos (user_id, tipo, valor, descricao, data_referencia)
            VALUES (?, 'receita', ?, 'Saldo do mês anterior', ?)
        """,
            (user.id, saldo, hoje),
        )

    conn.commit()
    conn.close()

    update.message.reply_text(
        f"✅ Mês resetado com sucesso!\n" f"💰 Saldo mantido: R$ {saldo:.2f}"
    )


def resetar_tudo_command(update: Update, context: CallbackContext):
    """Comando /resetar_tudo - Zera todos os dados com confirmação"""
    user = update.effective_user
    bot_instance = context.bot_data.get("bot_instance")

    if not context.args or context.args[0].lower() != "confirmar":
        update.message.reply_text(
            "⚠️ **ATENÇÃO**: Este comando irá apagar *TODOS* os seus dados!\n"
            "Para confirmar, digite:\n"
            "`/resetar_tudo confirmar`",
            parse_mode="Markdown",
        )
        return

    # Apaga todos os dados do usuário
    conn = sqlite3.connect(bot_instance.db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM lancamentos WHERE user_id = ?", (user.id,))
    cursor.execute("DELETE FROM metas WHERE user_id = ?", (user.id,))
    cursor.execute("DELETE FROM categorias WHERE user_id = ?", (user.id,))
    cursor.execute("DELETE FROM limites_gastos WHERE user_id = ?", (user.id,))

    conn.commit()
    conn.close()

    update.message.reply_text(
        "✅ Todos os dados foram resetados com sucesso!\n"
        "Use /start para começar novamente."
    )


def help_command(update: Update, context: CallbackContext):
    """Comando /help - Lista todos os comandos"""
    help_text = """
🤖 **Bot de Vida Financeira - Comandos**

📊 **Lançamentos:**
/add categoria, tipo, valor, descrição
Exemplo: /add alimentação, despesa, 25,50, almoço no araujo
Exemplo: /add salário, receita, 5000, trabalho freelance

📅 **Despesas Fixas:**
/fixo categoria, valor, quantidade_meses
Exemplo: /fixo aluguel, 1000, 12

🗑️ **Gerenciar Lançamentos:**
/apagar ID - Remove um lançamento pelo ID
/resetar_mes - Zera os gastos do mês mantendo o saldo
/resetar_tudo - Zera todos os dados com confirmação

💰 **Saldo e Relatórios:**
/saldo - Ver saldo atual
/mes MM-AAAA - Ver relatório mensal (ex: /mes 11-2025)
/relatorio - Relatório mensal completo
/grafico - Gráfico de gastos por categoria

🎯 **Metas Inteligentes:**
/meta Viagem de Casamento 20000 30-03-26
/meta Notebook Gamer 3000 15-12-24
/metas - Listar todas as metas

🎯 **Limites de Gastos:**
/limite alimentação 500
/limite transporte 200
/limites - Ver limites ultrapassados

📤 **Exportação:**
/exportar - Exportar dados em CSV

⚙️ **Configurações:**
/reset - Resetar todos os dados (com confirmação)

💡 **Dicas:**
• Use vírgulas para separar os campos: categoria, tipo, valor, descrição
• Use vírgula ou ponto para valores: 25,50 ou 25.50
• O bot reconhece categorias automaticamente
• Datas aceitas: 30-03-26, 30/03/2026
• Use /mes para ver os IDs dos lançamentos antes de apagar
    """
    update.message.reply_text(help_text)


def mes_command(update: Update, context: CallbackContext):
    """Comando /mes - Ver relatório de um mês específico"""
    user = update.effective_user
    bot_instance = context.bot_data.get("bot_instance")

    if not context.args:
        update.message.reply_text(
            "❌ Por favor, especifique o mês e ano no formato MM-AAAA\n"
            "Exemplo: /mes 11-2025"
        )
        return

    try:
        mes_ano = context.args[0]
        if not re.match(r"^\d{2}-\d{4}$", mes_ano):
            raise ValueError("Formato inválido")

        mes, ano = map(int, mes_ano.split("-"))
        if mes < 1 or mes > 12:
            raise ValueError("Mês inválido")

        # Cria a data do primeiro dia do mês especificado
        data_referencia = date(ano, mes, 1)

        # Busca os lançamentos do mês
        conn = sqlite3.connect(bot_instance.db_path)
        cursor = conn.cursor()

        # Calcula o saldo do mês
        cursor.execute(
            """
            SELECT COALESCE(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE -valor END), 0)
            FROM lancamentos
            WHERE user_id = ? AND strftime('%Y-%m', data_referencia) = ?
        """,
            (user.id, data_referencia.strftime("%Y-%m")),
        )
        saldo = cursor.fetchone()[0]

        # Busca receitas e despesas separadamente
        cursor.execute(
            """
            SELECT l.tipo, l.valor, l.descricao, c.nome as categoria,
                   l.parcela_atual, l.total_parcelas
            FROM lancamentos l
            LEFT JOIN categorias c ON l.categoria_id = c.id
            WHERE l.user_id = ? AND strftime('%Y-%m', l.data_referencia) = ?
            ORDER BY l.data_referencia, l.tipo DESC
        """,
            (user.id, data_referencia.strftime("%Y-%m")),
        )

        lancamentos = cursor.fetchall()
        conn.close()

        if not lancamentos:
            update.message.reply_text(
                f"📊 Não há lançamentos registrados em {calendar.month_name[mes]}/{ano}"
            )
            return

        # Formata a mensagem
        total_receitas = sum(l[1] for l in lancamentos if l[0] == "receita")
        total_despesas = sum(l[1] for l in lancamentos if l[0] == "despesa")

        mensagem = f"📊 **Relatório de {calendar.month_name[mes]}/{ano}**\n\n"

        # Receitas
        mensagem += "💰 **Receitas:**\n"
        for l in lancamentos:
            if l[0] == "receita":
                categoria = l[3] if l[3] else "Sem categoria"
                parcela_info = f" [{l[4]}/{l[5]}]" if l[4] and l[5] else ""
                mensagem += f"• {categoria}: R$ {l[1]:.2f}{parcela_info}\n"
        mensagem += f"**Total Receitas: R$ {total_receitas:.2f}**\n\n"

        # Despesas
        mensagem += "💸 **Despesas:**\n"
        for l in lancamentos:
            if l[0] == "despesa":
                categoria = l[3] if l[3] else "Sem categoria"
                parcela_info = f" [{l[4]}/{l[5]}]" if l[4] and l[5] else ""
                mensagem += f"• {categoria}: R$ {l[1]:.2f}{parcela_info}\n"
        mensagem += f"**Total Despesas: R$ {total_despesas:.2f}**\n\n"

        # Saldo
        mensagem += f"📈 **Saldo do Mês: R$ {saldo:.2f}**"

        update.message.reply_text(mensagem, parse_mode="Markdown")

    except ValueError as e:
        update.message.reply_text(
            "❌ Formato inválido! Use MM-AAAA\n" "Exemplo: /mes 11-2025"
        )
    except Exception as e:
        update.message.reply_text(
            "❌ Erro ao buscar relatório do mês.\n"
            "Certifique-se de usar o formato correto: MM-AAAA\n"
            "Exemplo: /mes 11-2025"
        )


def add_lancamento_command(update: Update, context: CallbackContext):
    """Comando /add - Adicionar lançamento com parsing inteligente"""
    user = update.effective_user
    texto_completo = update.message.text

    # Registrar usuário se não existir
    bot_instance = context.bot_data.get("bot_instance")
    if bot_instance:
        bot_instance.registrar_usuario(user.id, user.username, user.first_name)
        bot_instance.criar_conta_padrao(user.id)
        bot_instance.criar_responsavel_padrao(user.id, user.first_name)
        bot_instance.criar_metodo_pagamento_padrao(user.id)

        # Fazer parsing inteligente
        resultado = bot_instance.parser.parse_comando_add(texto_completo)

        if resultado["erro"]:
            update.message.reply_text(f"❌ {resultado['erro']}")
        else:
            # Adicionar lançamento
            sucesso = bot_instance.adicionar_lancamento(
                user.id,
                resultado["categoria"],
                resultado["tipo"],
                resultado["valor"],
                resultado["descricao"],
                user.first_name,  # Usar nome do usuário como responsável
                resultado["metodo_pagamento"],
            )

            if sucesso:
                emoji = "💰" if resultado["tipo"] == "receita" else "💸"
                update.message.reply_text(
                    f"{emoji} **Lançamento adicionado!**\n\n"
                    f"📊 Categoria: {resultado['categoria']}\n"
                    f"🏷️ Tipo: {resultado['tipo']}\n"
                    f"💵 Valor: R$ {resultado['valor']:.2f}\n"
                    f"👤 Responsável: {user.first_name}\n"
                    f"💳 Método: {resultado['metodo_pagamento']}\n"
                    f"📝 Descrição: {resultado['descricao']}\n\n"
                    f"✅ Saldo atualizado!"
                )
            else:
                update.message.reply_text(
                    "❌ Erro ao adicionar lançamento. Tente novamente."
                )
    else:
        update.message.reply_text("❌ Erro interno do bot. Tente novamente.")


def saldo_command(update: Update, context: CallbackContext):
    """Comando /saldo - Ver saldo atual"""
    user = update.effective_user

    bot_instance = context.bot_data.get("bot_instance")
    if bot_instance:
        saldo = bot_instance.obter_saldo(user.id)

        if saldo >= 0:
            emoji = "💰"
            status = "Positivo"
        else:
            emoji = "⚠️"
            status = "Negativo"

        update.message.reply_text(
            f"{emoji} **Saldo do Casal**\n\n"
            f"💵 Valor: R$ {saldo:.2f}\n"
            f"📊 Status: {status}\n\n"
            f"💡 Use /add para adicionar lançamentos"
        )
    else:
        update.message.reply_text("❌ Erro interno do bot. Tente novamente.")


def meta_command(update: Update, context: CallbackContext):
    """Comando /meta - Criar meta com parsing inteligente"""
    user = update.effective_user
    texto_completo = update.message.text

    bot_instance = context.bot_data.get("bot_instance")
    if bot_instance:
        # Fazer parsing inteligente
        resultado = bot_instance.parser.parse_comando_meta(texto_completo)

        if resultado["erro"]:
            update.message.reply_text(f"❌ {resultado['erro']}")
        else:
            # Adicionar meta
            sucesso = bot_instance.adicionar_meta(
                user.id, resultado["nome"], resultado["valor"], resultado["data_limite"]
            )

            if sucesso:
                data_info = (
                    f"\n📅 Prazo: {resultado['data_limite']}"
                    if resultado["data_limite"]
                    else ""
                )

                update.message.reply_text(
                    f"🎯 **Meta criada!**\n\n"
                    f"📝 Nome: {resultado['nome']}\n"
                    f"💰 Valor: R$ {resultado['valor']:.2f}{data_info}\n\n"
                    f"✅ Use /metas para ver todas as metas"
                )
            else:
                update.message.reply_text("❌ Erro ao criar meta. Tente novamente.")
    else:
        update.message.reply_text("❌ Erro interno do bot. Tente novamente.")


def listar_metas_command(update: Update, context: CallbackContext):
    """Comando /metas - Listar todas as metas"""
    user = update.effective_user

    bot_instance = context.bot_data.get("bot_instance")
    if bot_instance:
        metas = bot_instance.listar_metas(user.id)

        if not metas:
            update.message.reply_text(
                "🎯 **Suas Metas**\n\n"
                "📝 Nenhuma meta encontrada.\n\n"
                "💡 Use /meta para criar uma nova meta!\n"
                "Exemplo: /meta Viagem de Casamento 20000 30-03-26"
            )
        else:
            texto_metas = "🎯 **Suas Metas**\n\n"

            for meta in metas:
                progresso = (
                    (meta["valor_atual"] / meta["valor_meta"]) * 100
                    if meta["valor_meta"] > 0
                    else 0
                )
                barra_progresso = "█" * int(progresso / 10) + "░" * (
                    10 - int(progresso / 10)
                )

                data_info = (
                    f"\n📅 Prazo: {meta['data_limite']}" if meta["data_limite"] else ""
                )

                texto_metas += (
                    f"📝 **{meta['nome']}**\n"
                    f"💰 Meta: R$ {meta['valor_meta']:.2f}\n"
                    f"📊 Atual: R$ {meta['valor_atual']:.2f}\n"
                    f"📈 Progresso: {progresso:.1f}%\n"
                    f"`{barra_progresso}`{data_info}\n\n"
                )

            update.message.reply_text(texto_metas)
    else:
        update.message.reply_text("❌ Erro interno do bot. Tente novamente.")


def fixo_command(update: Update, context: CallbackContext):
    """Comando /fixo - Adiciona despesa fixa com repetição por até 12 meses"""
    if not context.args or len(context.args) < 3:
        update.message.reply_text(
            "❌ Uso incorreto. Use:\n"
            "/fixo categoria, valor, quantidade_meses\n"
            "Exemplo: /fixo aluguel, 1000, 12"
        )
        return

    entrada = " ".join(context.args).split(",")
    if len(entrada) < 3:
        update.message.reply_text(
            "❌ Use o formato correto separando por vírgulas:\n"
            "/fixo categoria, valor, quantidade_meses\n"
            "Exemplo: /fixo aluguel, 1000, 12"
        )
        return

    user = update.effective_user
    bot_instance = context.bot_data.get("bot_instance")
    if not bot_instance:
        update.message.reply_text("❌ Erro interno do bot")
        return

    categoria = entrada[0].strip()
    try:
        valor = float(entrada[1].strip().replace("R$", "").replace(" ", ""))
    except ValueError:
        update.message.reply_text("❌ Valor inválido")
        return

    try:
        meses = int(entrada[2].strip())
        if meses < 1 or meses > 12:
            update.message.reply_text("❌ Quantidade de meses deve ser entre 1 e 12")
            return
    except ValueError:
        update.message.reply_text("❌ Quantidade de meses inválida")
        return

    # Adiciona lançamentos fixos
    conn = sqlite3.connect(bot_instance.db_path)
    cursor = conn.cursor()

    hoje = date.today()

    # Registra lançamentos para os próximos meses
    for i in range(meses):
        data_ref = hoje.replace(day=1) + timedelta(days=32 * i)
        data_ref = data_ref.replace(day=1)  # Primeiro dia do mês

        cursor.execute(
            """
            INSERT INTO lancamentos (
                user_id, tipo, valor, descricao, data_referencia,
                fixo_parcelas, fixo_parcela_atual
            )
            VALUES (?, 'despesa', ?, ?, ?, ?, ?)
            """,
            (user.id, valor, f"{categoria} (Fixo)", data_ref, meses, i + 1),
        )

    conn.commit()
    conn.close()

    update.message.reply_text(
        f"✅ Despesa fixa adicionada!\n\n"
        f"📊 Categoria: {categoria}\n"
        f"💵 Valor: R$ {valor:.2f}\n"
        f"🔄 Repetição: {meses} meses\n"
    )


def apagar_command(update: Update, context: CallbackContext):
    """Comando /apagar - Remove um lançamento pelo ID"""
    if not context.args:
        update.message.reply_text(
            "❌ Informe o ID do lançamento\n"
            "Exemplo: /apagar 123\n"
            "Use /mes para ver os lançamentos e seus IDs"
        )
        return

    try:
        lancamento_id = int(context.args[0])
    except ValueError:
        update.message.reply_text("❌ ID inválido")
        return

    user = update.effective_user
    bot_instance = context.bot_data.get("bot_instance")

    if not bot_instance:
        update.message.reply_text("❌ Erro interno do bot")
        return

    # Busca o lançamento
    conn = sqlite3.connect(bot_instance.db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT l.*, c.nome as categoria
        FROM lancamentos l
        LEFT JOIN categorias c ON l.categoria_id = c.id
        WHERE l.id = ? AND l.user_id = ?
        """,
        (lancamento_id, user.id),
    )

    lancamento = cursor.fetchone()

    if not lancamento:
        update.message.reply_text("❌ Lançamento não encontrado ou não pertence a você")
        conn.close()
        return

    # Remove o lançamento
    cursor.execute(
        "DELETE FROM lancamentos WHERE id = ? AND user_id = ?", (lancamento_id, user.id)
    )

    conn.commit()
    conn.close()

    update.message.reply_text(
        f"✅ Lançamento removido!\n\n"
        f"🆔 ID: {lancamento_id}\n"
        f"📊 Categoria: {lancamento['categoria']}\n"
        f"💵 Valor: R$ {lancamento['valor']:.2f}\n"
    )


def relatorio_command(update: Update, context: CallbackContext):
    """Comando /relatorio - Relatório mensal"""
    user = update.effective_user

    bot_instance = context.bot_data.get("bot_instance")
    if bot_instance:
        lancamentos = bot_instance.obter_lancamentos_por_periodo(user.id, "mes_atual")
        resumo = bot_instance.obter_resumo_por_categoria(user.id, "mes_atual")

        if not lancamentos:
            update.message.reply_text(
                "📊 **Relatório Mensal**\n\n"
                "📝 Nenhum lançamento encontrado para este mês.\n\n"
                "💡 Use /add para adicionar lançamentos!"
            )
        else:
            # Calcular totais
            total_receitas = sum(dados["receita"] for dados in resumo.values())
            total_despesas = sum(dados["despesa"] for dados in resumo.values())
            saldo_mensal = total_receitas - total_despesas

            # Montar relatório
            relatorio = f"📊 **Relatório Mensal do Casal**\n\n"
            relatorio += f"💰 **Receitas:** R$ {total_receitas:.2f}\n"
            relatorio += f"💸 **Despesas:** R$ {total_despesas:.2f}\n"
            relatorio += f"📈 **Saldo:** R$ {saldo_mensal:.2f}\n\n"

            relatorio += "📋 **Por Categoria:**\n"
            for categoria, dados in resumo.items():
                if dados["receita"] > 0 or dados["despesa"] > 0:
                    relatorio += f"• {categoria}: "
                    if dados["receita"] > 0:
                        relatorio += f"💰 R$ {dados['receita']:.2f} "
                    if dados["despesa"] > 0:
                        relatorio += f"💸 R$ {dados['despesa']:.2f}"
                    relatorio += "\n"

            # Mostrar últimos lançamentos com responsáveis
            if lancamentos:
                relatorio += "\n📝 **Últimos Lançamentos:**\n"
                for lancamento in lancamentos[:5]:  # Mostrar apenas os 5 últimos
                    emoji_lanc = "💰" if lancamento["tipo"] == "receita" else "💸"
                    relatorio += f"{emoji_lanc} {lancamento['responsavel']}: R$ {lancamento['valor']:.2f} - {lancamento['descricao']}\n"

            update.message.reply_text(relatorio)
    else:
        update.message.reply_text("❌ Erro interno do bot. Tente novamente.")


def grafico_command(update: Update, context: CallbackContext):
    """Comando /grafico - Gerar gráfico de gastos"""
    user = update.effective_user

    bot_instance = context.bot_data.get("bot_instance")
    if bot_instance:
        grafico_texto = bot_instance.criar_grafico_gastos(user.id)

        if (
            grafico_texto
            and grafico_texto != "📊 Nenhum gasto encontrado para criar gráfico."
        ):
            update.message.reply_text(
                f"{grafico_texto}\n" "💡 Use /relatorio para ver detalhes!"
            )
        else:
            update.message.reply_text(
                "📊 **Gráfico de Gastos**\n\n"
                "📝 Nenhum gasto encontrado para criar gráfico.\n\n"
                "💡 Use /add para adicionar lançamentos!"
            )
    else:
        update.message.reply_text("❌ Erro interno do bot. Tente novamente.")


def exportar_command(update: Update, context: CallbackContext):
    """Comando /exportar - Exportar dados em CSV"""
    user = update.effective_user

    bot_instance = context.bot_data.get("bot_instance")
    if bot_instance:
        filename = bot_instance.exportar_csv(user.id)

        if filename:
            try:
                with open(filename, "rb") as document:
                    update.message.reply_document(
                        document=document,
                        filename=f"dados_financeiros_{user.first_name}.csv",
                        caption="📤 **Dados Exportados!**\n\n"
                        "📊 Arquivo CSV com todos os seus lançamentos.\n"
                        "💡 Pode ser aberto no Excel ou Google Sheets.",
                    )
                # Limpar arquivo temporário
                os.remove(filename)
            except Exception as e:
                update.message.reply_text("❌ Erro ao enviar arquivo. Tente novamente.")
        else:
            update.message.reply_text(
                "📤 **Exportação de Dados**\n\n"
                "📝 Nenhum lançamento encontrado para exportar.\n\n"
                "💡 Use /add para adicionar lançamentos!"
            )
    else:
        update.message.reply_text("❌ Erro interno do bot. Tente novamente.")


def limite_command(update: Update, context: CallbackContext):
    """Comando /limite - Definir limite de gastos"""
    user = update.effective_user
    args = context.args

    if len(args) < 2:
        update.message.reply_text(
            "⚠️ **Uso:** /limite [categoria] [valor]\n\n"
            "📝 Exemplos:\n"
            "• /limite alimentação 500\n"
            "• /limite transporte 200\n"
            "• /limite lazer 300"
        )
        return

    categoria = args[0]
    try:
        valor_limite = float(args[1].replace(",", "."))

        bot_instance = context.bot_data.get("bot_instance")
        if bot_instance:
            sucesso = bot_instance.adicionar_limite_gasto(
                user.id, categoria, valor_limite
            )

            if sucesso:
                update.message.reply_text(
                    f"🎯 **Limite Definido!**\n\n"
                    f"📊 Categoria: {categoria}\n"
                    f"💰 Limite: R$ {valor_limite:.2f}\n\n"
                    f"✅ Use /limites para ver todos os limites"
                )
            else:
                update.message.reply_text("❌ Erro ao definir limite. Tente novamente.")
        else:
            update.message.reply_text("❌ Erro interno do bot. Tente novamente.")

    except ValueError:
        update.message.reply_text("❌ Valor inválido. Use números como: 500 ou 500,50")


def listar_limites_command(update: Update, context: CallbackContext):
    """Comando /limites - Listar limites de gastos"""
    user = update.effective_user

    bot_instance = context.bot_data.get("bot_instance")
    if bot_instance:
        limites_ultrapassados = bot_instance.verificar_limites(user.id)

        if limites_ultrapassados:
            texto = "⚠️ **Limites Ultrapassados!**\n\n"
            for limite in limites_ultrapassados:
                texto += (
                    f"🚨 **{limite['categoria']}**\n"
                    f"💰 Limite: R$ {limite['limite']:.2f}\n"
                    f"💸 Gasto: R$ {limite['gasto_atual']:.2f}\n"
                    f"📈 Excesso: R$ {limite['excesso']:.2f}\n\n"
                )
            update.message.reply_text(texto)
        else:
            update.message.reply_text(
                "🎯 **Limites de Gastos**\n\n"
                "✅ Nenhum limite ultrapassado!\n\n"
                "💡 Use /limite para definir novos limites:\n"
                "• /limite alimentação 500\n"
                "• /limite transporte 200"
            )
    else:
        update.message.reply_text("❌ Erro interno do bot. Tente novamente.")


def reset_command(update: Update, context: CallbackContext):
    """Comando /reset - Resetar todos os dados"""
    user = update.effective_user

    # Criar teclado de confirmação
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Sim, resetar", callback_data=f"reset_confirm_{user.id}"
            ),
            InlineKeyboardButton("❌ Cancelar", callback_data="reset_cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "⚠️ **ATENÇÃO!**\n\n"
        "🗑️ Esta ação irá **DELETAR TODOS** os seus dados:\n"
        "• Lançamentos\n"
        "• Metas\n"
        "• Limites\n"
        "• Categorias\n"
        "• Contas\n\n"
        "❌ **Esta ação NÃO pode ser desfeita!**\n\n"
        "🤔 Tem certeza que deseja continuar?",
        reply_markup=reply_markup,
    )


def button_callback(update: Update, context: CallbackContext):
    """Handler para botões inline"""
    query = update.callback_query
    query.answer()

    if query.data.startswith("reset_confirm_"):
        user_id = int(query.data.split("_")[2])

        bot_instance = context.bot_data.get("bot_instance")
        if bot_instance:
            sucesso = bot_instance.resetar_dados(user_id)

            if sucesso:
                query.edit_message_text(
                    "🗑️ **Dados Resetados!**\n\n"
                    "✅ Todos os seus dados foram deletados.\n"
                    "🆕 Use /start para começar novamente!"
                )
            else:
                query.edit_message_text("❌ Erro ao resetar dados. Tente novamente.")
        else:
            query.edit_message_text("❌ Erro interno do bot. Tente novamente.")

    elif query.data == "reset_cancel":
        query.edit_message_text("❌ Reset cancelado. Seus dados estão seguros!")


def relatorio_command(update: Update, context: CallbackContext):
    """Gera relatório mensal em CSV"""
    try:
        if not context.args or len(context.args) != 1:
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
        else:
            mes_ano = context.args[0]
            mes_atual, ano_atual = map(int, mes_ano.split("-"))

        filepath = gerar_relatorio_mensal(
            update.effective_user.id, mes_atual, ano_atual
        )

        with open(filepath, "rb") as f:
            update.message.reply_document(
                document=f,
                filename=f"relatorio_{mes_atual:02d}_{ano_atual}.csv",
                caption=f"📊 Relatório financeiro de {mes_atual:02d}/{ano_atual}",
            )
    except Exception as e:
        update.message.reply_text(f"Erro ao gerar relatório: {str(e)}")


def mes_command(update: Update, context: CallbackContext):
    """Visualiza gastos de um mês específico"""
    if not context.args or len(context.args) != 1:
        update.message.reply_text("Use: /mes MM-YYYY (exemplo: /mes 11-2025)")
        return

    try:
        mes_ano = context.args[0]
        mes, ano = map(int, mes_ano.split("-"))

        conn = get_database_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT l.*, c.nome as categoria, r.nome as responsavel
            FROM lancamentos l
            LEFT JOIN categorias c ON l.categoria_id = c.id
            LEFT JOIN responsaveis r ON l.responsavel_id = r.id
            WHERE l.user_id = ? 
            AND strftime('%m', l.data_referencia) = ? 
            AND strftime('%Y', l.data_referencia) = ?
            ORDER BY l.data_lancamento
        """,
            (update.effective_user.id, f"{mes:02d}", str(ano)),
        )

        lancamentos = cursor.fetchall()

        if not lancamentos:
            update.message.reply_text(
                f"Nenhum lançamento encontrado para {mes:02d}/{ano}"
            )
            return

        mensagem = f"📅 Lançamentos de {mes:02d}/{ano}:\n\n"
        total_receitas = 0
        total_despesas = 0

        for l in lancamentos:
            valor = l["valor"]
            if l["tipo"] == "receita":
                total_receitas += valor
            else:
                total_despesas += valor

            parcela_info = (
                f" [{l['parcela_atual']}/{l['total_parcelas']}]"
                if l["total_parcelas"]
                else ""
            )
            mensagem += (
                f"{'💰' if l['tipo'] == 'receita' else '💸'} "
                f"{l['categoria']}: R$ {valor:.2f}{parcela_info}\n"
                f"📝 {l['descricao']}\n\n"
            )

        saldo = total_receitas - total_despesas
        mensagem += (
            f"📊 Resumo:\n"
            f"📈 Receitas: R$ {total_receitas:.2f}\n"
            f"📉 Despesas: R$ {total_despesas:.2f}\n"
            f"💰 Saldo: R$ {saldo:.2f}"
        )

        update.message.reply_text(mensagem)
        conn.close()

    except ValueError:
        update.message.reply_text("Formato inválido. Use MM-YYYY (exemplo: 11-2025)")
    except Exception as e:
        update.message.reply_text(f"Erro ao buscar lançamentos: {str(e)}")


if __name__ == "__main__":
    main()
