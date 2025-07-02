# ixc_api

Cliente Python para integração com a API do sistema IXC Provedor.

## 📦 Instalação

Clone o repositório e instale localmente:

```bash
pip install .
```

## 🧾 Requisitos
- Python >= 3.8
- `requests`
- `pandas`

## 🚀 Como usar

```python
from ixc_api import IXC

# Obter informações de clientes com ID maior que 0
dados = IXC.get_info_IXC('cliente', col='id', op='>', value=0)
print(dados)
```

### Editar um cliente
```python
IXC.edit_info_IXC('cliente', id=123, payload={"bairro": "Centro"})
```

### Fechar uma Ordem de Serviço
```python
IXC.close_OS(id_os=456, mensagem="Problema resolvido", id_atendente=1)
```

## 📁 Estrutura recomendada

```
ixc_api/
├── ixc_api/
│   └── __init__.py        # contém a classe IXC
├── setup.py
├── README.md
├── LICENSE
```

## 📝 Licença
MIT

## 🤝 Contribuindo
Pull requests são bem-vindos!
