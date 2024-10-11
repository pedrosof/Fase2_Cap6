import cx_Oracle
cx_Oracle.init_oracle_client(lib_dir="/Users/pedrosof/Downloads/instantclient_23_3")
import requests
import json
from configparser import ConfigParser
from datetime import datetime
import locale

# Função para conectar ao banco de dados Oracle
def conectar_banco():
    dsn_tns = cx_Oracle.makedsn('oracle.fiap.com.br', '1521', service_name='ORCL')
    conn = cx_Oracle.connect(user='rm560665', password='280678', dsn=dsn_tns)
    return conn

# Função para carregar as configurações do arquivo
def carregar_configuracoes():
    config = ConfigParser()
    try:
        # Tente ler o arquivo de configuração, ajuste o caminho se necessário
        config.read('config_plantio_colheita.txt')  # Caminho relativo ou absoluto, conforme necessário
        return config
    except Exception as e:
        print(f"Erro ao carregar o arquivo de configuração: {e}")
        return None

def inserir_dados_solo(cursor, conn, dados_solo):
    # Inserir os dados no banco de dados
    insert_sql = """
    INSERT INTO Solo (Numero_Amostras, Data_Amostra, Nutriente_N, Nutriente_P, Nutriente_K, Umidade_Solo, pH_Solo, Temperatura_Solo)
    VALUES (:1, TO_DATE(:2, 'YYYY-MM-DD'), :3, :4, :5, :6, :7, :8)
    """
    cursor.execute(insert_sql, dados_solo)
    conn.commit()
    
    print("Dados de solo inseridos com sucesso.")


def coletar_dados_solo():
    try:
        num_amostras = int(input("Digite o número de amostras: "))
        data_amostra = input("Digite a data da amostra (YYYY-MM-DD): ")
        nutriente_n = float(input("Digite o nível de Nitrogênio (N): "))
        nutriente_p = float(input("Digite o nível de Fósforo (P): "))
        nutriente_k = float(input("Digite o nível de Potássio (K): "))
        umidade = float(input("Digite o nível de umidade do solo: "))
        ph = float(input("Digite o pH do solo: "))
        temperatura = float(input("Digite a temperatura do solo: "))

        # Retornar os dados em um formato esperado para o SQL
        return (num_amostras, data_amostra, nutriente_n, nutriente_p, nutriente_k, umidade, ph, temperatura)
    
    except ValueError as e:
        print(f"Erro de valor inválido: {e}")
        return None


# Função para listar as amostras de solo e analisar um ID específico
def listar_amostras_solo(cursor):
    # Executar consulta para listar todas as amostras de solo
    cursor.execute("SELECT ID_Solo, Data_Amostra, Umidade_Solo, pH_Solo, Temperatura_Solo FROM Solo")
    
    # Buscar todos os resultados
    amostras = cursor.fetchall()

    # Verificar se há amostras retornadas
    if amostras:
        print("\nAmostras de Solo Disponíveis:")
        
        # Listar todas as amostras retornadas
        for amostra in amostras:
            print(f"ID_Solo: {amostra[0]}, Data da Amostra: {amostra[1]}, Umidade: {amostra[2]}%, pH: {amostra[3]}, Temperatura: {amostra[4]}°C")
        
        # Solicitar ao usuário que selecione um ID_Solo para análise
        try:
            id_solo = int(input("\nDigite o ID_Solo para análise: "))
            analisar_solo_por_id(cursor, id_solo)  # Verifica se o ID digitado existe na tabela
        except ValueError:
            print("Erro: Por favor, insira um ID_Solo válido.")
    else:
        print("Nenhuma amostra de solo disponível.")

# Função para analisar uma amostra de solo específica com base no ID_Solo e nas configurações
from datetime import datetime

def analisar_solo_por_id(cursor, id_solo):
    # Dicionário para mapear os meses de inglês para português
    meses_map = {
        'january': 'janeiro',
        'february': 'fevereiro',
        'march': 'março',
        'april': 'abril',
        'may': 'maio',
        'june': 'junho',
        'july': 'julho',
        'august': 'agosto',
        'september': 'setembro',
        'october': 'outubro',
        'november': 'novembro',
        'december': 'dezembro'
    }

    # Carregar as configurações
    config = carregar_configuracoes()

    if config is None:
        print("Não foi possível carregar o arquivo de configuração.")
        return

    # Verificar se a chave 'Mes_Ideal_Plantio' está presente nas configurações
    try:
        meses_ideais_plantio = [mes.strip().lower() for mes in config['Solo']['Mes_Ideal_Plantio'].split(',')]
        #print(f"Meses Ideais para Plantio: {meses_ideais_plantio}")
    except KeyError:
        print("Erro: 'Mes_Ideal_Plantio' não encontrado no arquivo de configuração.")
        return

    # Executar consulta para buscar o ID_Solo selecionado
    cursor.execute("SELECT * FROM Solo WHERE ID_Solo = :id", {'id': id_solo})
    resultado = cursor.fetchone()

    # Verificar se a amostra foi encontrada
    if resultado:
        _, num_amostras, data_amostra, nutriente_n, nutriente_p, nutriente_k, umidade, ph, temp = resultado
        
        print(f"\nAnalisando o Solo com ID {id_solo}:")
        print(f"Data da Amostra: {data_amostra}")
        print(f"Nitrogênio (N): {nutriente_n}")
        print(f"Fósforo (P): {nutriente_p}")
        print(f"Potássio (K): {nutriente_k}")
        print(f"Umidade: {umidade}%")
        print(f"pH: {ph}")
        print(f"Temperatura: {temp}°C")

        # Verificar se o mês da amostra está no mês ideal de plantio
        mes_amostra_en = datetime.strptime(str(data_amostra), '%Y-%m-%d %H:%M:%S').strftime('%B').lower()
        mes_amostra = meses_map.get(mes_amostra_en)  # Traduzir para português usando o dicionário
        print(f"Mês da Amostra: {mes_amostra}")

        correcao = []

        # Verificar os parâmetros de solo com base nas configurações

        # Verificar Umidade
        if umidade < float(config['Solo']['Umidade_Minima']):
            correcao.append('Aumentar Umidade do Solo')
        elif umidade > float(config['Solo']['Umidade_Maxima']):
            correcao.append('Baixar Umidade do Solo')

        # Verificar Nitrogênio
        if nutriente_n < float(config['Solo']['Nutrientes_N_Minimo']):
            correcao.append('Aumentar Nitrogênio do Solo')
        elif nutriente_n > float(config['Solo']['Nutrientes_N_Maximo']):
            correcao.append('Baixar Nitrogênio do Solo')

        # Verificar Fósforo
        if nutriente_p < float(config['Solo']['Nutrientes_P_Minimo']):
            correcao.append('Aumentar Fósforo do Solo')
        elif nutriente_p > float(config['Solo']['Nutrientes_P_Maximo']):
            correcao.append('Baixar Fósforo do Solo')

        # Verificar Potássio
        if nutriente_k < float(config['Solo']['Nutrientes_K_Minimo']):
            correcao.append('Aumentar Potássio do Solo')
        elif nutriente_k > float(config['Solo']['Nutrientes_K_Maximo']):
            correcao.append('Baixar Potássio do Solo')

        # Verificar pH
        if ph < float(config['Solo']['pH_Minimo']):
            correcao.append('Aumentar pH do Solo')
        elif ph > float(config['Solo']['pH_Maximo']):
            correcao.append('Diminuir pH do Solo')

        # Verificar Temperatura
        if temp < float(config['Solo']['Temperatura_Minima']):
            correcao.append('Aumentar Temperatura do Solo')
        elif temp > float(config['Solo']['Temperatura_Maxima']):
            correcao.append('Diminuir Temperatura do Solo')

        # Exibir resultado com base no mês
        if not correcao:
            if mes_amostra in meses_ideais_plantio:
                print(f"O solo com ID {id_solo} está bom para plantio.")
            else:
                print(f"O solo está regulado, mas o mês não é bom para o cultivo.")
        else:
            print(f"Sugestão de Correção para o Solo com ID {id_solo}: {', '.join(correcao)}")
    else:
        print(f"Nenhuma amostra encontrada com o ID_Solo {id_solo}.")


# Função para coletar dados climáticos do OpenWeatherMap
def coletar_dados_climaticos(cidade, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Erro ao coletar dados climáticos. Status code: {response.status_code}")
        return None


# Função para inserir dados nas tabelas
def inserir_dados_climaticos(cursor, dados_clima):
    sql = """
        INSERT INTO Condicoes_Climaticas (Data_Coleta, Temperatura, Clima, Umidade)
        VALUES (:1, :2, :3, :4)
    """
    data_coleta = datetime.now()
    temperatura = dados_clima['main']['temp']
    clima = dados_clima['weather'][0]['description']
    umidade = dados_clima['main']['humidity']
    cursor.execute(sql, (data_coleta, temperatura, clima, umidade))

def inserir_dados_planta(cursor, conn):
    try:
        # Solicitar os dados do usuário
        num_amostras = int(input("Digite o número de amostras: "))

        # Data da amostra será a data atual
        data_amostra = datetime.now().strftime('%Y-%m-%d')

        # Solicitar e validar a cor da planta
        cores_validas = ['verde claro', 'verde escuro', 'roxo esverdeado', 'amarelo']
        cor_plantas = input(f"Digite a cor da planta ({', '.join(cores_validas)}): ").lower()
    
        if cor_plantas not in cores_validas:
            print("Cor inválida! As cores válidas são: verde claro, verde escuro, roxo esverdeado, amarelo.")
            return None

        # Solicitar altura da planta
        altura_plantas = float(input("Digite a altura da planta (em metros): "))

        # Solicitar e validar os valores de Brix
        brix_alta = float(input("Digite o valor do Brix da parte alta (0 a 20): "))
        brix_meio = float(input("Digite o valor do Brix da parte do meio (0 a 20): "))
        brix_baixa = float(input("Digite o valor do Brix da parte baixa (0 a 20): "))
    
        # Validar se o Brix está dentro da faixa correta
        if not (0 <= brix_alta <= 20) or not (0 <= brix_meio <= 20) or not (0 <= brix_baixa <= 20):
            print("Os valores de Brix devem estar entre 0 e 20.")
            return None

        # Calcular o Brix Médio
        brix_medio = (brix_alta + brix_meio + brix_baixa) / 3

        # Inserir os dados no banco de dados
        insert_sql = """
        INSERT INTO Plantas (Numero_Amostras, Data_Amostra, Cor_Plantas, Altura_Plantas, Brix_Alta, Brix_Meio, Brix_Baixa, Brix_Medio)
        VALUES (:1, TO_DATE(:2, 'YYYY-MM-DD'), :3, :4, :5, :6, :7, :8)
        """
        cursor.execute(insert_sql, (num_amostras, data_amostra, cor_plantas, altura_plantas, brix_alta, brix_meio, brix_baixa, brix_medio))
        conn.commit()

        print(f"Dados da planta inseridos com sucesso. Data da amostra: {data_amostra}")
        return True

    except ValueError as e:
        print(f"Erro de valor inválido: {e}")
        return None

def listar_amostras_plantas(cursor):
    # Executar consulta para listar todas as amostras de plantas
    cursor.execute("SELECT ID_Planta, Data_Amostra, Cor_Plantas, Brix_Medio FROM Plantas")
    
    amostras = cursor.fetchall()

    if amostras:
        print("\nAmostras de Plantas Disponíveis:")
        for amostra in amostras:
            print(f"ID_Planta: {amostra[0]}, Data da Amostra: {amostra[1]}, Cor: {amostra[2]}, Brix Médio: {amostra[3]}")

        # Solicitar ID_Planta para análise
        id_planta = int(input("\nDigite o ID_Planta para análise: "))
        analisar_planta_por_id(cursor, id_planta)
    else:
        print("Nenhuma amostra de planta disponível.")

def analisar_planta_por_id(cursor, id_planta):
    # Executar consulta para buscar a planta com o ID fornecido
    cursor.execute("SELECT * FROM Plantas WHERE ID_Planta = :id", {'id': id_planta})
    planta = cursor.fetchone()

    if planta:
        _, num_amostras, data_amostra, cor_plantas, altura_plantas, brix_alta, brix_meio, brix_baixa, brix_medio = planta
        
        print(f"\nAnalisando a Planta com ID {id_planta}:")
        print(f"Data da Amostra: {data_amostra}")
        print(f"Cor da Planta: {cor_plantas}")
        print(f"Altura da Planta: {altura_plantas} metros")
        print(f"Brix - Alta: {brix_alta}, Meio: {brix_meio}, Baixa: {brix_baixa}, Médio: {brix_medio}")
        
        # Verificar se a planta está pronta para colheita
        if brix_medio == 18 and cor_plantas == 'roxo esverdeado':
            print("A planta está pronta para colheita (Brix Médio 18 e cor 'roxo esverdeado').")
        else:
            print("A planta ainda não está pronta para colheita.")
    else:
        print(f"Nenhuma planta encontrada com o ID {id_planta}.")

# Menu principal atualizado
def menu_principal():
    config = carregar_configuracoes()  # Carrega as configurações uma vez no início
    conn = conectar_banco()
    cursor = conn.cursor()

    while True:
        print("\nMenu:")
        print("1. Inserir dados de Solo para Plantio")
        print("2. Listar Amostras de Solo e Analisar por ID")
        print("3. Inserir Dados de Planta")
        print("4. Listar Amostras de Plantas e Analisar por ID")
        print("5. Sair")
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            # Inserir dados de solo
            dados_solo = coletar_dados_solo()
            if dados_solo:
                inserir_dados_solo(cursor, dados_solo)
        elif escolha == '2':
            listar_amostras_solo(cursor)
        elif escolha == '3':
            # Inserir dados de planta com verificação
            if inserir_dados_planta(cursor, conn):
                print("Dados de planta inseridos com sucesso!")
            else:
                print("Falha ao inserir dados da planta.")
        elif escolha == '4':
            listar_amostras_plantas(cursor)
        elif escolha == '5':
            break
        else:
            print("Opção inválida. Tente novamente.")

    cursor.close()
    conn.close()



if __name__ == "__main__":
    menu_principal()
