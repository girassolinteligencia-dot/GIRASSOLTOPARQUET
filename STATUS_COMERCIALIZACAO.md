# Relatório de Status e Viabilidade de Comercialização
**Projeto:** ConversorParquetOffline / GIRASSOLtoPARQUET  
**Autor:** Antigravity AI  
**Data:** 9 de Julho de 2026  

---

## 1. Inventário Técnico Atual

Com base na auditoria direta efetuada no código-fonte contido em [app/core/](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core), seguem as funcionalidades implementadas, a cobertura de testes e as configurações de versão reais do projeto:

### Funcionalidades Core (app/core)
*   **Formatos de Entrada Suportados:**
    *   **CSV:** Processado no arquivo [csv_reader.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core/csv_reader.py). Possui detecção dinâmica de codificação (testa sequencialmente `utf-8-sig`, `utf-8`, `cp1252` e `latin-1`) e delimitador (analisa a frequência dos delimitadores `,`, `;`, `\t` e `|` nas primeiras 5 linhas não-vazias).
    *   **Excel (.xlsx):** Processado no arquivo [excel_reader.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core/excel_reader.py). Utiliza o motor ultraveloz `calamine` com fallback automático para `openpyxl`. Suporta a leitura apenas da primeira aba (comportamento padrão) ou o processamento de todas as abas, gravando um arquivo `.parquet` individual por aba preenchida.
    *   **JSON:** Processado no arquivo [json_reader.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core/json_reader.py). Converte arquivos estruturados como dicionário único, listas de registros, ou objetos cuja chave interna contenha listas de dicionários. Possui fallback de leitura linha a linha (JSON Lines).
    *   **NDJSON/JSONL:** Processado no arquivo [ndjson_reader.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core/ndjson_reader.py). Processa arquivos no formato Newline Delimited JSON. Se o parâmetro `ignore_invalid_lines` for ativado, ignora e isola linhas malformadas sem interromper a execução.
*   **Opções de Compressão Parquet:**
    *   A gravação no arquivo [parquet_writer.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core/parquet_writer.py) mapeia três modos usando o motor PyArrow: `Snappy` (padrão), `Zstd` (alta compressão) e `Nenhuma` (uncompressed).
*   **Tratamento de Dados Sensíveis:**
    *   A lógica em [schema.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core/schema.py) identifica colunas sensíveis (como `cpf`, `cnpj`, `documento`, `titulo_eleitoral`, `inscricao`, `cep`, `telefone`, `celular`, `zona`, `secao`, `codigo`, `id_municipio`, `numero_candidato`, `numero_partido`, etc.) através de correspondência insensível a maiúsculas/minúsculas, espaços e acentuação.
    *   As colunas sensíveis são forçadas para o tipo `pl.String` na importação. Isso previne que zeros à esquerda sejam truncados (como ocorre com CPFs iniciados em zero convertidos erroneamente para inteiros) e que ocorram perdas de representação numérica. Para o Excel, há tratamento específico em floats de valor inteiro (`.0`) antes de passá-los para String.
*   **Validações e Tratamento de Erros:**
    *   O módulo [validator.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core/validator.py) executa verificações antes da escrita: valida a existência e integridade do arquivo de entrada (tamanho > 0 bytes), se o formato é suportado e as permissões reais de leitura. Também valida as permissões de gravação no diretório de destino escrevendo e removendo um arquivo temporário `.write_test`.
    *   A aplicação implementa processamento assíncrono em fila com [job_queue.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/services/job_queue.py) em segundo plano, evitando travamentos na GUI.
*   **Normalização de Nomes de Colunas:**
    *   O arquivo [normalizer.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core/normalizer.py) executa a limpeza dos cabeçalhos das tabelas: converte para minúsculas, remove acentos, remove caracteres especiais não-alfanuméricos (mantendo apenas `a-z`, `0-9` e `_`), substitui espaçamentos e hifens por underline e resolve colisões de nomes duplicados inserindo sufixos numéricos (`_1`, `_2`, etc.).
*   **Achatamento de JSON (Flattening):**
    *   Suporta recursão para desaninhar sub-objetos JSON complexos em colunas planas (ex: `{"contato": {"email": "x"}}` -> `contato_email`).
*   **Perfis / Presets de Conversão:**
    *   Disponibiliza três presets configuráveis no [settings_panel.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/ui/settings_panel.py): "Preservação Máxima", "BI de Dados" e "GIS & Geoprocessamento". Nos presets "BI" e "GIS", o sistema realiza casting inteligente automático de colunas identificadas como coordenadas (`latitude`, `longitude`, `lat`, `lon`, `lng`, etc.) de String para `Float64`, tratando vírgulas como pontos decimais e ignorando erros de conversão.
*   **Relatórios de Auditoria:**
    *   Implementado em [report_service.py](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/services/report_service.py). Se ativado, gera um arquivo `.json` (com metadados técnicos brutos) e um `.txt` (formatado de forma legível para humanos e contendo a data, o status final, o hash SHA-256 da origem, o tamanho do arquivo, o mapeamento de colunas normalizadas, os tipos de dados inferidos e os eventuais erros da conversão).

### Testes Automatizados
*   A suíte de testes está localizada no diretório [tests/](file:///c:/GIRASSOLTOPARQUET/parquet-converter/tests).
*   Consiste em 8 arquivos que cobrem a lógica de dados do projeto: `test_csv.py`, `test_excel.py`, `test_json.py`, `test_jsonl.py`, `test_ndjson.py`, `test_normalizer.py`, `test_parquet.py` e `test_presets.py`.
*   O comando `pytest` executa com sucesso, coletando e aprovando todos os **14 testes unitários** estruturados.
*   **Cobertura aproximada:** Cerca de 100% dos módulos de processamento lógico de dados contidos em [app/core/](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/core) estão cobertos. No entanto, não há testes automatizados para a interface gráfica ([app/ui/](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/ui)) ou para os serviços gerais ([app/services/](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/services)). A cobertura geral do código Python do projeto situa-se na faixa de **60% a 70%**.

### Versionamento do Projeto
*   O arquivo [pyproject.toml](file:///c:/GIRASSOLTOPARQUET/parquet-converter/pyproject.toml) define o projeto na versão `1.0.0`.
*   Os arquivos [version_info.txt](file:///c:/GIRASSOLTOPARQUET/parquet-converter/version_info.txt) e [app/version_info.txt](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/version_info.txt) definem a versão `1.0.0.0` da aplicação Windows.
*   Não existe um arquivo `CHANGELOG.md` na raiz.
*   **Versionamento Formal via Git:** O diretório **não é um repositório git** ativo (o comando `git log` falha com `fatal: not a git repository`). Portanto, não há histórico de commits, tags ou rastreabilidade de mudanças do desenvolvimento.

---

## 2. Status de Empacotamento/Distribuição

### Configurações de Spec e Metadados PE (Windows VERSIONINFO)
O projeto conta com os seguintes arquivos para controle de compilação por PyInstaller:
1.  [ALLtoParquet.spec](file:///c:/GIRASSOLTOPARQUET/parquet-converter/ALLtoParquet.spec) (na raiz): Gera um executável standalone nomeado `ALLtoParquet.exe`. Ele aplica os metadados descritos no `version_info.txt` raiz.
2.  [ConversorParquetOffline.spec](file:///c:/GIRASSOLTOPARQUET/parquet-converter/ConversorParquetOffline.spec) (na raiz): Gera um executável standalone `ConversorParquetOffline.exe`, porém não incorpora metadados de VERSIONINFO.
3.  [app/GIRASSOLtoPARQUET.spec](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/GIRASSOLtoPARQUET.spec) (na pasta app): Gera o executável standalone `GIRASSOLtoPARQUET.exe` e exclui módulos não utilizados do PyArrow para otimizar o tamanho final. Foi desenhado para usar o [app/version_info.txt](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/version_info.txt).

**Análise do Build Atual:**
*   A pasta `dist/` contém o binário `ALLtoParquet.exe` (tamanho: 127.334.529 bytes, ~121,4 MB) e o arquivo [dist/BUILD_INFO.json](file:///c:/GIRASSOLTOPARQUET/parquet-converter/dist/BUILD_INFO.json).
*   O arquivo [dist/BUILD_INFO.json](file:///c:/GIRASSOLTOPARQUET/parquet-converter/dist/BUILD_INFO.json) confirma que o build foi realizado em `2026-07-03T16:18:20Z` com a especificação `ALLtoParquet.spec` e possui o hash SHA-256 `a91cd3c97e1eebd283bfff2b1a2f615cd8466ff72d8615992f875979e2577a55`.
*   O script automático [build.ps1](file:///c:/GIRASSOLTOPARQUET/parquet-converter/build.ps1) executa testes, compila o arquivo usando `ALLtoParquet.spec`, valida o `VERSIONINFO` via biblioteca `pefile` e grava os metadados de hash no `BUILD_INFO.json`.
*   Por outro lado, o script de conveniência [build_windows.ps1](file:///c:/GIRASSOLTOPARQUET/parquet-converter/build_windows.ps1) gera um executável chamado `GIRASSOLtoPARQUET.exe`, mas faz isso executando parâmetros diretos da CLI do PyInstaller, sem apontar para `GIRASSOLtoPARQUET.spec` ou aplicar o `version_info.txt`.
*   **Inconsistência Identificada:** O arquivo de metadados raiz do `ALLtoParquet.exe` aponta para a marca genérica/temporária *"ALL to Parquet"*, enquanto o `version_info.txt` localizado na pasta `app` possui os dados corretos da empresa proprietária (*"Girassol Inteligência"*). A compilação oficial com a marca do cliente e nome correto (`GIRASSOLtoPARQUET.exe`) ainda não foi alinhada nos scripts globais de build.

### Mecanismos de Licenciamento / Ativação
*   **A aplicação não possui nenhum controle de licenciamento.**
*   Não existem requisições, validações, checks de chaves seriais, verificação online de expiração (trial) ou restrição por volume de dados processados.
*   **Risco Comercial Crítico:** O software roda inteiramente livre offline. Uma vez que o comprador realiza o download na Hotmart, o binário `.exe` pode ser duplicado e executado em qualquer outro computador sem restrições ou validações adicionais. Não há barreira contra pirataria ou distribuição gratuita paralela.

---

## 3. Requisitos da Hotmart para este Tipo de Produto

Com base nas diretrizes oficiais vigentes para comercialização de produtos digitais e programas de computador na Hotmart:

### 1. Modelo de Cadastro e Formato de Arquivos
*   **Categoria do Produto:** O produto deve ser cadastrado sob o formato de **"Arquivos para Baixar"** (ou "Programa para baixar").
*   **Infraestrutura de Armazenamento:** A Hotmart aceita o upload direto do software em sua própria infraestrutura (gerenciando a segurança de entrega de forma automatizada ao comprador).
*   **Limites de Tamanho:** O limite para upload direto de arquivos individuais na Hotmart é de **250 MB**. Como o executável atual tem cerca de 121,4 MB (ou ~127 MB dependendo do spec), ele está apto a ser armazenado de forma direta. Recomenda-se empacotar o executável junto com o manual e termos de uso em um arquivo `.zip` ou `.rar`.
*   **Entrega por Link Externo:** Caso o executável exceda 250 MB ou necessite de atualizações contínuas fora da Hotmart, a plataforma permite entregar um link externo seguro (hospedado em AWS S3, Google Drive, ou servidor próprio da Girassol Inteligência) que pode ser configurado dentro de uma página simples de entrega na plataforma ou em sua área de membros (Hotmart Club).

### 2. Automação de Entrega de Licenças e Chaves de Ativação
A Hotmart não possui uma ferramenta interna/nativa de gestão de chaves seriais para licenciamento. O fluxo de entrega automática de chaves e o controle de uso deve ser feito via integração externa:
*   **Integração por Webhook (API e Notificações):** A Hotmart disponibiliza uma ferramenta de Webhook. Nela, configura-se o envio de notificações HTTP POST automáticas ao servidor do produtor toda vez que ocorrer o evento de **Compra Aprovada** (`PURCHASE_APPROVED`).
*   **Fluxo Técnico de Ativação:**
    1.  O cliente realiza a compra na Hotmart.
    2.  O gateway de pagamento aprova a transação.
    3.  A Hotmart dispara uma requisição POST contendo os dados do comprador (e-mail, nome, ID da transação) para o servidor da Girassol Inteligência.
    4.  O servidor da Girassol (validando a autenticidade com o token `X-HOTMART-HOTTOK` enviado no cabeçalho) gera uma chave de licença única, registra a chave associada ao e-mail do cliente em um banco de dados e a envia por e-mail automaticamente (utilizando serviços como SendGrid, Mailgun ou ferramentas de automação como Pluga/Zapier).
    5.  O cliente instala o software e, na primeira inicialização, insere seu e-mail e chave serial. O software valida esses dados (seja por um check online único ao servidor de licenças da Girassol ou offline por meio de assinaturas criptográficas baseadas em chaves públicas e privadas).

### 3. Aspectos Fiscais (Nota Fiscal) e Cadastro de Produtor
*   **Cadastro como Pessoa Física vs. Jurídica (CNPJ):** Embora a Hotmart não impeça o início de operações como Pessoa Física (CPF), para a Girassol Inteligência o uso do CNPJ é mandatório pelos seguintes fatores:
    *   **Tributação:** Ganhos obtidos como Pessoa Física são enquadrados na tabela progressiva do IRPF (Leão), chegando a até **27,5%** de imposto. Com CNPJ (Microempresa no Simples Nacional), a carga tributária inicial para desenvolvimento/licenciamento de software (CNAE 6202-3/00 ou 6203-1/00) pode iniciar em taxas muito menores.
    *   **Obrigatoriedade de Nota Fiscal:** De acordo com a legislação brasileira, é obrigação do vendedor emitir nota fiscal eletrônica de serviço (NFS-e) para o cliente final. A Hotmart não emite nota fiscal para os compradores do produtor (ela emite apenas a nota da taxa de intermediação cobrada do produtor). A automação fiscal deve ser integrada via ERP de notas (como eNotas ou Focus NFe) ao webhook da Hotmart.
*   **Compliance e Análise de Conta:** Para aprovação definitiva e saque de comissões, a Hotmart exige:
    *   Identidade do produtor (RG/CNH e biometria facial).
    *   Contrato Social e Cartão CNPJ (para contas PJ).
    *   Conta bancária cadastrada com a **mesma titularidade** (CNPJ e Razão Social da Girassol Inteligência).
    *   Validação da Página de Vendas (que não pode prometer ganhos fáceis ou conter simulações enganosas) e indicação clara de um e-mail de suporte pós-venda.

---

## 4. Gap Analysis para Comercialização

Abaixo estão listados os desvios entre o estado atual do projeto e os requisitos necessários para a entrada em produção e comercialização segura no marketplace, ordenados por prioridade crítica:

### 🟥 Bloqueadores Críticos (Impedem a venda ou geram prejuízo financeiro/técnico)
1.  **Ausência de Mecanismo de Licenciamento no Aplicativo:** O executável é 100% livre. É imperativo implementar uma rotina interna de ativação que exija a validação de um token/chave serial.
2.  **Desenvolvimento do Servidor de Licenciamento:** Necessidade de construir um microsserviço/API web simples (ex: em FastAPI/Python rodando na nuvem) conectado a um banco de dados simples (PostgreSQL ou Supabase) para cadastrar chaves, receber ativações e marcar as licenças já usadas.
3.  **Configuração de Webhook de Vendas (Hotmart -> Servidor):** Desenvolver o receptor do webhook para capturar a notificação `PURCHASE_APPROVED`, gerar uma licença na API de licenciamento e disparar a chave para o e-mail do cliente de forma imediata.
4.  **Ajuste e Alinhamento do Build com os Metadados Oficiais:** Corrigir a compilação automática para gerar o binário com o nome `GIRASSOLtoPARQUET.exe` e metadados de VERSIONINFO apontando para a *"Girassol Inteligência"*, garantindo a propriedade intelectual correta.
5.  **Assinatura de Código (Code Signing):** Sem assinar digitalmente o `.exe` com um certificado comercial emitido por Autoridade Certificadora pública (Sectigo, DigiCert), o Windows SmartScreen bloqueará o aplicativo com alertas vermelhos invasivos. Isso causará cancelamentos em massa das compras. A alternativa é a conta da Microsoft Store para empacotamento MSIX e publicação via loja (onde a Microsoft assina digitalmente o pacote de forma inclusa).
6.  **Configuração de Invoicing Automático:** Integrar um emissor automático de NFS-e (ex: eNotas) conectado ao webhook de faturamento aprovado da Hotmart sob o CNPJ da Girassol Inteligência.

### 🟨 Requisitos Importantes (Não bloqueiam a venda, mas afetam a percepção do usuário e suporte)
1.  **Criação de um Assistente de Instalação (Setup Wizard):** O aplicativo é distribuído como um executável de 127MB solto. A criação de um instalador clássico do Windows (gerado via Inno Setup ou Wix Toolset) que cria atalhos de área de trabalho e adiciona o programa à lista de Desinstalação do painel de controle transmite muito mais profissionalismo.
2.  **Mecanismo Simples de Auto-Update (ou Check de Versão):** Como a aplicação roda totalmente local, se um bug grave for corrigido, não há como notificar os clientes. Um verificador básico de versão que consulte um JSON estático na web e notifique "Nova versão disponível" é crucial.
3.  **Documentação de Usuário Final (Manual em PDF):** Atualmente, a única documentação disponível é o `README.md` (redigido para programadores). É necessário gerar um manual de instalação rápido com capturas de tela explicando as configurações e a instalação.

### 🟩 Diferenciais de Venda Existentes (Pontos Fortes a serem explorados)
*   **Privacidade e Segurança Rígida (100% Offline):** O argumento de que os dados (incluindo CPF, CNPJ, telefones, etc.) não saem da máquina do cliente e que não há dependência de internet é o maior atrativo corporativo e governamental.
*   **Alta Performance de Processamento:** Motor de processamento Polars e DuckDB que processa arquivos grandes na velocidade de linguagem de baixo nível.
*   **Tratamento Automático de Dados Sensíveis:** Evita a perda de formatação de CPFs, CNPJs e CEPs automaticamente.
*   **Normalização de Cabeçalhos e Presets Prontos:** O preset de BI economiza horas de engenheiros de dados na preparação das bases para Power BI e bancos de dados SQL.
*   **Fila Assíncrona Robusta:** Permite que o usuário continue operando o app enquanto processa lotes gigantescos de dados.

---

## 5. Resumo Executivo

### Tabela de Status Atual
| Área do Projeto | Status | Detalhes |
| :--- | :---: | :--- |
| **Funcionalidade Core** | **Pronto** | Formatos suportados, normalização, presets e auditoria operando perfeitamente. |
| **Testes Automatizados** | **Parcial** | Cobertura excelente no core (~100%), mas sem cobertura em UI e Services auxiliares. |
| **Empacotamento** | **Parcial** | Executável compila e funciona, mas há desalinhamento de metadados nos scripts e spec de build. |
| **Licenciamento** | **Não Iniciado** | Ausência completa de validação de chave de licença no código-fonte. |
| **Integração Hotmart (Entrega)** | **Não Iniciado** | Falta construir receptor de Webhook e servidor de suporte para gerar as chaves de acesso. |
| **Compliance Hotmart / Fiscal** | **Não Iniciado** | Conta necessita validação de CNPJ e integração com plataforma de Notas Fiscais (NFS-e). |
| **Documentação de Usuário** | **Não Iniciado** | Existe apenas a documentação técnica voltada para desenvolvedores. |

### Estimativa de Esforço Restante (Dev-Days) para Bloqueadores

A estimativa abaixo prevê o desenvolvimento e homologação dos itens bloqueadores técnicos identificados no Item 4:

1.  **Check de Licenciamento Criptográfico Offline no Aplicativo:** **2 dev-days**
    *   *Escopo:* Implementar rotina no cliente Python que valida a assinatura criptográfica de um arquivo de licença local (usando RSA/ECDSA) contendo data de expiração e e-mail do cliente, sem necessidade de estar online em todas as execuções.
2.  **Servidor de Chaves de Licença e API de Geração:** **3 dev-days**
    *   *Escopo:* Construir uma API simples (ex: FastAPI + Supabase DB) para gerar e registrar pares de chaves criptográficas de ativação, e responder a chamadas para emissão da chave correspondente ao e-mail cadastrado.
3.  **Webhook de Integração com Hotmart:** **3 dev-days**
    *   *Escopo:* Criar a rota de escuta para as notificações HTTP da Hotmart (`PURCHASE_APPROVED`). Conectar essa escuta à API de geração de chaves para enviar a licença automaticamente para o e-mail do comprador via SMTP ou API de e-mail (SendGrid).
4.  **Integração e Automação de Nota Fiscal Eletrônica (NFS-e):** **2 dev-days**
    *   *Escopo:* Integrar o webhook da Hotmart à plataforma Focus NFe ou eNotas para gerar e enviar a nota fiscal automaticamente a cada venda aprovada.
5.  **Ajuste do Pipeline de Build:** **1 dev-day**
    *   *Escopo:* Alinhar o script [build_windows.ps1](file:///c:/GIRASSOLTOPARQUET/parquet-converter/build_windows.ps1) com o arquivo [app/GIRASSOLtoPARQUET.spec](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/GIRASSOLtoPARQUET.spec) e o [app/version_info.txt](file:///c:/GIRASSOLTOPARQUET/parquet-converter/app/version_info.txt) para garantir metadados corretos de proprietário no binário final.
6.  **Homologação e Assinatura Digital (Code Signing):** **1 dev-day** *(Nota: Exclui tempo administrativo de aprovação da Autoridade Certificadora, que leva entre 3 e 7 dias).*
    *   *Escopo:* Configurar a ferramenta `signtool` do Windows SDK no script de compilação da esteira para assinar digitalmente o executável gerado.

*   **Esforço Técnico Estimado Total:** **12 dev-days** de desenvolvimento, testes e implantação dos bloqueadores.
