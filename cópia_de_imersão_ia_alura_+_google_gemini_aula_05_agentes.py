# -*- coding: utf-8 -*-
"""Cópia de Imersão IA Alura + Google Gemini - Aula 05 - Agentes.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1CaXipEG3R4YFiIGbXUrbu8ATixfl_vyJ
"""

# Commented out IPython magic to ensure Python compatibility.
# %pip -q install google-genai

# Configura a API Key do Google Gemini

import os
from google.colab import userdata

os.environ["GOOGLE_API_KEY"] = userdata.get('GOOGLE_API_KEY')

# Configura o cliente da SDK do Gemini

from google import genai

client = genai.Client()

MODEL_ID = "gemini-1.5-flash"

# Pergunta ao Gemini uma informação mais recente que seu conhecimento

from IPython.display import HTML, Markdown

# Perguntar pro modelo quando é a próxima imersão de IA ###############################################
resposta = client.models.generate_content(model=MODEL_ID,contents='quando é a proxima imersão de ia da alura?')

# Exibe a resposta na tela
display(Markdown(f"Resposta:\n {resposta.text}"))

# Pergunta ao Gemini uma informação utilizando a busca do Google como contexto

response = client.models.generate_content(model=MODEL_ID,
    contents='Quando é a próxima Imersão IA com Google Gemini da Alura?',
    config={"tools": [{"google_search":{}}]})

# Exibe a resposta na tela
display(Markdown(f"Resposta:\n {response.text}"))

# Exibe a busca
print(f"Busca realizada: {response.candidates[0].grounding_metadata.web_search_queries}")
# Exibe as URLs nas quais ele se baseou
print(f"Páginas utilizadas na resposta: {', '.join([site.web.title for site in response.candidates[0].grounding_metadata.grounding_chunks])}")
print()
display(HTML(response.candidates[0].grounding_metadata.search_entry_point.rendered_content))

# Instalar Framework ADK de agentes do Google ################################################
!pip install -q google-adk

!pip install Pillow transformers torch torchvision torchaudio google-cloud-aiplatform google-generativeai

print("Bibliotecas instaladas/verificadas.")

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types  # Para criar conteúdos (Content e Part)
from datetime import date
import textwrap # Para formatar melhor a saída de texto
from IPython.display import display, Markdown # Para exibir texto formatado no Colab
import requests # Para fazer requisições HTTP
import warnings

warnings.filterwarnings("ignore")

# Função auxiliar que envia uma mensagem para um agente via Runner e retorna a resposta final
def call_agent(agent: Agent, message_text: str) -> str:
    # Cria um serviço de sessão em memória
    session_service = InMemorySessionService()
    # Cria uma nova sessão (você pode personalizar os IDs conforme necessário)
    session = session_service.create_session(app_name=agent.name, user_id="user1", session_id="session1")
    # Cria um Runner para o agente
    runner = Runner(agent=agent, app_name=agent.name, session_service=session_service)
    # Cria o conteúdo da mensagem de entrada
    content = types.Content(role="user", parts=[types.Part(text=message_text)])

    final_response = ""
    # Itera assincronamente pelos eventos retornados durante a execução do agente
    for event in runner.run(user_id="user1", session_id="session1", new_message=content):
        if event.is_final_response():
          for part in event.content.parts:
            if part.text is not None:
              final_response += part.text
              final_response += "\n"
    return final_response

# Função auxiliar para exibir texto formatado em Markdown no Colab
def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

!pip install gTTS Pillow

##############################################################################################################################
# -- gerar audiodescrição em texto e audio a partir de uma imagem de foto carregada pelo usuário Cego ou com baixa Visão --- #
##############################################################################################################################
# Importações necessárias no início do script
from google.colab import files
from PIL import Image
import io
import IPython.display as ip_display # Renomeado para evitar conflito com a função display
import textwrap # Para formatar melhor a saída de texto
import warnings
# Supondo que 'google.genai' e o modelo já foram configurados anteriormente.
# Exemplo: import google.generativeai as genai
# genai.configure(api_key="SUA_API_KEY") # Configuração da API Key
# model = genai.GenerativeModel('gemini-pro-vision') # ou o modelo que você está usando

# --- Configurações Iniciais ---
warnings.filterwarnings("ignore")

# (!! IMPORTANTE !!)
# Descomente e configure as linhas abaixo com sua API Key e o modelo desejado
import google.generativeai as genai
try:
  GOOGLE_API_KEY = userdata.get('GOOGLE_API_KEY')
  genai.configure(api_key=GOOGLE_API_KEY) # <<< DEVE FUNCIONAR AGORA com o import correto
  print("API Key do Google configurada com sucesso usando genai.configure().")
except Exception as e:
  print(f"Erro ao configurar o modelo Generativo: {e}")
  print("Por favor, configure sua API Key e o modelo para continuar.")
  model = None # Define model como None para evitar erros posteriores se a configuração falhar

# Crie a instância do modelo
MODEL_ID = "gemini-1.5-flash-latest" # Seu ID de modelo
model = genai.GenerativeModel(model_name=MODEL_ID) # <<< DEVE FUNCIONAR AGORA
print(f"Instância do modelo '{MODEL_ID}' criada com sucesso!")

# --- Agente 1 para Carregar a Imagem ---
def carregar_e_exibir_imagem():
    """
    Solicita o upload de uma imagem no Google Colab,
    exibe a imagem e a retorna como um objeto PIL.Image.
    """
    print("Por favor, carregue a imagem que você deseja audiodescrever.")
    uploaded = files.upload()

    if not uploaded:
        print("\nNenhuma imagem foi carregada. Por favor, rode a célula novamente e carregue uma imagem.")
        return None, None
    else:
        # Pega o nome do primeiro arquivo carregado
        file_name = next(iter(uploaded))
        print(f"\nImagem '{file_name}' carregada com sucesso!")

        # Prepara e exibe a imagem carregada
        img_data = uploaded[file_name]
        img_pil = Image.open(io.BytesIO(img_data))

        print("\n--- Imagem Carregada ---")
        ip_display.display(img_pil) # Usando ip_display para evitar conflito
        print("------------------------")
        return img_pil, file_name

# --- Agente 2 - para Gerar Audiodescrição ---
def gerar_audiodescricao_da_imagem(modelo, imagem_pil, prompt):
    """
    Gera a audiodescrição para uma imagem fornecida usando um modelo generativo.

    Args:
        modelo: O modelo generativo configurado (ex: Gemini).
        imagem_pil: A imagem carregada como um objeto PIL.Image.
        prompt: O prompt detalhado para guiar a geração da audiodescrição.

    Returns:
        A string da audiodescrição gerada ou None se ocorrer um erro.
    """
    if modelo is None:
        print("\nO modelo generativo não foi configurado. Não é possível gerar a audiodescrição.")
        return None
    if imagem_pil is None:
        print("\nNenhuma imagem fornecida para gerar audiodescrição.")
        return None

    print("\nGerando audiodescrição da imagem...")
    try:
        response = modelo.generate_content([prompt, imagem_pil])

        if response.candidates and response.candidates[0].content.parts:
            audiodescricao_texto = response.candidates[0].content.parts[0].text
            return audiodescricao_texto
        else:
            print("\nNão foi possível gerar a audiodescrição. A resposta do modelo está vazia ou malformada.")
            print("Detalhes da resposta:", response)
            return None
    except Exception as e:
        print(f"\nOcorreu um erro durante a geração da audiodescrição: {e}")
        return None

# --- Agente 3 - (Opcional) para Gerar Áudio da Descrição ---
def gerar_audio_da_descricao(texto_descricao, idioma='pt', nome_arquivo="audiodescricao.mp3"):
    """
    Converte o texto da audiodescrição em um arquivo de áudio MP3.

    Args:
        texto_descricao: A string da audiodescrição.
        idioma: O idioma para a síntese de voz (padrão 'pt').
        nome_arquivo: O nome do arquivo MP3 a ser salvo (padrão 'audiodescricao.mp3').
    """
    if not texto_descricao:
        print("\nNenhum texto de descrição fornecido para gerar áudio.")
        return

    try:
        # Tenta importar gTTS aqui para não ser um requisito rígido se não for usado
        from gtts import gTTS
        print("\nGerando áudio da descrição...")
        tts = gTTS(text=texto_descricao, lang=idioma, slow=False)
        tts.save(nome_arquivo)
        print(f"Áudio salvo como '{nome_arquivo}'")
        ip_display.display(ip_display.Audio(nome_arquivo)) # Usando ip_display
    except ImportError:
        print("\nPara gerar áudio, a biblioteca gTTS é necessária.")
        print("Você pode instalá-la executando: !pip install gTTS")
    except Exception as e_tts:
        print(f"\nErro ao gerar áudio: {e_tts}")
        print("A geração de áudio é opcional. A descrição em texto foi gerada com sucesso.")

# --- Fluxo Principal do Programa ---
def main():
    """
    Função principal para orquestrar o carregamento da imagem e a geração da audiodescrição.
    """
    # (Certifique-se de que a variável 'model' está configurada no início do script)
    if 'model' not in globals() or model is None:
        print("ERRO CRÍTICO: A variável 'model' não foi definida ou configurada.")
        print("Por favor, descomente e configure a inicialização do modelo no início do script.")
        return

    # 1. Agente para carregar a imagem
    imagem_pil, nome_arquivo = carregar_e_exibir_imagem()

    if imagem_pil:
        # 2. Definir o prompt para o agente de audiodescrição
        prompt_audiodescricao = """
        Você é um audiodescritor profissional para pessoas cegas ou com baixa visão.
        Descreva a imagem a seguir em detalhes vívidos e objetivos. Concentre-se nos seguintes aspectos:
        1.  **Cena Geral:** Qual é o tema principal ou a configuração da imagem? Onde parece estar acontecendo?
        2.  **Elementos Principais:** Quais são os objetos, pessoas ou animais mais proeminentes? Descreva suas aparências, roupas (se aplicável), posições e expressões.
        3.  **Ações e Interações:** O que está acontecendo na imagem? As pessoas ou animais estão interagindo? Se sim, como?
        4.  **Contexto e Atmosfera:** Quais cores predominam? Qual é a iluminação? A imagem transmite alguma emoção ou atmosfera específica (alegria, tristeza, mistério, etc.)?
        5.  **Detalhes Relevantes:** Inclua detalhes menores que possam ser importantes para a compreensão completa da imagem, como texturas, padrões ou elementos de fundo significativos.
        Evite interpretações subjetivas ou opiniões pessoais. Forneça uma descrição clara e concisa, como se estivesse narrando a cena para alguém que não pode vê-la.
        Comece a descrição diretamente, sem frases introdutórias como "Esta imagem mostra...".
        Defina o sequenciamento da descrição dos elementos, sendo priorizado de cima para baixo e da esquerda para a direita.
        """

        # 3. Agente para gerar a audiodescrição
        audiodescricao_texto = gerar_audiodescricao_da_imagem(model, imagem_pil, prompt_audiodescricao)

        if audiodescricao_texto:
            print("\n--- Audiodescrição Gerada ---")
            # Usando textwrap para formatar a saída para melhor leitura
            wrapped_text = textwrap.fill(audiodescricao_texto, width=150) # Ajuste width conforme necessário
            print(wrapped_text)
            # ip_display.display(ip_display.Markdown(audiodescricao_texto)) # Outra forma de exibir, se preferir Markdown
            print("----------------------------")

            # 4. (Opcional) Agente para gerar áudio da descrição
            # Perguntar ao usuário se deseja gerar o áudio
            gerar_audio_agora = input("\nDeseja gerar o áudio desta descrição? (s/n): ").strip().lower()
            if gerar_audio_agora == 's':
                gerar_audio_da_descricao(audiodescricao_texto)
            else:
                print("\nGeração de áudio pulada.")
    else:
        print("\nProcesso interrompido pois nenhuma imagem foi carregada ou houve um erro no carregamento.")

# --- Executar o programa ---
if __name__ == "__main__":
    # Esta verificação __name__ == "__main__" é padrão em scripts Python,
    # mas em notebooks Colab, você pode simplesmente chamar main() diretamente.
    # No Colab, você chamaria a função main() assim:
    # main()
    # No entanto, para que funcione colando diretamente na célula,
    # é melhor chamar main() sem o if, ou garantir que o model está configurado.

    # Exemplo de como você chamaria no Colab (após configurar o 'model'):
    if 'model' in globals() and model is not None:
         main()
    else:
         print("Por favor, configure o modelo generativo (descomente e edite as linhas de configuração no início do script) antes de rodar 'main()'.")