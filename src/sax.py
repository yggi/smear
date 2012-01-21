import math


def normalize(xs, epsilon):
    #epsilon
    if max(xs) - min(xs) <= epsilon:
        return [0 for x in xs]
    
    avg = float(sum(list(xs)))/len(xs)
    avgd = [float(x)-avg for x in xs]
    sigma = math.sqrt(sum([x**2 for x in avgd])/len(avgd))
    return [x/sigma for x in avgd]
        
def paa(xs, word_size):
    return [sum(slice) / len(slice) for slice in slices(xs,word_size)]
    
    #if len(xs)%word_size == 0:
    #    n = len(xs)/word_size
    #else:
    #    n = len(xs)/word_size+1
    # 
    #return [sum(chunk) / len(chunk) for chunk in chunks(xs, n)]
    #r = []
    #for chunk in chunks(xs, len(xs) / self.word_size + 1):
    #    r.append(sum(chunk) / len(chunk))
    #return r

def sax(xs, alphabet_size):
    breakpoints = {
        3: (-0.43,0.43),
        4: (-0.67,0,0.67),
        5: (-0.84,-0.25,0.25,0.84),
        6: (-0.97,-0.43,0,0.43,0.97),
        7: (-1.07,-0.57,-0.18,0.57,1.07),
    }
    alphabet="ABCDEFGHIJ"
    
    r = ""
    for x in xs:
        i = 0
        done = False
        for b in breakpoints[alphabet_size]:
            if x <= b:
                r+= alphabet[i]
                done = True
                break
            i+=1
        if not done:
            r+= alphabet[alphabet_size-1]
    return r

def distance(asrc, bsrc, ref = None):
    a = "".join(asrc)
    b = "".join(bsrc)
    
    if not len(a)==len(b):
        raise Exception("Can't compare SAX-Strings of different length. Length a: %s Length b:%s"%(len(a),len(b)))
    
    d=0
    for i in range(len(a)):
        d+=(ord(a[i])-ord(b[i]))**2
    dist = math.sqrt(d)
    if ref is not None:
        return 1/float(ref)*dist
    else:
        return dist

def chunks(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def slices(l, n):
    smallslice = len(l)/n
    bigslice = smallslice +1
    bigslices = len(l)%n
    out = []
    for i in range(bigslices):
        out.append(l[i*bigslice:(i+1)*bigslice])
    for j in range(n-bigslices):
        out.append(l[bigslice*bigslices+j*smallslice:bigslice*bigslices+(j+1)*smallslice])
    return out

def multisaxify(xs, *args):
    sax = ""
    for x in xs:
        sax += saxify(x, args)
    return sax
            
def saxify(xs, epsilon = 50, word_size = 7, alphabet_size = 5):
    nxs = normalize(xs, epsilon)
    pax = paa(nxs, word_size)
    sx = sax(pax, alphabet_size)
    return sx