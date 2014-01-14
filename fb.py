import sys

def fb(inLine):
    first=line[0]
    second=line[1]
    max=line[2]
    return " ".join([["F" if i%first==0]).join(["B" if i%second==0]).join([str(i) if i%first!=0&&i%second!=0]) for i in range(1,n+1)])

if(__name__=="__main__"):
    filename=sys.argv[1]

    f=open(filename)
    data=f.read()
    f.close()

    print "\n".join([fizzbuzz([int(j) for j in i.split(" ")]) for i in data.split("\n")[:-1]])
