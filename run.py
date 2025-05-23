import pandas as pd
import random
import os
import subprocess
from PyPDF2 import PdfMerger
import re

def gerar_valor_aleatorio(tipo, min_val, max_val, precision=0):
    if tipo == 'int':
        return random.randint(min_val, max_val)
    elif tipo == 'float':
        return round(random.uniform(min_val, max_val), precision)
    else:
        raise ValueError("Tipo inválido. Use 'int' ou 'float'.")

def substituir_aleatorios_e_nome(tex_template, valores_aleatorios, nome_aluno):
    tex_modificado = tex_template
    for i, val in enumerate(valores_aleatorios):
        tex_modificado = tex_modificado.replace(f"aleat{i+1}", str(val))
    tex_modificado = tex_modificado.replace("completo", nome_aluno)
    return tex_modificado

def gerar_pdf(tex_content, nome_aluno, output_dir):
    safe_nome_aluno = "".join(c if c.isalnum() else "_" for c in nome_aluno)
    if not safe_nome_aluno:
        safe_nome_aluno = "aluno_sem_nome"

    tex_file_name_base = os.path.join(output_dir, safe_nome_aluno)
    tex_file_path = f"{tex_file_name_base}.tex"
    
    try:
        with open(tex_file_path, 'w', encoding='utf-8') as tex_file:
            tex_file.write(tex_content)
        
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', output_dir, tex_file_path], 
            check=True, capture_output=True, text=True, encoding='latin-1'
        )
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao compilar LaTeX para {safe_nome_aluno}: {e}")
        print(f"Saída do pdflatex (stdout):\n{e.stdout}")
        print(f"Saída de erro do pdflatex (stderr):\n{e.stderr}")
        print(f"O arquivo .tex problemático foi salvo em: {tex_file_path}")
        return 
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao gerar PDF para {safe_nome_aluno}: {e}")
        if os.path.exists(tex_file_path):
             print(f"O arquivo .tex foi salvo em: {tex_file_path}")
        return

    for ext in ['aux', 'log', 'out', 'tex']:
        aux_file = f"{tex_file_name_base}.{ext}"
        if os.path.exists(aux_file):
            try:
                os.remove(aux_file)
            except OSError as e:
                print(f"Aviso: Não foi possível remover {aux_file}: {e}")

def processar_alunos(csv_path, tex_template_path, output_dir):
    try:
        alunos_df = pd.read_csv(csv_path, encoding='latin-1')
    except FileNotFoundError:
        print(f"Erro: Arquivo CSV '{csv_path}' não encontrado.")
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")
        return

    try:
        with open(tex_template_path, 'r', encoding='utf-8', errors="ignore") as tex_file:
            tex_template_original = tex_file.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo template LaTeX '{tex_template_path}' não encontrado.")
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo template LaTeX: {e}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    match = re.search(r'(\\begin\{questions\})(.*?)(\\end\{questions\})', tex_template_original, re.DOTALL)
    if not match:
        print("Erro: Ambiente \\begin{questions}...\\end{questions} não encontrado no template.")
        return

    tex_header = tex_template_original[:match.start(1)]
    questions_section_original_content = match.group(2)
    tex_footer = tex_template_original[match.end(3):]

    split_by_questao_marker = re.split(r'(\\questao)', questions_section_original_content)
    content_before_first_questao = split_by_questao_marker[0]
    
    original_question_blocks_raw = []
    if len(split_by_questao_marker) > 1:
        for i in range(1, len(split_by_questao_marker), 2):
            try:
                original_question_blocks_raw.append(split_by_questao_marker[i] + split_by_questao_marker[i+1])
            except IndexError:
                original_question_blocks_raw.append(split_by_questao_marker[i])
    
    all_question_blocks_cleaned = []
    for q_block in original_question_blocks_raw:
        cleaned_block = re.sub(r'\\newpage\s*$', '', q_block)
        all_question_blocks_cleaned.append(cleaned_block)
    

    for _, aluno in alunos_df.iterrows():
        nome_aluno = aluno['Nome']
        
        aleat1 = gerar_valor_aleatorio('int', 7, 25)
        aleat2 = gerar_valor_aleatorio('int', 10, 40)
        aleat3 = gerar_valor_aleatorio('int', 95, 255)
        aleat4 = gerar_valor_aleatorio('int', 100, 200) # Usado para \setrandomizerseed no TeX
        aleat5 = gerar_valor_aleatorio('float', 100.0, 200.0, precision=2)
        valores_aleatorios = [aleat1, aleat2, aleat3, aleat4, aleat5]
        

        shuffled_questions_for_student = list(all_question_blocks_cleaned) # Criar uma cópia
        random.shuffle(shuffled_questions_for_student) # Embaralhar a cópia
        

        student_questions_section = content_before_first_questao + "".join(shuffled_questions_for_student)
        
        tex_for_student_final_order = tex_header + student_questions_section + tex_footer
        tex_content_final = substituir_aleatorios_e_nome(tex_for_student_final_order, valores_aleatorios, nome_aluno)
        
        gerar_pdf(tex_content_final, nome_aluno, output_dir)
        print(f"PDF gerado para {nome_aluno} com valores: {valores_aleatorios}, TODAS as questões randomizadas e \\newpage entre questões removido.")

def unir_pdf(saida_dir, saida_nome="provas_prontas.pdf"):
    pdfs = [os.path.join(saida_dir, pdf) for pdf in os.listdir(saida_dir) if pdf.endswith('.pdf')]
    pdfs.sort()

    if not pdfs:
        print(f"Nenhum PDF encontrado em {saida_dir} para unir.")
        return

    merger = PdfMerger()
    for pdf in pdfs:
        try:
            merger.append(pdf)
        except Exception as e:
            print(f"Erro ao tentar adicionar {pdf} ao merge: {e}")
    
    saida_caminho = os.path.join(saida_dir, saida_nome)
    try:
        merger.write(saida_caminho)
        merger.close()
        print(f"PDFs unidos e salvos como {saida_caminho}")
    except Exception as e:
        print(f"Erro ao salvar o PDF unido: {e}")

# --- Configuração ---
csv_path = 'alunos.csv'
tex_template_path = 'main.tex'
output_dir = 'pdfs_gerados'   

# --- Execução ---
processar_alunos(csv_path, tex_template_path, output_dir)
unir_pdf(output_dir)