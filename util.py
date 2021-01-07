import numpy as np
from sklearn.preprocessing import normalize

def account_to_group(address: str, number_of_group):
    return int(address, 16) % number_of_group


if __name__ == "__main__":
    x = np.array([[1,2,3,4,5], [3,4,5,6,7], [8,9,10,11,12]])
    print(normalize(x.reshape(1,-1), norm='max').reshape(3, 5))
    print(account_to_group("0x043f3579201977dfed8ae46bc9f1561c92b6cfac",100))