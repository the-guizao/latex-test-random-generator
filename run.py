import pandas as pd
import random
import os
import subprocess
from PyPDF2 import PdfMerger

def gerar_valor_aleatorio(tipo, min_val, max_val, precision=0):
    if tipo == 'int':
        return random.randint(min_val, max_val)
    elif tipo == 'float':
        return round(random.uniform(min_val, max_val), precision)
    else:
        raise ValueError("Tipo inválido. Use 'int' ou 'float'.")

def substituir_aleatorios_e_nome(tex_template, valores_aleatorios, nome_aluno):

    tex_modificado = tex_template.replace("aleat1", str(valores_aleatorios[0]))
    tex_modificado = tex_modificado.replace("aleat2", str(valores_aleatorios[1]))
    tex_modificado = tex_modificado.replace("aleat3", str(valores_aleatorios[2]))
    tex_modificado = tex_modificado.replace("aleat4", str(valores_aleatorios[3]))
    tex_modificado = tex_modificado.replace("aleat5", str(valores_aleatorios[4]))
    tex_modificado = tex_modificado.replace("completo", nome_aluno)
    return tex_modificado

def gerar_pdf(tex_content, nome_aluno, output_dir):
    """
    Gera o arquivo .tex e compila em PDF usando pdflatex.
    """
    tex_file_name = f"{output_dir}/{nome_aluno}.tex"
    
    # Salvar o conteúdo no arquivo .tex
    with open(tex_file_name, 'w') as tex_file:
        tex_file.write(tex_content)
    
    # Compilar o .tex em PDF
    subprocess.run(['pdflatex', '-output-directory', output_dir, tex_file_name], check=True)
    
    # Limpar arquivos auxiliares gerados pela compilação LaTeX
    for ext in ['aux', 'log', 'out', 'tex']:
        aux_file = f"{output_dir}/{nome_aluno}.{ext}"
        if os.path.exists(aux_file):
            os.remove(aux_file) 

def processar_alunos(csv_path, tex_template_path, output_dir):
    
    # Carregar a tabela de alunos
    alunos_df = pd.read_csv(csv_path, encoding='latin-1')
    
    # Ler o arquivo .tex template
    with open(tex_template_path,  'r', errors="ignore") as tex_file:
        tex_template = tex_file.read()

    # Criar diretório de saída, se não existir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Processar cada aluno
    for _, aluno in alunos_df.iterrows():
        nome_aluno = aluno['Nome']
        
        # Gerar valores aleatórios para aleat1, aleat2, aleat3, e aleat4, com diferentes configurações
        aleat1 = gerar_valor_aleatorio('int', 7, 25)  # Inteiro entre 1 e 100
        aleat2 = gerar_valor_aleatorio('int', 10, 40)  # Float entre 1.0 e 10.0 com 2 casas decimais
        aleat3 = gerar_valor_aleatorio('int', 95, 255)  # Float entre 20.0 e 50.0 com 1 casa decimal
        aleat4 = gerar_valor_aleatorio('int', 100, 200)  # Inteiro entre 100 e 200
        aleat5 = gerar_valor_aleatorio('float', 100.0, 200.0, precision=2)

        valores_aleatorios = [aleat1, aleat2, aleat3, aleat4, aleat5]
        
        tex_content = substituir_aleatorios_e_nome(tex_template, valores_aleatorios, nome_aluno)
        
        # Gerar o PDF personalizado
        gerar_pdf(tex_content, nome_aluno, output_dir)
        print(f"PDF gerado para {nome_aluno} com valores aleatórios: {valores_aleatorios}")

def unir_pdf(saida_dir, saida_nome="provas_prontas.pdf"):
    pdfs = [f"{saida_dir}/{pdf}" for pdf in os.listdir(saida_dir) if pdf.endswith('.pdf')]
    pdfs.sort()

    merger = PdfMerger()
    for pdf in pdfs:
        merger.append(pdf)
    
    saida_caminho = os.path.join(saida_dir,saida_nome)
    merger.write(saida_caminho)
    merger.close()

    print(f"Salvo como {saida_caminho}")


# Caminhos dos arquivos
csv_path = 'alunos.csv'  # Caminho do arquivo .csv com os nomes dos alunos
tex_template_path = 'main.tex'  # Caminho do arquivo .tex template
output_dir = 'pdfs'  # Diretório de saída para os PDFs gerados

processar_alunos(csv_path, tex_template_path, output_dir)
unir_pdf(output_dir)
