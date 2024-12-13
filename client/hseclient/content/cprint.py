import colorama

def p_error(text):
    print(f"{colorama.Fore.RED}Ошибка:{colorama.Style.RESET_ALL} {text}")

def p_success(text):
    print(f"{colorama.Fore.GREEN}{text}{colorama.Style.RESET_ALL}")