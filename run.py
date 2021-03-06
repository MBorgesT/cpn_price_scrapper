import sys
from miner.scrapper import Scrapper


if __name__ == '__main__':
    try:
        argv = sys.argv
        if len(argv) > 2:
            raise Exception('This program can only receive one or no arguments')
        elif len(argv) == 2:
            jsons_path = argv[1]
            json_flag = True
        else:
            json_flag = False

        scrapper = Scrapper(jsons_path if json_flag else None)
        scrapper.scrap()
    except Exception as e:
        print('\n\n')
        print(e)

    input('\n\n\nPress any key to end the program')
