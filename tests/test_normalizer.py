from app.core.normalizer import normalize_column_name, normalize_columns

def test_normalize_column_name():
    assert normalize_column_name("NOME COMPLETO") == "nome_completo"
    assert normalize_column_name("DATA DE NASCIMENTO") == "data_de_nascimento"
    assert normalize_column_name("E-MAIL") == "email"
    assert normalize_column_name("CPF/CNPJ") == "cpf_cnpj"
    assert normalize_column_name("  Ações & Opções!  ") == "acoes_opcoes"
    assert normalize_column_name("") == "coluna_sem_nome"

def test_normalize_columns_duplicates():
    cols = ["Nome", "Nome", "E-Mail", "Nome Completo", "Nome Completo"]
    normalized, mapping = normalize_columns(cols)
    
    assert normalized == ["nome", "nome_1", "email", "nome_completo", "nome_completo_1"]
    assert mapping["Nome"] == "nome_1"  # Matches the last seen element mapped value or maps sequentially
    assert len(normalized) == 5
    assert len(set(normalized)) == 5
