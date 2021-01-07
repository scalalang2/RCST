def account_to_shard(address: str, number_of_shard):
    return int(address, 16) % number_of_shard


if __name__ == "__main__":
    print(account_to_shard("0x043f3579201977dfed8ae46bc9f1561c92b6cfac",20))