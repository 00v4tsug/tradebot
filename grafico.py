import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pytz  # Importe a biblioteca pytz
import time
# Importar Seaborn para o tema escuro
import seaborn as sns

# Configurar o tema escuro
plt.style.use('dark_background')

# Nome da criptomoeda
criptomoeda_nome = '(BTC-USD)'

# Defina o fuso horário desejado (São Paulo, Brasil)
fuso_horario = pytz.timezone('America/Sao_Paulo')

# Obter a data e hora atuais
data_atual = datetime.now(fuso_horario)

# Calcular a data de 30 dias atrás
data_inicio = data_atual - timedelta(days=50)
data_final = data_atual + timedelta(days=1)

# Converter as datas para o formato necessário (YYYY-MM-DD)
start = data_inicio.strftime('%Y-%m-%d')
end = data_final.strftime('%Y-%m-%d')

# Obter dados históricos
dados = yf.download('ETH-USD', start=start, end=end, interval='5m')

# Calcular médias móveis
dados['MM_bb'] = dados['Close'].rolling(window=20).mean()
dados['MM_2'] = dados['Close'].rolling(window=1000).mean()

# Calcular RSI
periodos = 14
delta = dados['Close'].diff(1)
ganho = delta.where(delta > 0, 0)
perda = -delta.where(delta < 0, 0)
media_ganho = ganho.rolling(window=periodos).mean()
media_perda = perda.rolling(window=periodos).mean()
rs = media_ganho / media_perda
dados['RSI'] = 100 - (100 / (1 + rs))

dados['MM_rsi'] = dados['RSI'].rolling(window=10).mean()

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


# Adicionando a condição para o sinal de compra
condicao_compra = (dados['MM'] > dados['MM_2']) & (dados['MM_rsi'] > limite_compra) & (dados['MM_rsi'].shift(1) < limite_compra) & (dados['Close'].shift(1) < dados['MM_bb'])


# Adicionando a condição para o sinal de venda
condicao_venda = (dados['MM'] > dados['MM_2']) & (dados['Close'].shift(1) > dados['MM_bb']) & (dados['MM_rsi'].shift(1) > limite_venda)

# Adicionando o sinal com base nas condições
dados['Sinal'] = 0
dados.loc[condicao_compra, 'Sinal'] = 1  # Compra
dados.loc[condicao_venda, 'Sinal'] = -2  # Venda

dados['Posicao'] = dados['Sinal']

periodo_compra = dados[dados['Posicao'] == 1]
periodo_venda = dados[dados['Posicao'] == -2]

# Gerar gráfico aprimorado
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

# Plotar Preço de Fechamento
ax1.plot(dados['Close'], color='cyan', linewidth=2)
ax1.plot(dados['MM_2'], linestyle='-', color='yellow', alpha=0.9)
ax1.plot(dados['MM_bb'], linestyle='-', color='orange', alpha=0.9)
ax1.fill_between(dados.index, dados['Banda_Superior'], dados['Banda_Inferior'], color='purple', alpha=0.6)
ax1.scatter(periodo_compra.index, periodo_compra['Close'], color='red', label='Compra')
ax1.scatter(periodo_venda.index, periodo_venda['Close'], color='green', label='Venda')


# Adicionar valor atual com destaque visual
valor_atual = dados['Close'].iloc[-1]
ax1.annotate(f'Preço Atual: {valor_atual:.2f}', xy=(0.20, 0.96), xycoords='axes fraction', ha='right', va='top',
             bbox=dict(boxstyle='round', alpha=0.1, facecolor='white'),
             fontsize=10)

# Adicionar nome da criptomoeda
ax1.set_title(criptomoeda_nome, fontsize=14)

# Ajustar formato da data no eixo x
ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

# Adicionar grade
ax1.grid(True, linestyle='--', alpha=0.7)

# Plotar RSI
ax2.plot(dados['RSI'], color='orange')
ax2.axhline(y=limite_compra, color='red', linestyle='--')
ax2.axhline(y=meio, color='white', linestyle='--')
ax2.axhline(y=limite_venda, color='green', linestyle='--')
ax2.plot(dados['MM_rsi'], linestyle='-', color='green', alpha=0.9)

# Adicionar legendas
ax1.legend()
ax2.legend()

# Adicionar título
plt.suptitle('Análise Técnica com Médias Móveis, RSI e BB', y=0.99, fontsize=16)

plt.draw()

plt.show()

saldo_inicial = 1000  # Substitua pelo valor desejado
saldo = saldo_inicial
posicao = 0  # 1 para comprado, -1 para vendido, 0 para neutro
portifolio_valor = []

for i in range(len(dados)):
    sinal = dados['Sinal'][i]

    if sinal == 1 and posicao == 0:  # Sinal de compra e não está em posição comprada
        posicao = 1
        saldo -= dados['Close'][i]  # Deduzir o custo de compra

    elif sinal == -2 and posicao == 1:  # Sinal de venda e está em posição comprada
        posicao = 0
        saldo += dados['Close'][i]  # Adicionar o ganho da venda

    portifolio_valor.append(saldo + posicao * dados['Close'][i])

retorno_total = portifolio_valor[-1] - saldo_inicial
retorno_percentual = (retorno_total / saldo_inicial) * 100

print(f"Retorno Total: {retorno_total:.2f} USD")
print(f"Retorno Percentual: {retorno_percentual:.2f}%")

# Plotar o desempenho do portfólio
plt.figure(figsize=(10, 4))
plt.plot(dados.index, portifolio_valor, label='Portfólio')
plt.title('Desempenho do Portfólio ao Longo do Tempo')
plt.xlabel('Data')
plt.ylabel('Valor do Portfólio (USD)')
plt.legend()
plt.show()