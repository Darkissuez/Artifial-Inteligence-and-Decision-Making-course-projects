#!/usr/bin/python3

import sys
sys.path.append( '../aima' )
import search

class ASARProblem(search.Problem):
    def __init__(self):
        """ the dictionaries are coded in the following way:
        dict airpoirt: keys = AIRPORT_CODE, values = (opening time, closing time)
        dict airplanes: keys = plane_ids, values = (PLANE_CODE, MODEL_CODE, rotation_time)
        dict legs: keys = leg_ids, values = ((DEPARTURE, ARRIVAL), flight_time, tuples(MODEL_CODE, profit))

        Definition of the state variables: tuple where first element is the number of legs that
        are left to do +  tuples with (plane_id, legs made, current time) (for each plane) """
        self.initial = None  #the initial state in only initialized in load()
        self.airports = {}
        self.airplanes = {}
        self.legs = {}
        self.max_profit = 0.0
        self.N = 1

    def get_hours(self, x):
        """convert time from HHMM to hours
        """
        return x // 100 + (x % 100) / 60

    def get_time_str (self, x):
        """return a string with time in HHMM give time in hours (float)
        """
        h = int (x)

        m =x - int(x)
        m *= 60
        m = round (m)

        if (m == 60):
            h += 1
            m = 0

        if h < 10:
            str1="0"+str(h)
        else:
            str1= str(h)

        if m < 10:
            str1+="0"+str(m)
        else:
            str1+= str(m)

        return str1


    def validate(self, leg, current_time):
        t = self.legs[leg][1]
        airport = self.legs[leg][0]
        A0 = self.airports[airport[0]][0]
        A1 = self.airports[airport[0]][1]
        B0 = self.airports[airport[1]][0]
        B1 = self.airports[airport[1]][1]

        if current_time != -1:
            A0 = current_time

        if (A0 > A1):
            return False

        if (A0+t >= B0 and A0+t <= B1):
            return True
        if (A1+t >= B0 and A1+t <= B1):
            return True
        if (B0-t >= A0 and B0-t <= A1):
            return True
        if (B1-t >= A0 and B1-t <= A1):
            return True
        return False



    def actions(self, state):
        """this function returns a list of actions, given a state
        each action is a tuple with the plane_id and leg_id -> (plane_id, leg_id)"""
        actions = []
        current_legs = state[0]
        if not current_legs:
            return actions #there are no legs -> no possible actions to do

        for (plane,legs_made, current_time) in state[1:]:
            last_leg = legs_made[-1] #get the last leg made (may be -1)

            if last_leg == -1: #if the airplane did not make a move yet, all legs are possible

                for leg in current_legs:
                    act = (plane, leg)
                    if self.validate(leg,current_time):
                        actions.append(act)
            else: #generally the airplane can only take legs that depart from where it is now
                current_location = self.legs[last_leg][0][1]
                for leg in current_legs:
                    if(self.legs[leg][0][0] == current_location): #the next leg has to start in current_location
                        act = (plane, leg)
                        if self.validate(leg,current_time):
                            actions.append(act)
        return(actions)

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. Assuming that the action is valid in this state"""
        if not action:
            return None #if there is no action to apply, return None

        else:
            self.N += 1
            new_state = list(state) #get a copy of the previous state
            action_plane = action[0]
            action_leg = action[1]
            for (i,(plane, legs_made, current_time)) in enumerate(state[1:]):
                if (legs_made[0] == -1):
                    legs_made = []
                else:
                    legs_made = list(legs_made)
                #casting legs_made to a list

                if plane == action_plane:
                    t_flight = self.legs[action_leg][1]
                    t_rot = self.airplanes[plane][2]
                    airport = self.legs[action_leg][0]
                    time_A_0 = self.airports[airport[0]][0]
                    time_B_0 = self.airports[airport[1]][0]
                    if current_time != -1:
                        time_A_0 = current_time

                    delta = time_B_0 - time_A_0
                    if delta <= t_flight:#problematico
                        current_time = time_A_0 + t_flight + t_rot
                    else:
                        current_time = time_B_0 + t_rot

                    legs_made.append(action_leg)
                    replace = (action_plane,tuple(legs_made),current_time)

                    new_state[i+1] = replace
                    new_state[0] = [i for i in state[0] if i!=action_leg]
        new_state = tuple((map(tuple, new_state)))
        return new_state

    def goal_test(self, state):
        """Return True if the state is a goal.
        Conditions to take into consideration:
            -The current legs tuple must be empty
            -Each plane should start and finish in the same airport
            -If one plane did not move, it doesn't matter"""
        goal = False
        current_legs = state[0]
        if (current_legs == ()):
            for (plane, legs_made,current_time) in state[1:]:
                goal = True #goal starts True, changes to False if one of the conditions is not met
                if (legs_made[0] == -1):
                    continue
                elif (len(legs_made) == 1):
                    goal = False
                    #if a certain plane only moved once, then it doesnt start and end in the same place
                    break

                else: #when the plane made more that one leg
                    start_place = self.legs[legs_made[0]][0][0] #first departure
                    end_place = self.legs[legs_made[-1]][0][1] #last arrival
                    if not (start_place == end_place):
                        goal = False
                        break
                        #if there is one pair that doesn't match, the state is not a goal one
        return goal

    def path_cost(self, c, state1, action, state2):
        """Return the cost of a solution path that arrives at state2 from
        state1 via action, assuming cost c to get up to state1."""
        plane_model = self.airplanes[action[0]][1]
        info = self.legs[action[1]][2:]
        for (model, profit) in info:
            if model == plane_model:
                return c + (self.max_profit - float(profit))



    def heuristic(self, node):
        """return the heuristic of node n
        h(n) is calculated by summing the profits in all the remaining legs
        (problem relaxation). In order to achieve optimal solution, the heuristic
        has to be the inverse of the sum of the greatest profits:
        h(n) = 1 / (greatest_profit(leg1) + ... + greatest_profit(last_leg))"""
        current_legs = node.state[0]
        if self.goal_test(node.state):
            return 0 #heuristic of goal node is 0


        total_profit = 0.0
        for leg in current_legs:
            info = self.legs[leg]
            leg_profits = [float(p[1]) for p in info[2:]] #list with all the possible profits
                                                    #for each model
            total_profit += (self.max_profit - max(leg_profits))

        return total_profit



    def load(self, fh):
        lines = [ln for ln in fh]
        ac_models = {}
        for ln in lines:
            vals = ln.split()
            if vals:
                if vals[0] == 'A':
                    self.airports[vals[1]] = (self.get_hours(int(vals[2])), self.get_hours(int(vals[3])))

                if vals[0] == 'P':
                    self.airplanes[len(self.airplanes)] = [vals[1],vals[2]]

                if vals[0] == 'C':
                    ac_models[vals[1]] = self.get_hours(int(vals[2]))

                if vals[0] == 'L':
                    nodes = [(vals[1],vals[2]),self.get_hours(int(vals[3]))]
                    for i in range(4,len(vals), 2):
                        nodes.append((vals[i],vals[i+1]))
                    self.legs[len(self.legs)] = tuple(nodes)

        for plane_id in self.airplanes.keys():
            model = self.airplanes[plane_id]
            model.append(ac_models[model[1]]) #append the rotation time
            self.airplanes[plane_id] = model


        #defining initial state
        plane_id = self.airplanes.keys()
        state = [tuple([i for i in self.legs.keys()])]
        for plane_id in self.airplanes.keys():
            state.append( (plane_id,(-1,), -1) )
        self.initial = tuple(state)

        #getting the greatest value for all legs (Majorant of profit)
        vec = []
        for leg_id in self.legs:
            for i in self.legs[leg_id][2:]:
                vec.append(float(i[1]))
        self.max_profit = max(vec) + 10.0


    def save(self, fh, state):
        if state == None:
            fh.write("Infeasible")
        else:
            profit = 0
            for (plane, legs_made,final) in state[1:]:
                if (legs_made[0] == -1):
                    continue
                name = self.airplanes[plane][0]
                model = self.airplanes[plane][1]
                t_rot = self.airplanes[plane][2]
                str1 = "S " + name + " "

                current_time = -1
                for leg in legs_made:
                    t_flight = self.legs[leg][1]
                    airport = self.legs[leg][0]
                    time_A_0 = self.airports[airport[0]][0]
                    time_B_0 = self.airports[airport[1]][0]
                    if current_time != -1:
                        time_A_0 = current_time

                    delta = time_B_0 - time_A_0
                    if delta <= t_flight:
                        current_time = time_A_0
                    else:
                        current_time = time_B_0 - t_flight

                    str1 += self.get_time_str(current_time) + " "

                    str1 += airport[0] + " " + airport[1] + " "

                    current_time += t_flight + t_rot

                    #calcular profits
                    l = self.legs[leg]
                    for (mod, pro) in l[2:]:
                        if mod == model:
                            profit += float(pro)

                fh.write(str1)
                fh.write("\n")
            fh.write("P " + str(round(profit,1)))






def main(argv):

    try:
        fh = open(argv[1])
    except (FileNotFoundError,IndexError):
        str = ("FileNotFoundError on file {}.\n"
               "To run this script use './ASAR.py PATH' where PATH is the path to the input file").format(argv[0])
        print(str)
        exit()

    solver = ASARProblem()
    solver.load(fh)
    solution = search.astar_search(solver, solver.heuristic)
    fh = open("solution.txt", "w")
    if solution == None:
        solver.save(fh, None)
    else:
        solver.save(fh,solution.state)

    print("Script ran successfully. Results on 'solution.txt' file")
    # print("generated states: ", solver.N)

if __name__ == "__main__":
   main(sys.argv)
