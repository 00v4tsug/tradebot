import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz  # Importe a biblioteca pytz
import time

def enviar_email(subject):
    sender_email = ""
    receiver_email = ""
    password = ""

    message = MIMEMultipart()
    message["From"] = ""
    message["To"] = ""
    message["Subject"] = "Atualização do mercado financeiro de criptomoedas"

    # Escolha o símbolo e a cor com base no tipo de sinal
    if tipo_sinal == 'compra':
        symbol = '🔴'  # Símbolo vermelho para compra
        color = 'red'
    elif tipo_sinal == 'venda':
        symbol = '🟢'  # Símbolo verde para venda
        color = 'green'
    elif tipo_sinal == 'sobrevenda':
        symbol = '🔵'  # Símbolo azul para sobrevenda
        color = 'blue'
    else:
        symbol = ''  # Símbolo vazio por padrão
        color = 'black'  # Cor preta por padrão

    # Adicione o símbolo ao corpo do e-mail
    body = f"<p style='color:{color}; font-size:20px;'>{symbol} {messages}</p>"
    message.attach(MIMEText(body, 'html'))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)

while True:
    # Defina o fuso horário desejado (São Paulo, Brasil)
    fuso_horario = pytz.timezone('America/Sao_Paulo')

    # Obter a data e hora atuais com o fuso horário especificado
    data_atual = datetime.now(fuso_horario)

    # Calcular a data de 30 dias atrás
    data_inicio = data_atual - timedelta(days=30)
    data_final = data_atual + timedelta(days=1)

    # Converter as datas para o formato necessário (YYYY-MM-DD)
    start = data_inicio.strftime('%Y-%m-%d')
    end = data_final.strftime('%Y-%m-%d')

    # Obter dados históricos
    dados = yf.download('BTC-USD', start=start, end=end, interval='5m')

    # Calcular médias móveis
    dados['MM_bb'] = dados['Close'].rolling(window=20).mean()
    dados['MM_2'] = dados['Close'].rolling(window=1000).mean()
    dados['MM_1'] = dados['Close'].rolling(window=15).mean()

    # Calcular RSI
    periodos = 14
    delta = dados['Close'].diff(1)
    ganho = delta.where(delta > 0, 0)
    perda = -delta.where(delta < 0, 0)
    media_ganho = ganho.rolling(window=periodos).mean()
    media_perda = perda.rolling(window=periodos).mean()
    rs = media_ganho / media_perda
    dados['RSI'] = 100 - (100 / (1 + rs))

    dados['MM_rsi'] = dados['RSI'].rolling(window=20).mean()

    # Calcular média móvel simples
    dados['MM'] = dados['Close'].rolling(window=20).mean()

    # Calcular desvio padrão
    dados['Desvio'] = dados['Close'].rolling(window=20).std()

    # Calcular as bandas de Bollinger
    dados['Banda_Superior'] = dados['MM'] + 2 * dados['Desvio']
    dados['Banda_Inferior'] = dados['MM'] - 2 * dados['Desvio']

    # Sinal de compra/venda
    limite_compra = 30
    meio = 50
    limite_venda = 70

    limite_comprab = 40
    meio = 50
    limite_vendab = 60

    # Adicionando a condição para o sinal de compra
    condicao_compra = (dados['Close'] > dados['MM_2']) & (dados['MM_rsi'] > limite_compra) & (dados['MM_rsi'].shift(1) < limite_compra)

    # Adicionando a condição para o sinal de venda
    condicao_venda = (dados['Close'] > dados['MM_2']) & (dados['MM_rsi'] < limite_venda) & (dados['MM_rsi'].shift(1) > limite_venda)

    # Adicionando a condição para o sinal de compra
    condicao_comprab = (dados['Close'] < dados['MM_2']) & (dados['MM_rsi'] > limite_comprab) & (dados['MM_rsi'].shift(1) < limite_comprab)

    # Adicionando a condição para o sinal de venda
    condicao_vendab = (dados['Close'] < dados['MM_2']) & (dados['MM_rsi'] < limite_vendab) & (dados['MM_rsi'].shift(1) > limite_vendab)

    # Adicionando o sinal com base nas condições
    dados['Sinal'] = 0
    dados.loc[condicao_compra, 'Sinal'] = 1  # Compra
    dados.loc[condicao_venda, 'Sinal'] = -2  # Venda

    dados.loc[condicao_comprab, 'Sinal'] = 1  # Compra
    dados.loc[condicao_vendab, 'Sinal'] = -2  # Venda

    # Verifica se há sinais consecutivos iguais e ajusta
    dados['Sinal'] = dados['Sinal'].diff().fillna(0)

    dados['Posicao'] = dados['Sinal']

    periodo_compra = dados[dados['Posicao'] == 1]
    periodo_venda = dados[dados['Posicao'] == -2]

    # notificação
    hora_sinal = datetime.now(fuso_horario).strftime('%H.%M')

    if not periodo_compra.empty:
        ultima_hora_compra = periodo_compra.index[-1].strftime('%H.%M')

    else:
        ultima_hora_compra = hora_sinal

    if not periodo_venda.empty:
        ultima_hora_venda = periodo_venda.index[-1].strftime('%H.%M')

    else:
        ultima_hora_venda = hora_sinal


    # Converte as strings para minutos desde a meia-noite
    hora_sinal_ = float(hora_sinal)*60

    ultima_hora_compra_ = float(ultima_hora_compra) * 60  
    
    ultima_hora_venda_ = float(ultima_hora_venda) * 60
    
    vhsc = hora_sinal_ - ultima_hora_compra_
    vhsv = hora_sinal_ - ultima_hora_venda_

    if -180 < vhsc < -170:
        mensagem_compra = 'Houve um sinal de compra!'
        print("sinal de compra enviado")
        enviar_email("Sinal de Compra")

    elif -180 < vhsv < -170:
        mensagem_venda = 'Houve um sinal de venda!'
        print("sinal de venda enviado")
        enviar_email("Sinal de Venda")


    print(vhsc, vhsv)

    time.sleep(361)  # Aguarde antes de verificar novamente