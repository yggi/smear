import os
import serial
import time
import optparse
import struct
import wave
import math
from enthought.traits.api import HasTraits, Instance, List, Property, List, Array, Int, String, Generic,Float, Str
import sax
from threading import Thread

class RawData(HasTraits,Thread):

    data = List
    alphabet_size = Int(5)
    word_size = Int(10)
    epsilon = Int(50)

    id1 = Str()
    id2 = Str()
    id3 = Str()

    dist_max = Float(0.3)
    window_step = Int(0)
    window_min = Int(0)
    window_max = Int(0)
    data_transposed = Property(Array, depends_on=["data"])
    data_normalized = Property(Array, depends_on=["data_transposed", "epsilon"])
    data_paaed = Property(Array, depends_on=["data_normalized", "word_size"])
    data_saxed = Property(String, depends_on=["data_paaed", "alphabet_size"])

    length = Property(Int, depends_on=["data"])
    #sax = Property(SAX, depends_on=["data, alphabet_size, word_size, epsilon"])

    def __init__(self, filename="../td/exercise-1a.arff", data=None):
        Thread.__init__(self)
        #self.data = List
        if data:
            self.data =data
            self.window_min = self.length
            self.window_max = self.length
            return

        if filename[:4] == "/dev":

            self.is_serial = True
            self.serial = serial.Serial(filename,115200,timeout=1)

        elif filename[-3:] == "wav":
            self.data = self.load_wav(filename)
            self.id1 = filename[-6]
            self.id2 = filename[-5]
            self.window_min = self.length
            self.window_max = self.length
        elif filename[-4:] == "arff":
            self.id1 = filename[-7]
            self.id2 = filename[-6]
            self.data = self.load_arff(filename)
            self.window_min = self.length
            self.window_max = self.length
        elif filename[-3:] == "sax":
            self.load_sax(filename)
        else:
            print filename
            raise Exception("Filetype not supported")

    def run(self):
        #self.data=[[],[],[],[],[],[]]
        while(True):
            line = self.serial.readline()
            if line != "":
                try:
                    vals = map(int,line.strip().split(" "))
                except KeyboardInterrupt:
                    raise
                except:
                    continue
                if len(vals)==6:
                    self.data.append(vals)

    def __getitem__(self,slice):
        return RawData(data=self.data.__getitem__(slice))


    def load_arff(self, filename):
        file = open(filename,"r")

        line = ""
        # ignore everything before DATA
        while line != "@DATA\n":
            line = file.readline()

        rows = []

        while line:
            line = file.readline()
            if line.strip():
                rows.append(map(int,line.strip().split(",")))
        return rows

    def load_wav(self, file):
        w = wave.open (file, "r")

        rows =  []
        for rn in xrange(w.getnframes()):
            waveData = w.readframes(1)
            data = struct.unpack("hhhhhh", waveData)
            data = map(lambda x:x/10,list(data))
            rows.append(data)
        return rows

    def load_sax(self, file):
        file = open(file, "r")
        line = "DUMMY"
        while line:
            line = file.readline()
            if line == "": break
            (arg, val)= line.strip().split("=")
            if arg == "sax": s = val
            elif arg == "id1": self.id1 = val
            elif arg == "id2": self.id2 = val
            elif arg == "id3": self.id3 = val
            elif arg == "window_min": self.window_min = int(val)
            elif arg == "window_max": self.window_max = int(val)
            elif arg == "window_step": self.window_step = int(val)
            elif arg == "epsilon": self.epsilon = int(val)
            elif arg == "word_size": self.word_size = int(val)
            elif arg == "alphabet_size": self.alphabet_size = int(val)
            elif arg == "dist_max": self.dist_max = float(val)
            elif arg == "data": self.data.append([int(x) for x in val.split(",")])

        mys = "".join(self.data_saxed)
        if not s == mys:
            #raise Exception("Loaded string (%s) does not mach excepted string (%s)"%(s,mys))
            print "Loaded string (%s) does not mach excepted string (%s)"%(s,mys)
        print "done"

    def save_wav(self, file):
        w = wave.open(file, "w")
        w.setnchannels(6)
        w.setsampwidth(2) #BYTES
        w.setframerate(4400)
        w.setnframes = len(self.data)

        for row in self.data:
            for entry in row:
                w.writeframes(struct.pack('h', int(entry)*10))
        w.close()

    def save_sax(self, file):
        file = open(file, 'w')

        file.write("sax=%s\n"%("".join(self.data_saxed)))
        file.write("id1=%s\n"%(self.id1))
        file.write("id2=%s\n"%(self.id2))
        file.write("id3=%s\n"%(self.id3))
        file.write("data_size=%s\n"%(len(self.data)))
        file.write("window_min=%s\n"%(self.window_min))
        file.write("window_max=%s\n"%(self.window_max))
        file.write("window_step=%s\n"%(self.window_step))
        file.write("epsilon=%s\n"%(self.epsilon))
        file.write("word_size=%s\n"%(self.word_size))
        file.write("alphabet_size=%s\n"%(self.alphabet_size))
        file.write("dist_max=%s\n"%(self.dist_max))
        for row in self.data:
            #print row
            file.write("data=%s\n"%(", ".join(map(str,row))))
        file.close()

    def __str__(self):
        return "SAX: %s-%s-%s (%s)"%(self.id1,self.id2,self.id3," ".join(self.data_saxed))

    def _get_data_normalized(self):
        return [sax.normalize(dim, self.epsilon) for dim in self.data_transposed]

    def _get_data_paaed(self):
        return [sax.paa(dim, self.word_size) for dim in self.data_normalized]

    def _get_data_saxed(self):
        return [sax.sax(dim, self.alphabet_size) for dim in self.data_paaed]

    def collisions(self, other):
        #self.dist_max = 0.2

        step = 5
        pointer = 0
        r = []
        window = self.window_min

        while pointer+window <= len(other.data):
            slice = other[pointer:pointer+window]
            slice.epsilon = self.epsilon
            slice.alphabet_size = self.alphabet_size
            slice.word_size = self.word_size

            #s = SAX(slice)
            d = sax.distance(self.data_saxed, slice.data_saxed, (self.alphabet_size-1)*self.word_size)

            if d <= self.dist_max:
                #We have found a match, yay!
                col = "@%s(%s):%s"%(pointer,window,d)
                print col
                r.append(col)
                #move one (current) window ahead (= the match) and reset the window size
                pointer += window
                window = self.window_min
            if self.window_step == 0 or window + self.window_step > self.window_max or pointer + window + self.window_step > len(other.data):
                #No window stepping or the next window will be bigger than window_max or out of the data
                #move one step and reset the window size
                pointer += step
                window = self.window_min
            else:
                #Enlarge the window
                window += self.window_step
        return r

    def _get_data_transposed(self):
        return(zip(*self.data))

    def _get_length(self):
        return(len(self.data))

class MultiSAXComparator():
    def __init__(self, saxes, data, step):
        self.saxes = saxes
        self.data = data
        self.step = step

        self.windows = []
        self.lenmax = 0
        self.matches_dict = {}
        for s in self.saxes:
            self.matches_dict[s.id1]=0
            len = s.window_min
            while len <= s.window_max:
                self.windows.append({"sax": s, "length": len})
                if len > self.lenmax:
                    self.lenmax = len
                len += self.step

    def compare(self):
        pointer = 0
        candidates = []
        matches = []

        lastrep = 0
        while 1:
            if self.data.is_serial:
                #print "Pos: %s Len: %s"%(pointer, self.data.length)
                while pointer+self.lenmax > self.data.length:
                    #print "Waiting for data. Pos: %s Len: %s"%(pointer, self.data.length)
                    time.sleep(0.1)
            elif pointer > self.data.length:
                print "EOF"
                break

            if self.data.length-100 > lastrep:
                    print "@ %s of %s"%(pointer, self.data.length)
                    lastrep = self.data.length

            for window in self.windows:
                if pointer+window["length"] > self.data.length:
                    continue
                slice = self.data[pointer:pointer+window["length"]]
                slice.epsilon = window["sax"].epsilon
                slice.alphabet_size = window["sax"].alphabet_size
                slice.word_size = window["sax"].word_size
                #print "[%s:%s]"%(pointer, pointer+window["length"])
                #print slice.data_saxed
                #print window["length"]
                d = sax.distance(window["sax"].data_saxed, slice.data_saxed, (slice.alphabet_size-1)*slice.word_size)
                #print d
                if d <= window["sax"].dist_max:
                    #We have found a candidate, yay!
                    col = "Candidate for %s-%s [%s:%s] (%s) Len: %s"%(window["sax"].id1,window["sax"].id2,pointer,pointer+window["length"],d, window["length"])
                    print col
                    for c in candidates:
                        if c["sax"] == window["sax"] and c["d"]>d:
                            #print "removing"
                            #print len(candidates)
                            candidates.remove(c)
                    candidates.append({"start": pointer, "end": pointer+window["length"], "sax": window["sax"], "d": d})

            if candidates:
                minend = min([c["end"] for c in candidates])
                if minend <= pointer:
                    match = candidates[0]
                    for c in candidates:
                        if c["d"] < match["d"]:
                            match = c
                    matches.append(match)
                    candidates = []
                    self.matches_dict[match["sax"].id1] += 1
                    print "Match for %s-%s [%s:%s] (%s)"%(match["sax"].id1,match["sax"].id2,match["start"],match["end"], match["d"])
                    print self.matches_dict
                    pointer = match["end"]
                else:
                    pointer += self.step
            else:
                pointer += self.step

        print len(matches)


def chunks(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def matrix_format(matrix):
    r = "     a    b    c    d    e\n__________________________\n"
    i = 1
    for x in matrix:
        if i >= 10:
            head = (" %s |"%i)
        else:
            head = ("  %s |"%i)

        r+= head +("    ".join(map(str,x))+"\n")
        i+=1
    return r

def analyze_cm(d, exercise, positive, negative):
    tp = min(d[exercise - 1],positive)
    fp = sum(d)- tp
    # tn = negative - fp  #not needed
    fn = positive - tp
    print "True Positive: %s"%tp
    print "False Positive: %s"%fp
    print "False Negative: %s"%fn

    precision = float(tp)/(tp+fp)
    recall = float(tp)/(tp+fn)
    f1 = 2* precision * recall / (precision + recall)
    return (precision, recall, f1)

def init_parser():
    parser = optparse.OptionParser()

    parser.add_option("-f", "--file", dest="filename",
                      help="write output to FILE", metavar="FILE")

    parser.add_option("-w", "--wave", dest="wave",
                      metavar="FILE", help="export data as .wav to FILE")

    parser.add_option("-s", "--sax", action="store_true", dest="sax", default=False)

    parser.add_option("-l", "--length", action="store_true", dest="length", default=False,
                      help="get length (in samples) for the data")

    parser.add_option("-c", "--compare", dest="compare", metavar="FILE",
                      help="compare data (with sliding window) with sax-string in FILE")

    parser.add_option("-m", "--multicompare", action="store_true", dest="multicompare", default=False)

    parser.add_option("-r", "--record", dest="record", default=False,
                      help="record to FILE")
    return parser.parse_args()

if __name__ == "__main__":
    #test
    #exit()



    #Parse the commandline
    (options, args) = init_parser()

    sx = []

    #Load input file
    if len(args)>=1:
        #print "loading %s"%args[0]
        sx = RawData(args[0])

    #Export as .wav
    if options.wave:
        sx.save_wav(options.wave)

    #Generate SAX-String
    if options.sax:
        #sax = SAX(sx)
        print sx.data_saxed
        print len(sx.data_saxed)

    #Get length of data (in samples)
    if options.length:
        print len(sx.data)

    #Compare or multicompare a SAX-String with the data
    if options.compare:
        #file = open(options.compare,"r")
        cmpsax = RawData(options.compare)

        if not sx:
            #Multicompare
            exercise = int(cmpsax.id1)
            subject = cmpsax.id2

            collision_rows = []
            for e in range(1,11):
                row = []
                for s in "abcde":
                    f = "../td/exercise-%s%s.arff"%(e,s)
                    data = RawData(filename=f)
                    print ("Comparing with %s"%f)
                    row.append(len(cmpsax.collisions(data)))
                collision_rows.append(row)

            print
            print
            print "Single SAX - Multi Data Comparison"
            print "=================================="
            print "SAX: %s"%(" ".join(cmpsax.data_saxed))
            print "ID: %s - %s - %s"%(cmpsax.id1,cmpsax.id2,cmpsax.id3)
            print "Epsilon: %s     Word Size: %s     Alphabet Size: %s"%(cmpsax.epsilon, cmpsax.word_size, cmpsax.alphabet_size)
            print "Window Min: %s     Window Max: %s     Window Step: %s"%(cmpsax.window_min, cmpsax.window_max, cmpsax.window_step)
            print "dist max: %s"%(cmpsax.dist_max)
            print
            print

            print "Results"
            print "-------"
            print matrix_format(collision_rows)

            #Analyze collision matrix
            single = zip(*collision_rows)[ord(subject)-ord("a")]
            (p,r,f) = analyze_cm(single,exercise, 10, 9*10)
            print "Quality Single"
            print "--------------"
            print "Precision: " + str(p)
            print "Recall:    " + str(r)
            print "F1:        " + str(f)

            all = map(sum, collision_rows)
            (p,r,f) = analyze_cm(all,exercise, 5*10, 9*5*10)
            print

            print "Quality All"
            print "-----------"
            print "Precision: " + str(p)
            print "Recall:    " + str(r)
            print "F1:        " + str(f)
        else:
            coll = cmpsax.collisions(sx)
            print coll

    if options.multicompare:
        sx.start()
        saxes = []
        for subdir, dirs, files in os.walk("../sax_test/"):
            for file in files:
                saxes.append(RawData("../sax_test/"+file))
        for s in saxes:
            print "Using SAX-string: %s"%s.data_saxed
        mc = MultiSAXComparator(saxes, sx, 5)
        mc.compare()

    if options.record:
        print "Recording from serial"
        try:
            sx.run()
        except KeyboardInterrupt:
            print "DONE"
            sx.save_sax(options.record)
