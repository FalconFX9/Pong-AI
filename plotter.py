# Code to plot the computation time of the function


import matplotlib.pyplot as plt

file = open("CalculationTime.txt", 'r')
times = file.readlines()

plt.plot(times[8000:10000])
#plt.axhline(y=0.0003, color='r', linestyle='-')
plt.show()
