#Bug Fix Implemeted for closing/opening times   #Flag by default is set to restaurant open

from datetime import date, datetime
from pytz import timezone
import pytz

flag1 = 0    #Flag to check if the given time is a restaurant working time
x = str(datetime.now(pytz.timezone('US/Central')))  #import time
data = x.split()
k = data[1].split(":")
#s = int(k[0] + k[1]) #time
s = 1330             #A random time in which the restaurant is open
p = datetime.now(pytz.timezone('US/Central')).weekday() #weekday, monday is 0 and so on
          
#if case for closing times
def checktimings(p, s, flag1):                 #A function to check whether the restaurant is open
    if(flag1 == 0):
        if ((p == "0" or "2" or "3" or "5" or "6")):
            if(s > 1129 and s < 1531) or (s > 1729 and s < 2131):           
                flag1 = 0
            else:
                flag1 = 1                

        elif(p == "4"):
            if (s >= 1130 and s<= 1530) or (s>=1730 and s<=2230):
                flag1 = 0
            else:
                flag1 = 1
                 
        else:
            flag1 = 1

    return flag1

    
#print(checktimings(p, s, flag1)) 
