import sys
from miner.scrapper import Scrapper


if __name__ == '__main__':
    while True:
        print('Selecione o país a ser escaneado:')
        print('1 - Portugal')
        print('2 - Israel')
        print('3 - Hong Kong')
        op = input('Opção: ')

        if op == '1':
            country_param = 'portugal'
            break
        elif op == '2':
            country_param = 'israel'
            break
        elif op == '3':
            country_param = 'hk'
            break
        else:
            print('\nOpção inválida. Favor selecionar alguma das listadas.\n')

    try:
        print('\nLoading modules...')
        argv = sys.argv
        if len(argv) > 2:
            raise Exception('This program can only receive one or no arguments')
        elif len(argv) == 2:
            jsons_path = argv[1]
            json_flag = True
        else:
            json_flag = False

        scrapper = Scrapper(country_param, jsons_path if json_flag else None)
        if country_param == 'portugal':
            scrapper.scrap_portugal()
        elif country_param == 'israel':
            scrapper.scrap_israel()
        elif country_param == 'hk':
            scrapper.scrap_hk()
    except Exception as e:
        print('\n\n')
        raise e

    input('\n\nPressione ENTER tecla para encerrar o programa ')
