# even fibonaccy numbers

fnless1 = 1
fnless2 = 0
for _ in range(40):
    fn = fnless1 + fnless2
    if fn % 2 == 0:
        print (fn)
    fnless2 = fnless1
    fnless1 = fn

