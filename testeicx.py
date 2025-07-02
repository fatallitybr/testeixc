import requests
import base64
import json
import csv
from datetime import datetime
from pprint import pp
from Tokens import *
import pandas as pd

class IXC:
    DEBUG = True  # Define para False em produção

    @staticmethod
    def _log(msg):
        if IXC.DEBUG:
            print(msg)

    @staticmethod
    def _get_headers(ixcsoft=''):
        encode = base64.b64encode(IXC_token.encode('utf-8')).decode('utf-8')
        return {
            'ixcsoft': ixcsoft,
            'Authorization': "Basic " + encode,
            'Content-Type': 'application/json'
        }

    @staticmethod
    def send_to_IXC(tab, payload):
        IXC._log(f'Enviando para o IXC: {payload}')
        url = IXC_url + tab
        headers = IXC._get_headers()

        response = requests.post(url, data=json.dumps(payload), headers=headers)
        try:
            return response.json() if response.status_code == 200 else "Error: " + response.text
        except:
            return "Error: resposta inválida"

    @staticmethod
    def parameters_format(parameters):
        cabecalho = ['TB', 'OP', 'P']
        param = [dict(zip(cabecalho, p)) for p in parameters]
        IXC._log(param)
        return param

    @staticmethod
    def create_log(response, diretory='', modo='w+'):
        now = datetime.now().strftime("%d-%m-%Y %Hh%Mm%Ss")
        path = diretory or fr'C:\Users\Financeiro\OneDrive\dev-bfp\GitHub\IXC_API\logs\log_IXC_{now}.csv'
        with open(path, modo, newline='', encoding='utf-8') as log:
            writer = csv.writer(log)
            if modo == 'w+':
                writer.writerow(['id_origem', 'type', 'message', 'atualiza_campos'])
            for x in response:
                writer.writerow([
                    x.get('id_origem', ''),
                    x.get('type', ''),
                    x.get('message', ''),
                    x.get('atualiza_campos', '')
                ])
        IXC._log(f"Log criado em: {path}")

    @staticmethod
    def swap(value_to_swap, source_table, table_column, value_return):
        data = IXC.get_info_IXC(source_table, table_column, '=', value_to_swap)['registros'][0]
        return data[value_return]

    @staticmethod
    def replace_manual(data, replace_list):
        new_data = {'page': data['page'], 'total': data['total'], 'registros': []}
        for dados in data['registros']:
            for campo, valor in dados.items():
                for key, value in replace_list.items():
                    if campo == key:
                        for y in value:
                            if valor == y[0]:
                                dados[campo] = y[1]
            new_data['registros'].append(dados)
        return new_data

    @staticmethod
    def update_date(date):
        try:
            if date in ['0000-00-00', '0000-00-00 00:00:00']:
                return ''
            if len(date) == 10:
                return datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
            if len(date) == 19:
                return datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
        except:
            return date
        return date

    @staticmethod
    def type_verificator(payload):
        data_formated = {}
        for key, value in payload.items():
            if isinstance(value, str) and len(value) in [10, 19] and '-' in value:
                data_formated[key] = IXC.update_date(value)
        payload.update(data_formated)
        return payload

    @staticmethod
    def edit_data_IXC(table, id_list, payload):
        array_log = []
        for x in id_list:
            edited = IXC.edit_info_IXC(table, x, payload)
            IXC._log(f"ID: {x} == {edited.get('type')} - {edited.get('message')}\n")
            edited['id_origem'] = x
            array_log.append(edited)
        IXC.create_log(array_log)

    @staticmethod
    def return_list(response, return_list):
        registros_filtrados = []
        for dados in response['registros']:
            registros_filtrados.append({k: v for k, v in dados.items() if k in return_list})
        response['registros'] = registros_filtrados
        return response

    @staticmethod
    def file_upload_ixc(id_cliente, arquivo, tipo_arquivo, nome_arquivo):
        url = IXC_url + 'cliente_arquivos'
        headers = IXC._get_headers()
        files = {
            'local_arquivo': (f"{nome_arquivo}.{tipo_arquivo}", arquivo)
        }
        payload = {
            'id_cliente': id_cliente,
            'nome_arquivo': f"{nome_arquivo}.{tipo_arquivo}",
            'descricao': nome_arquivo
        }

        response = requests.post(url, headers=headers, data=payload, files=files)
        try:
            return response.json() if response.status_code == 200 else "Error: " + response.text
        except:
            return "Error: resposta inválida"

    @staticmethod
    def get_info_IXC(tab, col='id', op='>', value=0, return_list='', param='', pag="1", lin="10000000",
                     ord_camp='id', order='asc', manual_replace=''):
        url = IXC_url + tab
        headers = IXC._get_headers('listar')
        payload = {
            'qtype': col, 'query': value, 'oper': op,
            'page': pag, 'rp': lin,
            'sortname': ord_camp, 'sortorder': order
        }
        if param:
            payload['grid_param'] = json.dumps(IXC.parameters_format(param))

        IXC._log(f'\nTabela: "{tab}"\nParâmetros: {payload}\n')

        response = requests.post(url, data=json.dumps(payload), headers=headers)
        try:
            if response.status_code == 200:
                data = response.json()
                if int(data['total']) > 0:
                    data['registros'] = [IXC.type_verificator(r) for r in data['registros']]
                    data = IXC.replace_manual(data, manual_replace) if manual_replace else data
                    return IXC.return_list(data, return_list) if return_list else data
                else:
                    return False, '***Sem registros - Verifique os parâmetros***'
            else:
                return "Error: " + response.text
        except:
            return False, 'Erro ao processar a resposta da API'

    @staticmethod
    def edit_info_IXC(tab, id, payload):
        IXC._log(f'Atualizando ID: {id} da tabela {tab}')
        try:
            dados = dict(IXC.get_info_IXC(tab, col='id', op='=', value=id)['registros'][0])
            dados.update(payload)
            payload1 = IXC.type_verificator(dados)
            dados.update(payload1)

            url = f'{IXC_url}{tab}/{id}'
            headers = IXC._get_headers()
            response = requests.put(url, data=json.dumps(dados), headers=headers)
            return response.json() if response.status_code == 200 else "Error: " + response.text
        except Exception as e:
            return f"Exception: {e}"

    @staticmethod
    def close_OS(id_os, mensagem, id_atendente):
        url = IXC_url + 'su_oss_chamado_fechar'
        headers = IXC._get_headers()
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        payload = {
            'id_chamado': id_os,
            'mensagem': mensagem,
            'status': 'F',
            'id_atendente': id_atendente,
            'id_tecnico': id_atendente,
            'data_inicio': date,
            'data_final': date,
        }
        response = requests.post(url, headers=headers, data=payload)
        return response.json()

    @staticmethod
    def desbloqueio_confianca(id_contrato):
        url = IXC_url + 'desbloqueio_confianca'
        headers = IXC._get_headers()
        payload = {'id': id_contrato}
        response = requests.post(url, headers=headers, data=payload)
        return response.json()

    @staticmethod
    def liberar_temp(id_contrato):
        url = IXC_url + 'cliente_contrato_btn_lib_temp_24722'
        headers = IXC._get_headers()
        payload = {'id': id_contrato}
        response = requests.post(url, headers=headers, data=payload)
        return response.json()

if __name__ == "__main__":
    print('IXC_Main')
