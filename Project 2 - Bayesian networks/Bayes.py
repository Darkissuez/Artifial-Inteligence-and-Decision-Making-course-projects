#!/usr/bin/python3

import sys
sys.path.append( '../aima' )
import probability as pb

class Problem:

    def __init__(self, fh):
        # Place here your code to load problem from opened file object fh
        # and use probability.BayesNet() to create the Bayesian network
        T, F = True, False
        self.rooms = {}
        self.connections = {}
        self.sensors = {}
        self.propagation_probability=0.0
        self.time = {}
        self.T = 0
        self.evidence={}
        self.load(fh)
        net = self.create_network()
        self.network = pb.BayesNet(net)
        room, likelihood = self.solve()

    def load(self, fh):
        lines = [ln for ln in fh]
        #first read the independent command lines
        for ln in lines:
            vals = ln.split()
            if vals:
                if vals[0] == 'R':
                    for i in range(1,len(vals)):
                        self.connections[len(self.rooms)+1]=[]
                        self.rooms[vals[i]] = len(self.rooms)+1
                if vals[0] == 'P':
                    self.propagation_probability = float(vals[1])
                if vals[0] == 'M':
                    self.T += 1
                    list_keys =[]
                    list_values=[]
                    for i in range(1, len(vals)):
                        a, b = vals[i].split(':')
                        list_keys.append(a)
                        list_values.append(b)
                    self.time[len(self.time)+1]={list_keys[j]:list_values[j] for j in range(0,i)}
        #then, read the ones that need info from the previous ones
        for ln in lines:
            vals = ln.split()
            if vals:
                if vals[0] == 'C':
                    for i in range(1, len(vals)):
                        a, b = vals[i].split(',')
                        self.connections[self.rooms[a]].append(self.rooms[b])
                        self.connections[self.rooms[b]].append(self.rooms[a])
                if vals[0] == 'S':
                    for i in range(1, len(vals)):
                        sensor, room, hit_rate, false_alarm = vals[i].split(':')
                        self.sensors[sensor]=[self.rooms[room], float(hit_rate), float(false_alarm)]


    def f(self,x):
        if x == '1':
            return True
        else:
            return False

    def any_true(self,x):
        ret = False
        for i in x:
            if i is True:
                ret = True
                break
        return ret


    def create_network(self):
        net = []
        T, F = True, False
        dict_aux = {'0':T, '1':F}
        dict_cpts = {}
        rooms = list(self.rooms.keys())

        for time in range(1, self.T+1):
            #nodes for the rooms
            for room in rooms:
                id = self.rooms[room]
                var = "r" + str(id)+ "_" + str(time)

                #filling up the parent nodes
                if time == 1:
                    parents = ''
                else:
                    # vai buscar o próprio, no tempo anterior
                    parents = "r" + str(id)+ "_" + str(time-1) + " "
                    #vai buscar as conexões
                    for cons in self.connections[id]:
                        parents += "r" + str(cons) + "_" + str(time-1) + " "

                #filling up the conditional probabilities of each node
                if time == 1:
                    cpt = 0.5
                else:
                    #dict_cpts is a dict with the cpt tables already created. They are only a function
                    #of nr - the number of parent nodes. So if the table was already created previously
                    #there is no need to make the computations again
                    nr = len(self.connections[id]) + 1
                    if nr in dict_cpts:
                        cpt = dict_cpts[nr]
                    else:
                        formatting = '0'+str(nr)+'b'
                        cpt = {}

                        for k in range(0,2**nr):
                            j = format(k,formatting)
                            a = tuple( map(self.f, j))
                            if a[0] == T:
                                #se o próprio já estava on fire
                                cpt[a] = 1
                            elif self.any_true(a[1:]) is True:
                                #se alguma das conexoes estava on fire
                                cpt[a] = self.propagation_probability
                            else:
                                cpt[a] = 0
                        dict_cpts[nr] = cpt
                net.append((var, parents, cpt))


            #nodes for the evidence variables
            for t, info in self.time.items():
                if t == time:
                    for sensor, evidence in info.items():
                        details = self.sensors[sensor]
                        #print(t, sensor, details)
                        var = sensor + "_" + str(t)
                        parent = "r"+str(details[0])+"_"+str(t)
                        cpt = {T: details[1], F:details[2]}
                        if evidence=='T':
                            evidence=True
                        else:
                            evidence=False
                        self.evidence[var] = evidence
                        net.append((var, parent, cpt))

        return net


    def solve(self):
            # Place here your code to determine the maximum likelihood solution
            # returning the solution room name and likelihood
        values={}
        prob=[]
        for room2 in self.rooms:
            id = self.rooms[room2]
            var = "r" + str(id)+ "_" + str(self.T)
            aux = pb.elimination_ask(var, self.evidence, self.network).show_approx(numfmt='{:.20g}')
            prob.append((aux, room2))
        for i in range(len(prob)):
            false_comp, true_comp = prob[i][0].split(',')
            booleano, prob_true = true_comp.split(':')
            values[prob[i][1]]=float(prob_true)
        comp = 0
        for room2 in values.keys():
            if values[room2] > comp:
                comp = values[room2]
                likelihood = values[room2]
                room = room2

        return (room, likelihood)



def solver(input_file):
    return Problem(input_file).solve()

def main(argv):
    try:
        fh = open(argv[1])
    except (FileNotFoundError,IndexError):
        str = ("FileNotFoundError on file {}.\n"
               "To run this script use './Bayes.py PATH' where PATH is the path to the input file").format(argv[0])
        print(str)
        exit()
    solution = solver(fh)
    print("Solution:\nRoom is {}, probability = {}".format(solution[0],solution[1]))


if __name__ == "__main__":
   main(sys.argv)
