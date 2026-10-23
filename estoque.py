import json
import os
import streamlit as st
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Controle de Estoque",
    page_icon="📦",
    layout="centered"
)

class Estoque:
    def __init__(self, nome_arquivo="estoque.json"):
        self.nome_arquivo = nome_arquivo
        self.produtos = self.carregar_dados()

    def carregar_dados(self):
        if os.path.exists(self.nome_arquivo):
            try:
                with open(self.nome_arquivo, "r", encoding="utf-8") as arquivo:
                    return json.load(arquivo)
            except json.JSONDecodeError:
                return {}
        return {}

    def salvar_dados(self):
        with open(self.nome_arquivo, "w", encoding="utf-8") as arquivo:
            json.dump(self.produtos, arquivo, ensure_ascii=False, indent=4)

    def gerar_proximo_codigo(self):
        if not self.produtos:
            return "1"
        
        codigos_existentes = sorted([int(codigo) for codigo in self.produtos.keys()])
        
        for i in range(1, codigos_existentes[-1] + 1):
            if i not in codigos_existentes:
                return str(i)
                
        return str(codigos_existentes[-1] + 1)

    def cadastrar_produto(self, nome, quantidade, preco, quantidade_minima):
        codigo = self.gerar_proximo_codigo()
        
        self.produtos[codigo] = {
            'nome': nome,
            'quantidade': quantidade,
            'preco': preco,
            'quantidade_minima': quantidade_minima
        }
        self.salvar_dados()
        return codigo

    def movimentar_estoque(self, codigo, tipo, quantidade):
        if codigo in self.produtos:
            produto = self.produtos[codigo]
            
            if tipo == "Entrada":
                produto['quantidade'] += quantidade
                self.salvar_dados()
                return f"Entrada de {quantidade} un. realizada com sucesso! Estoque atual: {produto['quantidade']}."
                
            elif tipo == "Saída":
                if produto['quantidade'] >= quantidade:
                    produto['quantidade'] -= quantidade
                    self.salvar_dados()
                    
                    if produto['quantidade'] == 0:
                        return f"⚠️ Saída realizada. O estoque do produto '{produto['nome']}' chegou a **0**. Você pode mantê-lo ou excluí-lo pelo menu."
                    else:
                        return f"Saída de {quantidade} un. realizada. Estoque atual: {produto['quantidade']}."
                else:
                    return f"Erro: Estoque insuficiente! Há apenas {produto['quantidade']} unidades disponíveis."
        return "Erro: Produto não encontrado!"

    def excluir_produto(self, codigo):
        if codigo in self.produtos:
            nome_removido = self.produtos[codigo]['nome']
            del self.produtos[codigo]
            self.salvar_dados()
            return True, f"Produto '{nome_removido}' (Código: {codigo.zfill(3)}) foi removido com sucesso!"
        return False, "Erro: Produto não encontrado!"

# Inicializa a classe de estoque na sessão do Streamlit
if "estoque" not in st.session_state:
    st.session_state.estoque = Estoque()

estoque = st.session_state.estoque

# --- INTERFACE WEB (STREAMLIT) ---
st.title("📦 Sistema de Controle de Estoque")
st.write("Gerencie seus produtos de forma simples e visual.")

# Menu Lateral
menu = st.sidebar.selectbox(
    "Escolha uma opção", 
    ["Listar Estoque", "Cadastrar Novo Produto", "Movimentar Estoque", "Excluir Produto"]
)

# 1. LISTAR PRODUTOS (Com destaque em amarelo para estoque baixo)
if menu == "Listar Estoque":
    st.subheader("📋 Produtos Cadastrados")
    
    if not estoque.produtos:
        st.info("O estoque está vazio no momento.")
    else:
        dados_tabela = []
        codigos_ordenados = sorted(estoque.produtos.keys(), key=int)
        
        for codigo in codigos_ordenados:
            info = estoque.produtos[codigo]
            qtd = info["quantidade"]
            qtd_min = info.get("quantidade_minima", 0)
            
            # Identifica se está abaixo ou igual à quantidade mínima
            abaixo_minimo = qtd <= qtd_min
            
            dados_tabela.append({
                "Código": codigo.zfill(3),
                "Nome": info["nome"],
                "Quantidade": qtd,
                "Preço Unitário (R$)": f"R$ {info['preco']:.2f}",
                "Valor Total (R$)": f"R$ {qtd * info['preco']:.2f}",
                "_alerta": abaixo_minimo  # Coluna auxiliar oculta para formatação
            })
        
        df = pd.DataFrame(dados_tabela)
        
        # Função para colorir o texto de amarelo se atingir a quantidade mínima
        def destacar_estoque_baixo(row):
            if row["_alerta"]:
                return ['color: #ffeb3b; font-weight: bold;' for _ in row]
            return ['' for _ in row]
        
        # Aplica o estilo e oculta a coluna auxiliar "_alerta"
        df_estilizado = df.style.apply(destacar_estoque_baixo, axis=1)
        st.dataframe(df_estilizado, column_config={"_alerta": None}, use_container_width=True)

# 2. CADASTRAR PRODUTO
elif menu == "Cadastrar Novo Produto":
    st.subheader("➕ Cadastrar Novo Produto")
    
    with st.form("form_cadastro"):
        nome = st.text_input("Nome do Produto")
        quantidade = st.number_input("Quantidade Inicial", min_value=0, step=1)
        preco = st.number_input("Preço Unitário (R$)", min_value=0.0, format="%.2f")
        quantidade_minima = st.number_input("Quantidade Mínima no Estoque (Alerta)", min_value=0, step=1, value=5)
        
        enviar = st.form_submit_button("Cadastrar Produto")
        
        if enviar:
            if nome.strip() == "":
                st.error("O nome do produto não pode estar vazio!")
            else:
                codigo_gerado = estoque.cadastrar_produto(nome, int(quantidade), float(preco), int(quantidade_minima))
                st.success(f"Produto '{nome}' cadastrado com sucesso! **Código: {codigo_gerado.zfill(3)}**")

# 3. MOVIMENTAR ESTOQUE
elif menu == "Movimentar Estoque":
    st.subheader("🔄 Movimento de Estoque (Entrada / Saída)")
    
    if not estoque.produtos:
        st.warning("Não há produtos cadastrados para movimentar.")
    else:
        codigos_ordenados = sorted(estoque.produtos.keys(), key=int)
        opcoes_produtos = {f"Cód: {k.zfill(3)} - {estoque.produtos[k]['nome']} (Atual: {estoque.produtos[k]['quantidade']})": k for k in codigos_ordenados}
        
        escolha = st.selectbox("Selecione o Produto", list(opcoes_produtos.keys()))
        codigo_selecionado = opcoes_produtos[escolha]
        
        tipo_movimento = st.radio("Tipo de Movimento", ["Entrada", "Saída"])
        quantidade_movimento = st.number_input("Quantidade", min_value=1, step=1)
        
        if st.button("Confirmar Movimento"):
            mensagem = estoque.movimentar_estoque(codigo_selecionado, tipo_movimento, int(quantidade_movimento))
            if "Erro" in mensagem:
                st.error(mensagem)
            elif "⚠️" in mensagem:
                st.warning(mensagem)
            else:
                st.success(mensagem)

# 4. EXCLUIR PRODUTO
elif menu == "Excluir Produto":
    st.subheader("🗑️ Excluir Produto do Sistema")
    
    if not estoque.produtos:
        st.info("Não há produtos cadastrados para excluir.")
    else:
        codigos_ordenados = sorted(estoque.produtos.keys(), key=int)
        opcoes_produtos = {f"Cód: {k.zfill(3)} - {estoque.produtos[k]['nome']} (Qtd: {estoque.produtos[k]['quantidade']})": k for k in codigos_ordenados}
        
        escolha_exclusao = st.selectbox("Selecione o produto que deseja apagar", list(opcoes_produtos.keys()))
        codigo_exclusao = opcoes_produtos[escolha_exclusao]
        
        st.warning("⚠️ Atenção: Esta ação removerá o produto permanentemente do arquivo JSON e liberará o código para futuros cadastros.")
        
        if st.button("Excluir Definitivamente"):
            sucesso, mensagem = estoque.excluir_produto(codigo_exclusao)
            if sucesso:
                st.success(mensagem)
                st.rerun()
            else:
                st.error(mensagem)