import os, sys, math, random, csv, time
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

sumoBinary = "/usr/bin/sumo-gui"
sumoCmd = [sumoBinary, "-c", "sumodata/osm.sumocfg"]

#defines theoretical bandwidth
def signal_stregnth(tower):
    LTE_freq = 700 #in MHz
    band = 50 #
    mod_ratio = 1/4 #average modulation ratio for LTE
    signal = 700*50*mod_ratio /  1000*len(traci.poi.getContextSubscriptionResults(tower[0]))
    return signal

import traci
import traci.constants as tc
import sumolib
#starts traci simulation
traci.start(sumoCmd,traceFile="traci.log")
max_step = 100 #number of steps in simulation, change to prolong or lower simulation
step = 0
count = 0 
i = 0
choices = random.sample(range(0,16), 4) #picks 4 random junctions from range of junctions 
choices.sort()

baseline_vehicles=[]
junctions=[]
global_tower_list = dict()
max_range=0
for junction in sumolib.output.parse("./sumodata/osm.net.xml", "junction"):
    if i != 4 and choices[i] == count:
        print(junction.id, count)
        junctions.append(junction.id)
        i+=1
        poiID = "junction"+str(junction.id)
        print(junction.x,junction.y)
        x = float(junction.x)
        y = float(junction.y)
        print(x,y)
        traci.poi.add(poiID, x, y, (200,200,200,100), width=10000.00, height=1)
        traci.poi.highlight(poiID, color=(255, 255, 0, 255), size=100, alphaMax=255, duration=max_step+1)
    elif i == 4:
        break
    count+=1
print(junctions, count)

net = sumolib.net.readNet('./sumodata/osm.net.xml')
# x, y = net.convertLonLat2XY(77.590571, 12.978174)
# print(x,y)
min_x, min_y, max_x, max_y = net.getBoundary()
print(max_x, max_y)

#adding cell towers as points of interest to corresponding locations on the map
with open('./opencellID/404.csv', 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    ind = 0
    for row in csv_reader:
        if ind == 0:
            pass
        if 'LTE' == row['radio']:
            x, y = net.convertLonLat2XY(row['lon'], row['lat'])
            if(x < min_x or y < min_y or x > max_x or y > max_y):
                pass
            else:
                print("found tower 404"+str(ind)+"x,y: "+ str(x)+" "+str(y) + "max_x,max_y: "+ str(max_x)+" "+str(max_y))
                poiID = "celltower404"+str(ind)
                traci.poi.add(poiID, x, y, (255,100,200,255), width=1, height=1)
                traci.poi.subscribeContext(poiID, tc.CMD_GET_VEHICLE_VARIABLE,int(row['range']), [tc.VAR_SPEED,tc.VAR_LANE_ID, tc.VAR_POSITION])
                global_tower_list[poiID] = [x,y,float(row['range'])]
        ind+=1

#adding cell towers as points of interest to corresponding locations on the map
with open('./opencellID/405.csv', 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    ind = 0
    for row in csv_reader:
        if ind == 0:
            pass
        if 'LTE' == row['radio']:
            x, y = net.convertLonLat2XY(row['lon'], row['lat'])
           # print(x,y)
            if(x < 0 or y < 0 or x > max_x or y > max_y):
                pass
            else:
                print("found tower 405 "+str(ind))
                poiID = "celltower405"+str(ind)
                traci.poi.add(poiID, x, y, (255,100,200,255), width=1000.0, height=1)
                traci.poi.subscribeContext(poiID, tc.CMD_GET_VEHICLE_VARIABLE,int(row['range']), [tc.VAR_SPEED,tc.VAR_LANE_ID, tc.VAR_POSITION])
                global_tower_list[poiID] = [x,y,float(row['range'])]
        ind+=1

colors=[(255,255,0,255),(255,0,100,255),(255,100,0,255),(255,0,255,255)] #colors for highlighting circles for UI

#selects junctions and keeps track of vehicles that pass within 1000m from junction
for i in range(4):
    traci.junction.subscribeContext(junctions[i], tc.CMD_GET_VEHICLE_VARIABLE, 1000, [tc.VAR_SPEED,tc.VAR_LANE_ID, tc.VAR_POSITION])
    baseline_vehicles.append(traci.junction.getContextSubscriptionResults(junctions[i]))

csvfile=dict()

for step in range(100):
   print("step", step)
   traci.simulationStep()
   for i in range(len(junctions)):
        csvdata={'speed':0,'laneID':0, 'location':0, 'distance':0,'time':0,'junctionID':0, 'junctionList':[], 'towerList':[]}
        data=[]
        index=0
        vehicles=traci.junction.getContextSubscriptionResults(junctions[i]) #get vehicles near junction
        unique_vehicles = {k:v for k,v in vehicles.items() if k not in baseline_vehicles[i]} #select unique vehicles
        timestamp=traci.simulation.getTime() #get simulation time
        for j in unique_vehicles:
            #trace objects that come within 1000m of vehicles, change to track more towers
            traci.vehicle.subscribeContext(j,tc.CMD_GET_POI_VARIABLE,1000, [tc.VAR_POSITION]) 
            junctionlist=[]
            tower_list=[]
            for junction in junctions:
                j_x, j_y = traci.junction.getPosition(junction)
                #[juntionId, distance of vehicle from juntion]
                junctionlist.append([junction, traci.simulation.getDistance2D(j_x,j_y,unique_vehicles[j][tc.VAR_POSITION][0],unique_vehicles[j][tc.VAR_POSITION][1])])
            tower_dict = traci.vehicle.getContextSubscriptionResults(j) #get cell tower information
            for tower in tower_dict:
                if "celltower" not in tower:
                    continue
                tower_x = tower_dict[tower][tc.VAR_POSITION][0]
                tower_y = tower_dict[tower][tc.VAR_POSITION][1]
                tower_location = traci.simulation.convertGeo(tower_x,tower_y)
                dist = traci.simulation.getDistance2D(tower_x,tower_y,unique_vehicles[j][tc.VAR_POSITION][0],unique_vehicles[j][tc.VAR_POSITION][1])
                if dist < global_tower_list[tower][2]: #only add towers when within range of vehicle
                    #[towerid, (long,lat), distance of vehicle from tower, range of tower]
                      tower_list.append([tower, tower_location, dist, global_tower_list[tower][2]])                    
            tower_list.sort()
            tower_list_new=[]
            k=0
            top_k = 10 #top k towers taken 
            if len(tower_list) == 10:
                k = 10
            while k < top_k:
                tower_list_new.append(tower_list[k])
                k+=1

            #[towerid, (long,lat), distance of vehicle from tower, range of tower, bandwidth, latency]
            for tower in tower_list_new:
                tower.append(signal_stregnth(tower))
                #usual formula is distance/speed in transmission medium + packet size/ bandwidth
                #but since divide by speed of light makes it negligibly small, ignore first half of equation
                #latency = tower[2]/299702547  +  1500*8/tower[4]*1000
                latency = 1500*8/(tower[4]*1000)
                tower.append(latency)
            
            if j not in csvfile.keys():
                csvfile[j]=[]
            for k in unique_vehicles[j]:
                data.append(unique_vehicles[j][k])
            data[len(data)-1] = traci.simulation.convertGeo(data[len(data)-1][0],data[len(data)-1][1])
            j_x,j_y = traci.junction.getPosition(junctions[i])
            dist = traci.simulation.getDistance2D(j_x,j_y,unique_vehicles[j][tc.VAR_POSITION][0],unique_vehicles[j][tc.VAR_POSITION][1])
            data.append(dist)
            data.append(timestamp)
            data.append(junctions[i])
            data.append(junctionlist)
            data.append(tower_list_new)
            #to add column titles
            if(os.path.isfile(j+'.csv') == False):
                with open(j+'.csv', 'w') as check_file:
                    csv_writer = csv.DictWriter(check_file, fieldnames=csvdata.keys())
                    csv_writer.writeheader()

            #adds the rest of the data
            with open(j+'.csv', 'a') as file:
                writer = csv.writer(file)
                writer.writerow(data)
        unused_vehicles = {k:v for k,v in baseline_vehicles[i].items() if k not in vehicles}
        try:
                for j in unique_vehicles:
                    print("highlighting", max_range)
                    traci.vehicle.highlight(j,(255,0,0,255), size=2000)
                for j in unused_vehicles:
                    traci.vehicle.highlight(j,(255,255,0,0), size=0)
        except:
                print("vehicle disappeared")

        baseline_vehicles[i]=vehicles

traci.close()