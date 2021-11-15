# Code to plot the computation time of the function


import matplotlib.pyplot as plt

file = open("CalculationTime.txt", 'r')
times = file.readlines()

p1 = []
p2 = []
for i in range(len(times)):
    p1.append(times[i][0])
    p2.append(times[i][1])

plt.plot(p1)
#plt.plot(p2)

#plt.plot(times[1])
#plt.axhline(y=0.0003, color='r', linestyle='-')
plt.show()
