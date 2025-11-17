# Tradutor AI

Aplicação para traduzir arquivos PDF ou EPUB para Português usando OpenAI. Interface moderna (CustomTkinter), exportação em PDF/EPUB/TXT, prévia em tempo real.

## Recursos
- Leitura de `.pdf` e `.epub`
- Tradução com `OpenAI` (API)
- Divisão em chunks por número de caracteres
- Exportação em `pdf`, `epub` e `txt`
- Interface escura com acentos verdes, barra de progresso e prévia em tempo real

## Requisitos
- Python 3.11+
- Dependências do projeto instaladas
- Chave `OPENAI_API_KEY` para uso com OpenAI

## Instalação
1. Crie/ative um ambiente virtual
   - Windows: `python -m venv .venv && .venv\Scripts\activate`
2. Instale dependências
   - `pip install -r requirements.txt` se existir, ou
   - `pip install PyPDF2 tqdm ebooklib beautifulsoup4 reportlab openai customtkinter`

## Configuração
- GUI: preencha o campo “API Key” com sua chave OpenAI.

## Execução (dev)
- Interface desktop: `python -m translator.gui_app`
- CLI simples: `python -m translator.main` (abre diálogos nativos)

## Geração de Executável
Recomendado `onedir` (mais estável com `customtkinter`).

### One-dir (pasta com `.exe`)
```
python -m pip install --upgrade pyinstaller pyinstaller-hooks-contrib
pyinstaller --noconfirm --onedir --windowed --name TradutorAI --collect-all customtkinter translator\gui_app.py
```
- Executável em `dist\TradutorAI\TradutorAI.exe`

### One-file (único `.exe`)
```
pyinstaller --noconfirm --onefile --windowed --name TradutorAI --collect-all customtkinter translator\gui_app.py
```
- Se faltar temas/fontes do `customtkinter`, adicione dados:
```
pyinstaller --noconfirm --onefile --windowed --name TradutorAI \
  --add-data "C:\\Users\\<usuario>\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\customtkinter;customtkinter" \
  translator\gui_app.py
```

### Observações de build
- Caso utilize `onefile`, o início pode ser mais lento por extração temporária.
- Se faltar temas/fontes do `customtkinter`, use `--collect-all customtkinter` ou `--add-data`.

## Uso da GUI
1. Selecione o arquivo de entrada (`.pdf` ou `.epub`)
2. Selecione a pasta de saída
3. Defina `Modelo`, `Chars por chunk` e `Formato de saída`
4. Informe sua `API Key`
5. Clique em `Iniciar`; acompanhe progresso, legenda e prévia
6. `Cancelar` interrompe o processo com segurança

## Organização do Projeto
- `translator/`
  - `gui_app.py`: Interface desktop
  - `main.py`: CLI simples
  - `pipeline.py`: fluxo unificado de tradução
  - `types.py`: tipos de configuração e métricas
  - `pdf_reader.py`, `epub_reader.py`: leitura de fontes
  - `chunker.py`: divisão em chunks
  - `openai_translator.py`: tradução OpenAI (stream e não-stream)
  - `exporter.py`: exportação para `pdf`, `epub` e `txt`

Boas práticas aplicadas:
- Separação por responsabilidade (reader, translator, exporter, GUI)

## Dicas de Desempenho
- Reduza `Chars por chunk` se o modelo demorar
- Preferir modelos menores acelera e reduz custo

## Solução de Problemas
- Falta de temas do `customtkinter` no `.exe`:
  - Use `--collect-all customtkinter` ou `--add-data` conforme acima
- Problemas com chave da API:
  - Certifique-se de preencher a “API Key” na GUI ou use `--api-key` na CLI
- Erros de dependência:
  - Atualize: `python -m pip install --upgrade pyinstaller pyinstaller-hooks-contrib`

## Licença
- Uso interno do projeto. Ajuste conforme necessidade.
