

def decode(fn = 'c:/users/ralph/desktop/testmoves.txt'):
    with open(fn, 'r') as f:
        data = f.read()
    dataspl = data.split('\n')
    histo = {}
    for item in dataspl:
        _ , list_str = item.split(" [", 1)
        list_part = eval("[" + list_str)
        relevant = list_part[-1]
        if relevant in list(histo):
            histo[relevant] += 1
        else:
            histo[relevant] = 1
    sorted_by_value_desc = {k: v for k, v in sorted(histo.items(), key=lambda item: item[1], reverse=True)}

    pass

if __name__ == '__main__':
    decode()




