import streamlit as st
import requests
import pandas as pd
import plotly.express as px


st.set_page_config(layout = 'wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'


#TITULO
st.title('DASHBOARD DE VENDAS:shopping_trolley:')


#Coleta dos Dados
url = 'https://labdados.com/produtos'

regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')

regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value= True)

if todos_anos:
    ano = ''
else:
    ano =  st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao':regiao.lower(), 'ano':ano}    
response = requests.get(url, params=query_string)


dados = pd.DataFrame.from_dict(response.json())

dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

    
##TABELAS

#Tabelas receita
receitas_estados = dados.groupby('Local da compra')[['Preço']].sum()
receitas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(receitas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending=False)


receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq= 'M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name()


receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending= False)

#Tabela quantidade de vendas
# Calculando a contagem de vendas por 'Local da compra'
quantidade_venda = dados.groupby('Local da compra').size().reset_index(name='Quantidade de vendas')

# Obtendo os dados de latitude e longitude
dados_lat_lon = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']]

# Mesclando os dois DataFrames com concatenação
quantidade_venda = pd.concat([dados_lat_lon.set_index('Local da compra'), quantidade_venda.set_index('Local da compra')], axis=1).reset_index()

# Ordenando pela quantidade de vendas em ordem decrescente
quantidade_venda = quantidade_venda.sort_values('Quantidade de vendas', ascending=False)

# Vendas Mensal

# Supondo que a coluna 'Data da Compra' contenha a data da compra no formato apropriado (você pode precisar ajustar isso)
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'])

# Extrair o mês da coluna 'Data da Compra' e converter para string
dados['Mês'] = dados['Data da Compra'].dt.to_period('M').astype(str)

# Agrupar por Mês e Local da compra e contar as vendas
vendas_por_mes_local = dados.groupby(['Mês', 'Local da compra']).size().reset_index(name='Quantidade de vendas')



vendas_categoria = dados.groupby('Categoria do Produto')[['Local da compra']].count().sort_values('Local da compra', ascending= False)



#Tabela Vendedores

vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

##GRAFICOS

#graficos receita
fig_mapa_receita = px.scatter_geo(receitas_estados, 
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  title='Receita por estado')


fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mês',
                             y = 'Preço',
                             markers= True,
                             range_y= (0, receita_mensal.max()),
                             color= 'Ano',
                             title= 'Receita Mensal')

fig_receita_mensal.update_layout(yaxis_title = 'Receita')


fig_receita_estado = px.bar(receitas_estados.head(),
                            x = 'Local da compra',
                            y = 'Preço',
                            color = 'Local da compra',
                            text_auto= True,
                            title= 'Top estados (receita)')

fig_receita_estado.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto= True,
                                title= 'Receita por categoria')


fig_receita_categorias.update_layout(yaxis_title = 'Quantidade de Vendas')


#graficos quantidade de venda

fig_mapa_venda = px.scatter_geo(quantidade_venda, 
                                lat='lat',  # Substitua 'lat' pelo nome correto da coluna de latitude
                                lon='lon',  # Substitua 'lon' pelo nome correto da coluna de longitude
                                scope='south america',
                                size='Quantidade de vendas',  # Certifique-se de que 'Preço' é a coluna correta para definir o tamanho
                                template='seaborn',
                                hover_name='Local da compra',
                                title='Quantidade venda por estado')


fig_vendas_mensal = px.line(vendas_por_mes_local, x='Mês', y='Quantidade de vendas', color='Local da compra',
              labels={'Mês': 'Mês', 'Quantidade de vendas': 'Quantidade de Vendas'},
              title='Quantidade de Vendas por Mês')

fig_vendas_mensal.update_layout(yaxis_title = 'Quantidade de Vendas')


fig_vendas_estado = px.bar(quantidade_venda.head(),
                            x = 'Local da compra',
                            y = 'Quantidade de vendas',
                            color = 'Local da compra',
                            text_auto= True,
                            title= 'Top estados (vendas)')

fig_receita_estado.update_layout(yaxis_title = 'Receita')

fig_vendas_categorias = px.bar(vendas_categoria,
                                text_auto= True,
                                title= 'Vendas Categorias(Estado)')


fig_receita_categorias.update_layout(yaxis_title = 'Quantidade de Vendas')



##VISUALIZACAO NO STREAMLITE

#Abas

aba1, aba2, aba3 = st.tabs(['Receitas', 'Quantidade de Vendas', 'Vendedores'])

#Metricas

with aba1:


    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita',formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita,use_container_width=True)
        st.plotly_chart(fig_receita_estado,use_container_width=True)
    with col2:
        st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)



with aba2:


    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita',formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_venda, use_container_width= True)
        st.plotly_chart(fig_vendas_estado, use_container_width=True)
    with col2:
        st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)
        st.plotly_chart(fig_vendas_categorias, use_container_width=True)

with aba3:
    qtd_vendedores = st.number_input('Quantidades de Vendedores', 2 , 10 ,5)

    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita',formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending= False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending= False).head(qtd_vendedores).index,
                                        text_auto= True,
                                        color = 'sum',
                                        title= f'Top {qtd_vendedores} vendedores (receita)')
        
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)
    with col2:
        st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending= False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending= False).head(qtd_vendedores).index,
                                        text_auto= True,
                                        color = 'count',
                                        title= f'Top {qtd_vendedores} vendedores (vendas)')
        
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)