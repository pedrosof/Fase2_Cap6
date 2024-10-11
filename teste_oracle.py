import cx_Oracle
cx_Oracle.init_oracle_client(lib_dir="/Users/pedrosof/Downloads/instantclient_23_3")


def conectar_banco():
    # Configurar os detalhes da conexão
    dsn_tns = cx_Oracle.makedsn('oracle.fiap.com.br', '1521', service_name='ORCL')
    conn = cx_Oracle.connect(user='rm560665', password='280678', dsn=dsn_tns)
    return conn

def executar_select(cursor):
    # Executar a consulta SQL
    cursor.execute("SELECT * FROM Solo")
    
    # Buscar todos os resultados
    resultados = cursor.fetchall()

    # Exibir os resultados
    for linha in resultados:
        print(linha)

# Script principal
def main():
    conn = conectar_banco()
    cursor = conn.cursor()

    try:
        executar_select(cursor)  # Executar a função que faz o SELECT
    finally:
        cursor.close()  # Fechar o cursor
        conn.close()    # Fechar a conexão

if __name__ == "__main__":
    main()
