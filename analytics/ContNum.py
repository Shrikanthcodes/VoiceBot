import re

pattern1 = r"^[1-9]{7}$"  # xxx xxxx format
pattern2 = r"^[1-9]{10}$"  # xxx xxx xxxx format
pattern3 = r"^\s*[1]\d{10}\s*$"   # 1 xxx xxx xxxx format
pattern4 = r"^\+[1][0-9]{10}$" # +1 xxx xxx xxxx format

reg1 = re.compile(pattern1)
reg2 = re.compile(pattern2)
reg3 = re.compile(pattern3)
reg4 = re.compile(pattern4)
#x = str(input())

def converto(h):
    if int(bool(reg1.match(h))) == 1:
        h = "+1469" + h
        return h
                
    elif int(bool(reg2.match(h))) == 1:
        h = "+1" + h
        return h
        
    elif int(bool(reg3.match(h))) == 1:
        h = "+" + h
        return h
    
    elif int(bool(reg4.match(h))) == 1:
        return h
    else:
        h = "+11111111111"
        return h
                
#print(converto(x))


