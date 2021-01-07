def account_to_group(address: str, number_of_group):
    return int(address, 16) % number_of_group


if __name__ == "__main__":
    print(account_to_group("0x043f3579201977dfed8ae46bc9f1561c92b6cfac",100))