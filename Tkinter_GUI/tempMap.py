import matplotlib.pyplot as plt
import numpy as np

plt.ion()

class tempMap():

    def __init__(self): 
       self.X,self.Y = np.meshgrid(np.linspace(0, 12, 13), np.linspace(0, 4, 13), indexing = "xy")
       self.Z = (self.X*self.Y*0) + 23
       self.figure, self.ax = plt.subplots()
       self.plot1 = self.ax.contourf(self.X, self.Y, self.Z, vmin = 23, vmax = 100, cmap='jet')
       self.ax.axis('scaled')
       self.cbar = self.figure.colorbar(self.plot1)
       self.count = 1

    def updateTemps(self,t1,t2,t3,t4,t5,t6):
        self.count = self.count +1
        self.Z[1*3, 3] = t1
        self.Z[3*3, 3] = t2
        self.Z[2*3, 5] = t3
        self.Z[2*3, 7] = t4
        self.Z[1*3, 9] = t5
        self.Z[3*3, 9] = t6
        
        self.cbar.remove()
        self.plot1 = self.ax.contourf(self.X, self.Y, self.Z, vmin = 23, vmax = 100, cmap='jet')   
        self.cbar = self.figure.colorbar(self.plot1) 
               
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        print(self.count)
        plt.pause(0.25)  
        
    def updateOneTemp(self,t3):
        self.count = self.count +1

        self.Z[2*3, 5] = t3

        self.cbar.remove()
        self.plot1 = self.ax.contourf(self.X, self.Y, self.Z, vmin = 23, vmax = 100, cmap='jet')   
        self.cbar = self.figure.colorbar(self.plot1) 
               
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        print(self.count)
        plt.pause(0.10)  
             
        
         

slide = tempMap()

for i in range(50):
    slide.updateTemps(23+i*2+1,23+i*2+3,23+i*2,23+i*2+8,23+i,23+i*2+1)

# for i in range(10):
#     slide.updateTemps(41+i,42+i,43+i,44+i,45+i,46+i)
#     time.sleep(2)
