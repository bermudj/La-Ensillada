'''
Hailstone exercise

    If   n   is     1     then the sequence ends.
    If   n   is   even then the next   n   of the sequence   = n/2
    If   n   is   odd   then the next   n   of the sequence   = (3 * n) + 1
'''

def hailstone(n):
    hs = [n]
    h = n
    while True:
        if h == 1:
            return hs

        if n % 2 == 0:
            h = n // 2
        else:
            h = 3 * n + 1
        hs.append(h)
        n = h

max = len(hailstone(1))
n = 1
for i in range(2, 100000):
    l = len(hailstone(i))
    if l > max:
        max = l
        n = i

print ("Sequence :", n, "Length: ", max)
