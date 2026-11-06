"""
Fase 1: Ingestão de Dados e Engenharia Relacional
Projeto: Graph Analytics & AML (Anti-Money Laundering)
Descrição: Lê o dataset bruto da IBM em chunks para evitar estouro de memória (RAM) e persiste de forma relacional indexada em um banco SQLite.
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

# Caminhos dos arquivos
DB_PATH = "../data/aml_network.db"
TRANS_CSV = "../data/HI-Small_Trans.csv"
ACCOUNTS_CSV = "../data/HI-Small_accounts.csv"  

def criar_banco_e_ingerir():
    inicio_total = datetime.now()
    print(f"[{inicio_total}] Início do processo de ingestão de dados...")

    # Conectando ao SQLite (cria o arquivo se não existir)
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Ingestão do arquivo de Transações em Chunks
    if os.path.exists(TRANS_CSV):
        print(f"Lendo transações de '{TRANS_CSV}' em blocos...")
        chunk_size = 100_000  # 100 mil linhas por bloco
        total_linhas = 0
        
        for i, chunk in enumerate(pd.read_csv(TRANS_CSV, chunksize=chunk_size)):
            # Normalizando nomes de colunas para evitar espaços ou caracteres especiais
            chunk.columns = [c.strip().replace(" ", "_").replace("(", "").replace(")", "") for c in chunk.columns]
            
            # Gravando no SQLite (substitui na primeira iteração, anexa nas seguintes)
            modo = "replace" if i == 0 else "append"
            chunk.to_sql("transacoes", conn, if_exists=modo, index=False)
            
            total_linhas += len(chunk)
            print(f"-> Bloco {i+1} processado. Total acumulado: {total_linhas:,} linhas.")
        
        print(f"Transações importadas com sucesso! Total geral: {total_linhas:,} registros.")
    else:
        print(f"Arquivo de transações não encontrado em: {TRANS_CSV}")

    # 2. Ingestão do cadastro de contas (se disponível)
    if os.path.exists(ACCOUNTS_CSV):
        print(f"Lendo cadastro de contas de '{ACCOUNTS_CSV}'...")
        df_accounts = pd.read_csv(ACCOUNTS_CSV)
        df_accounts.columns = [c.strip().replace(" ", "_") for c in df_accounts.columns]
        df_accounts.to_sql("contas", conn, if_exists="replace", index=False)
        print(f" Contas importadas com sucesso! Total: {len(df_accounts):,} registros.")
    else:
        print(f"ℹArquivo de contas não encontrado (opcional). Prosseguindo apenas com transações.")

    # 3. Criando índices para otimizar as consultas de grafos no SQLite
    print("Criando índices de performance nas colunas de origem e destino...")
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_origem ON transacoes (From_Bank, Account);")
    # Nota: Ajuste os nomes das colunas conforme o cabeçalho exato do seu CSV da IBM
    conn.commit()
    conn.close()

    fim_total = datetime.now()
    print(f"[{fim_total}] Ingestão concluída com sucesso em {(fim_total - inicio_total).seconds} segundos!")

if __name__ == "__main__":
    criar_banco_e_ingerir()