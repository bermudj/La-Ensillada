'''
Fizz buzz problem
Jesús A Bermúdez Silva
03/03/21
'''

for i in range(100):
    if (i % 3 == 0) and (i % 5 == 0):
        print("fizzbuzz")
    elif (i % 3 == 0):
        print("fizz")
    elif (i % 5 == 0):
        print("buzz")
    else:
        print(i)


