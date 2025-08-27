
slovar = {'1.1': 10, '1.2': 20}

ab = []
cisla = []

for k, v in slovar.items():
    ab.append(k)
    cisla.append(v)
    
    
print(ab)
print(cisla)

print(list(slovar.keys())[0])