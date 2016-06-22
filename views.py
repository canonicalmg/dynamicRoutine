from datetime import datetime
#from django.db import models
#from models import Stats
from operator import itemgetter
from django.views.decorators.csrf import csrf_exempt
from .models import Stats2, exercise, routine, exerciseForRoutine, exerciseCompare2, muscle, muscleGroupMajor, muscleGroupMinor, auxExercise, routineEntry, generatedRoutineExercise, muscleStats
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core import serializers
from django.utils import simplejson
import random




from django.shortcuts import render
import json

from django.http import HttpResponse

def home(request):
    return render(request, 'home.html', {'right_now':datetime.utcnow()})

def discover(request):
    return render(request, 'discover.html')

def createRoutine(request):
    return render(request, 'createRoutine.html')

def getExercises(request):
    if request.method == 'GET':
        if request.is_ajax():
            #data = exercise.objects.values_list('exerciseName', 'pk')
            foos = exercise.objects.all()
            data = serializers.serialize('json', foos)
            return HttpResponse(data, mimetype='application/json')

def saveStats(request):
    name = request.POST.getlist('dataSend[]') #[BenchWeight, benchRep, SquatWeight, SquatRep, DeadWeight, DeadRep, PullupWeight, PullupRep, User]
    if request.method == 'POST':
        if request.is_ajax():
            userForeign = request.user
            stats = Stats2(BenchWeight=name[0], BenchReps=name[1], SquatWeight=name[2], SquatReps=name[3], DeadWeight=name[4], DeadReps=name[5], PullupWeight=name[6], PullupReps=name[7], author=userForeign)
            stats.save()
            return HttpResponse(userForeign)
    else:
        return HttpResponse("Error")

def newUser(request):
    info = request.POST.getlist('dataSend[]')
    if request.method == 'POST':
        if request.is_ajax():
            #strip info[0] everything before @
            username = info[0].split('@')[0]
            #new_user = User(Username=username, Email=info[0], Password=info[1])

            new_user=User.objects.create_user(username, info[0], info[1])
            #new_user.first_name = self.cleaned_data['first_name']
            #new_user.last_name = self.cleaned_data['last_name']
            new_user.save()
            return HttpResponse("Welcome, " + username)
    else:
        return HttpResponse("Error")

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]

def newRoutine(request):
    info = request.POST.getlist('data[]') #[name,...[pk, sets, reps, freq, beg, nov, inter, adv, elite]...]
    if request.method == 'POST':
        if request.is_ajax():
            routineAddName = info[0]
            authorAdd = request.user
            newRoutine = routine(routineName=routineAddName, date=datetime.now, author=authorAdd, upVote=0, downVote=0)
            newRoutine.save()

            newRoutine2 = routine.objects.filter(author=request.user).latest('pk')
            routinePK = newRoutine2.pk
            info2 = info[1]
            info3 = info2.strip().split(",")
            info4 = list(chunks(info3, 9)) #9 because there are 9 fields per exercise sent from ajax
            for x in info4:
                exerciseNameAdding = exercise.objects.get(pk=x[0])
                actualRoutineAdding = routine.objects.get(pk=routinePK)
                newExerciseForRoutine = exerciseForRoutine(exerciseName=exerciseNameAdding, actualRoutine=actualRoutineAdding, exerciseSets=x[1], exerciseReps=x[2], exerciseFrequency=x[3], beginner=x[4], novice=x[5], intermediate=x[6], advanced=x[7], elite=x[8])
                newExerciseForRoutine.save()
            return HttpResponse("Success")
    else:
        return HttpResponse("Error")

def getRoutine(request):
    if request.method == 'GET':
        if request.is_ajax():
            routineList = routine.objects.filter()
            data = serializers.serialize("json", routineList)
            #print "testasd", routineList
            outerArr = []
            for x in routineList:
                arrName = str(x.routineName)
                innerArr = ["<option value='"+str(x.pk)+"'>"+arrName+ "</option>"]
                outerArr.append(innerArr)
                #print arrName
            #return HttpResponse(json.dumps(outerArr), content_type = "application/json"))
            #data2 = serializers.serialize("json", outerArr)
            json_stuff = simplejson.dumps({"data" : outerArr})
            return HttpResponse(json_stuff, content_type ="application/json")
            #return HttpResponse(outerArr, content_type='application/json')

def dynamicRoutine(request):
    if request.method == 'POST':
        if request.is_ajax():
            info = request.POST.getlist('dataSend[]')
            parentRoutine = routine.objects.get(pk=info[0])
            routineExercises = exerciseForRoutine.objects.filter(actualRoutine=parentRoutine)
            try:
                outerArr = []
                for x in routineExercises:
                    print "inside loop"
                    innerArr = [str(x.exerciseName.exerciseName), x.exerciseSets, x.exerciseReps, x.exerciseFrequency, x.beginner, x.novice, x.intermediate, x.advanced, x.elite, x.pk]
                    print "test", innerArr
                    outerArr.append(innerArr)
                    print "test2", outerArr
                print "before"
                json_stuff = simplejson.dumps({"data" : outerArr})
                print "inbetween"
                return HttpResponse(json_stuff, content_type ="application/json")
            except Exception,e:
                return HttpResponse("Error, query probably not found", e);




def routineGen(request):
    return render(request, 'routine.html')

def getMuscleDict():
    allMuscles = muscle.objects.all()
    muscleDict = []
    for x in allMuscles:
        muscleDict.append({'muscleName': str(x.muscleName), 'primaries':[], 'secondaries':[], 'pk':x.pk, 'muscleStrength':0})

    #for x in muscleDict:
        #print "printing x", x
        #print "printing muscle name: ", x['muscleName']
        #if x['muscleName'] == "Abdominals":
            #x['primaries'].append("ayy")
    #print "muscleDict = ", muscleDict
    return muscleDict

def getMuscleStrengthDict():
    allMuscles = muscle.objects.all()
    muscleArrOuter = {}
    for x in allMuscles:
        muscleArrInner = [str(x.muscleName), 0]
        muscleArrOuter[x.pk] = muscleArrInner
    return muscleArrOuter

def muscleDictPopulateScore(row, exercisePk, heur):
    #print "inside populate"
    primaries = muscleGroupMajor.objects.filter(exerciseActual = exercisePk, muscleActual = row['pk'])
    secondaries = muscleGroupMinor.objects.filter(exerciseActual = exercisePk, muscleActual = row['pk'])
    #print "prim = ", primaries
    #print "second = ", secondaries
    #print "after prim secon"
    for x in primaries:
        #print "Adding primary"
        row['primaries'].append(heur)
    for y in secondaries:
        #print "adding secondary"
        row['secondaries'].append(heur)
    #print "returning", row
    return row

def calculateMuscleStrength(muscleDict, PRIMHEUR, SECONDHEUR): #primheur and secondheur are modifiable heuristics. Starting out with 70% 30% but that could change
    for y in muscleDict:
        #print "WORKING ON ", y
        prim = 0
        second = 0
        for a in y['primaries']:
            prim = prim + a
        for b in y['secondaries']:
            second = second + b
        if len(y['primaries']) >= 1:
            if len(y['secondaries']) >=1:
                muscleStrength = ((PRIMHEUR * (prim/len(y['primaries']))) + (SECONDHEUR * (second/len(y['secondaries'])))) #gr8 (1,1)
            else:
                muscleStrength = (((prim/len(y['primaries'])))) #no secondaries (1,0)
        elif len(y['primaries']) == 0:
            if (len(y['secondaries'])) >=1:
                muscleStrength = (((second/len(y['secondaries'])))) #no primaries (0,1)
            else:
                muscleStrength = 0

        y['muscleStrength'] = round(muscleStrength,3)
        #print "MUSCLE STRENGTH=", muscleStrength
        #print "FINISHED WITH ", y
    return muscleDict

def updateMuscleCounter(routineWeek, muscleCounter):
    print "INSIDE UPDATEMUSCLECOUNTER:"
    print "ROUTINEWEEK = ", routineWeek
    print "MUSCLECOUNTER BEFORE = ", muscleCounter
    print "__"
    muscleCounter = sorted(muscleCounter, key=itemgetter(1)) #index #1. Sorting by pk
    print "muscleCounter After =", muscleCounter
    for x in routineWeek:
        print "using exercise", x
        try:
            majorMuscles = muscleGroupMajor.objects.filter(exerciseActual = x)
            for y in majorMuscles:
                muscleCounter[y.muscleActual.pk][2] = muscleCounter[y.muscleActual.pk][2] + 3
                print "muscleCounter muscle =", muscleCounter[y.muscleActual.pk]
        except:
            print "[UpdateCounter]nomuscle group major found for ", x
        try:
            minorMuscles = muscleGroupMinor.objects.filter(exerciseActual = x)
            for y in minorMuscles:
                muscleCounter[y.muscleActual.pk][2] = muscleCounter[y.muscleActual.pk][2] + 1
        except:
            print "[UpdateCounter]no muscle group minor found for ", x
    return sorted(muscleCounter, key=itemgetter(2)) #index #1. Sorting by strengthScore

def mondayRoutine(mondayFridayMuscles, routineWeek):
                #mondayFridayMuscles = muscleStats[:5]
                #print "weak 5 = ", mondayFridayMuscles
                print "MONFRI MUSCLES =", mondayFridayMuscles
                for x in mondayFridayMuscles:
                    primary = muscleGroupMajor.objects.filter(muscleActual = x[0])
                    for y in primary:
                        comparing = y.exerciseActual.pk
                        if comparing not in routineWeek:
                            print "ADDING PRIMARY for ", x[1]
                            routineWeek.append(comparing)
                            break
                    secondary = muscleGroupMinor.objects.filter(muscleActual = x[0])
                    counter = 1
                    for y in secondary:
                        if counter < 3:
                            comparing = y.exerciseActual.pk
                            if comparing not in routineWeek:
                                print "ADDING SECONDARY for", x[1]
                                routineWeek.append(comparing)
                                counter = counter + 1
                                break
                print "exercises being done monday = ", routineWeek
                return routineWeek

def TueWedThurRoutine(numMusclePerDay, muscleCounter, routineWeek):
    musclesUsed = muscleCounter[:numMusclePerDay] #take N muscles with lowest muscle counter score for the week.Schema = [name,pk,score]
    print "Muscles Used = ", musclesUsed
    for x in musclesUsed:
        print "tuesday X", x
        try:
            primary = muscleGroupMajor.objects.filter(muscleActual = x[1])
            print "PRIMARY =", primary
            for y in primary:
                print "tuesday Y", y
                comparing = y.exerciseActual.pk
                if comparing not in routineWeek:
                    print "ADDING PRIMARY for ", x[0]
                    routineWeek.append(comparing)
                    print "appended ", comparing
                    break
        except:
            print "[TueWedThur]error, no primary exercise for given muscle ", x[0]
        try:
            secondary = muscleGroupMinor.objects.filter(muscleActual = x[1])
            print "SECONDARY =", secondary
            counter = 1
            for y in secondary:
                print "tuesday Y2", y
                if counter < 3:
                    comparing = y.exerciseActual.pk
                    if comparing not in routineWeek:
                        print "ADDING SECONDARY FOR ", x[0]
                        routineWeek.append(comparing)
                        print "appended", comparing
                        counter = counter + 1
                        break
        except:
            print "[TueWedThur]Error, no secondary exercise for given muscle", x[0]
    return routineWeek

def generateMondayRoutine(musclesUsed): #musclesUsed = [pk, name, strength, score)
    routineWeek = []
    #Find a compound lift for each one whose primary muscle matches, initialize routine to hit that lift for 3 sets of 5
    compoundCounter = 0
    isolationCounter = 0
    compoundMax = 3
    isolationMax = 4
    for x in musclesUsed:
        #print "Muscle - ", x[1]
        primary = muscleGroupMajor.objects.filter(muscleActual = x[0])
        for y in primary:
            if compoundCounter <= compoundMax:
            #check if there is a compound, use the first one found
                try:
                    compoundLift = auxExercise.objects.get(exerciseActual = y.exerciseActual.pk, isCompound = True)
                    routineWeek.append([compoundLift.exerciseActual.exerciseName,compoundLift.exerciseActual.pk,3,5])
                    #print "appended ", y.exerciseActual.exerciseName
                    compoundCounter = compoundCounter + 1
                    break
                except:
                    print "EXERCISE", y.exerciseActual.exerciseName , "NOT COMPOUND. NOT ADDING"

        print "Working on Secondaries..."
        secondary = muscleGroupMajor.objects.filter(muscleActual = x[0])
        for y in secondary:
            if isolationCounter <= isolationMax:
                try:
                    isolationLift = auxExercise.objects.get(exerciseActual = y.exerciseActual.pk, isCompound = False)
                    routineWeek.append([isolationLift.exerciseActual.exerciseName,isolationLift.exerciseActual.pk, 3, 10])
                    isolationCounter = isolationCounter + 1
                    break
                except:
                    print "EXERCISE", y.exerciseActual.exerciseName , "NOT ISOLATION. NOT ADDING"
    #print "routineWeek = ", routineWeek
    #print "muscleStrengths = ", muscleStrengths
    return routineWeek

def generateTuesWedThursRoutine(muscleCounter):
    #TUES/WED/THURS
                #take M muscles from muscleStats so that the least used muscles get used. N=5
                #Find 3 compounds, initialize routine to hit that lift for 3x5
                    #if lift is already included, increment set +1
                #find 3 isolation lifts
                    #if lift is already included, find a different one
                #Each time lift is included, incrememnt muscle counter by 1
    #print "inside generate tueswedthurs, musclecounter = ", muscleCounter
    muscleCounterSend = muscleCounter
    musclesUsed = takeSmallestFromDict(muscleCounterSend, 5) #[pk, [name, val]]
    #print "smallest 5 = ", musclesUsed
    routineWeek = []
    #Find a compound lift for each one whose primary muscle matches, initialize routine to hit that lift for 3 sets of 5
    compoundCounter = 0
    isolationCounter = 0
    compoundMax = 4
    isolationMax = 5
    print "TUES WED THURS using: ", musclesUsed
    for x in musclesUsed:
        #print "Muscle - ", x[1]
        primary = muscleGroupMajor.objects.filter(muscleActual = x[0])
        for y in primary:
            if compoundCounter <= compoundMax:
            #check if there is a compound, use the first one found
                try:
                    compoundLift = auxExercise.objects.get(exerciseActual = y.exerciseActual.pk, isCompound = True)
                    routineWeek.append([compoundLift.exerciseActual.exerciseName,compoundLift.exerciseActual.pk,3,5])
                    #print "appended ", y.exerciseActual.exerciseName
                    compoundCounter = compoundCounter + 1
                    break
                except:
                    print "EXERCISE", y.exerciseActual.exerciseName , "NOT COMPOUND. NOT ADDING"

        #print "Working on Secondaries..."
        secondary = muscleGroupMajor.objects.filter(muscleActual = x[0])
        for y in secondary:
            if isolationCounter <= isolationMax:
                try:
                    isolationLift = auxExercise.objects.get(exerciseActual = y.exerciseActual.pk, isCompound = False)
                    routineWeek.append([isolationLift.exerciseActual.exerciseName,isolationLift.exerciseActual.pk, 3, 10])
                    isolationCounter = isolationCounter + 1
                    break
                except:
                    print "EXERCISE", y.exerciseActual.exerciseName , "NOT ISOLATION. NOT ADDING"
    #print "routineWeek = ", routineWeek
    #print "muscleStrengths = ", muscleStrengths
    return routineWeek

def takeSmallestFromDict(dict, number):
    returnedSmallest = []
    for x in range(0, number):
        smallest = [0,("", 100000)] #(key,[name, val])
        for key, value in dict.iteritems():
            if value[1] < smallest[1][1]:
                if (key, value) not in returnedSmallest:
                    smallest = (key, value)
        returnedSmallest.append(smallest)
    return returnedSmallest


def updateMuscleCounter2(routineWeek, muscleCounter):
    print "MUSCLECOUNTER ENTRY: ", muscleCounter
    for x in routineWeek:
        primary = muscleGroupMajor.objects.filter(exerciseActual = x[1])
        for y in primary:
            if y.muscleActual.pk in muscleCounter:
                muscleCounter[y.muscleActual.pk][1] = muscleCounter[y.muscleActual.pk][1] + ((x[2] * (10/x[3])) * 0.6) # sets * 10/rep. Heuristic takes account for number of sets and prioritizes lower reps (because lower rep = compound). Need to mult this by major or minor for each muscle
            else:
                muscleCounter[y.muscleActual.pk] = [y.muscleActual.muscleName, ((x[2] * (10/x[3])) * 0.6)]

        secondary = muscleGroupMinor.objects.filter(exerciseActual = x[1])
        for y in secondary:
            if y.muscleActual.pk in muscleCounter:
                muscleCounter[y.muscleActual.pk][1] = muscleCounter[y.muscleActual.pk][1] + ((x[2] * (10/x[3])) * 0.4) # sets * 10/rep. Heuristic takes account for number of sets and prioritizes lower reps (because lower rep = compound). Need to mult this by major or minor for each muscle
            else:
                muscleCounter[y.muscleActual.pk] = [y.muscleActual.muscleName, ((x[2] * (10/x[3])) * 0.4)]
    print "MUSCLECOUNTER EXIT: ", muscleCounter
    return muscleCounter

def generateMondayRoutine2(musclesUsed):
    #print "muscles used = ", musclesUsed
    compoundCounter = 0
    isolationCounter = 0
    compoundMax = 10
    isolationMax = 10
    routineWeek = []
    for x in musclesUsed:
        #print "running on ", x
        primary = muscleGroupMajor.objects.filter(muscleActual = x[0]).order_by('?')
        #if len(primary) > 1:
         #   random.shuffle(primary)
        #print "primaries for ", x, " --- ", primary
        for y in primary:
            #print "checking primary", y, " in ", x
            if compoundCounter <= compoundMax:
            #check if there is a compound, use the first one found
                try:
                    compoundLift = auxExercise.objects.get(exerciseActual = y.exerciseActual.pk, isCompound = True)
                    flag = True
                    for t in routineWeek:
                        if t[1] == compoundLift.exerciseActual.pk:
                            flag = False
                            t[2] = t[2] + 1
                    if flag: #exercise does not exist exists, append it
                        routineWeek.append([compoundLift.exerciseActual.exerciseName,compoundLift.exerciseActual.pk,3,5,"Compound exercise for "+x[1]])

                    #if any(t[1] == compoundLift.exerciseActual.pk for t in routineWeek):
                     #   t[2] = t[2] + 1
                    #else:
                     #   routineWeek.append([compoundLift.exerciseActual.exerciseName,compoundLift.exerciseActual.pk,3,5])
                    #print "appended ", y.exerciseActual.exerciseName
                    compoundCounter = compoundCounter + 1
                    break
                except:
                    print "EXERCISE", y.exerciseActual.exerciseName , "NOT COMPOUND. NOT ADDING"

        #print "Working on Secondaries..."
        secondary = muscleGroupMajor.objects.filter(muscleActual = x[0]).order_by('?')
        #if len(secondary) > 1:
        #    random.shuffle(secondary)
        #print "secondaries for ", x, " --- ", secondary
        for y in secondary:
            #print "checking secondary", y, " in ", x
            if isolationCounter <= isolationMax:
                try:
                    isolationLift = auxExercise.objects.get(exerciseActual = y.exerciseActual.pk, isCompound = False)
                    flag = True
                    for t in routineWeek:
                        if t[1] == isolationLift.exerciseActual.pk:
                            flag = False
                            t[2] = t[2] + 1
                    if flag: #exercise does not exist exists, append it
                        routineWeek.append([isolationLift.exerciseActual.exerciseName,isolationLift.exerciseActual.pk, 3, 10, "Isolation exercise for "+x[1]])
                    isolationCounter = isolationCounter + 1
                    break
                except:
                    print "EXERCISE", y.exerciseActual.exerciseName , "NOT ISOLATION. NOT ADDING"
    return routineWeek

@csrf_exempt
def compareUser(request):
    if request.method == 'POST':
        #if request.is_ajax():
        if 1 == 1:
            info = request.POST.getlist('dataSend[]') #Contains {gender:true, bweight:200, rows: [[1,5,225],[2,5,315]]} . [exercisePK, rep, weight]
            info = json.loads(info[0])
            try:
                muscleDict = getMuscleDict() #[{muscleName, primaries[], secondaries[], pk, muscleStrength}..{}]
                outerArr = []
                gender = info['gender'] #true or false
                bodyWeightUser = info['bweight']
                for x in info['rows']:
                    exerciseLookUp = exercise.objects.get(pk = int(x[0]))
                    reps = x[1]
                    weightLifted = x[2]
                    oneRepMax = (weightLifted / (1.0278 - ( 0.0278 * reps))) #Brzycki Formula
                    try:
                        comparison = exerciseCompare2.objects.filter(exerciseActual = exerciseLookUp, genderMale = gender, bodyWeight__lte=bodyWeightUser).order_by('-bodyWeight')[0] #still need to filter by bodyWeight
                    except:
                        comparison = exerciseCompare2.objects.filter(exerciseActual = exerciseLookUp, genderMale = gender).order_by('bodyWeight')[0]
                    value = "Beginner"
                    heur = 1.0
                    if oneRepMax >= comparison.elite:
                        value = "Elite"
                        heur = 5.0
                    elif oneRepMax >= comparison.advanced:
                        value = "Advanced"
                        heur = 4.0 + ((oneRepMax - comparison.elite) / (comparison.elite - comparison.advanced))
                    elif oneRepMax >= comparison.intermediate:
                        value = "Intermediate"
                        heur = 3.0 + ((oneRepMax - comparison.advanced) / (comparison.advanced - comparison.intermediate))
                    elif oneRepMax >= comparison.novice:
                        value = "Novice"
                        heur = 2.0 + ((oneRepMax - comparison.intermediate) / (comparison.intermediate - comparison.novice))
                    elif oneRepMax >= comparison.beginner:
                        value = "Beginner"
                        heur = 1.0 + ((oneRepMax - comparison.beginner) / (comparison.novice - comparison.beginner))
                    valueReturned  = {'Value':value, 'OneRepMax':round(oneRepMax,3), 'ExercisePK':x[0], 'exerciseName': exerciseLookUp.exerciseName, 'Strength':round(heur,3)}
                    print "valueReturned = ", valueReturned
                    outerArr.append(valueReturned)

                    for y in muscleDict:
                        #if y['pk'] == int(x[0]): #if the current exercise(x) uses the given muscle(y). Meaning if there is a muscleGroupMajor or muscleGroupMinor using (exerciseActual=x.pk, muscleActual=y.pk)
                        y = muscleDictPopulateScore(y, int(x[0]), heur)
                muscleDict = calculateMuscleStrength(muscleDict, 0.7, 0.3)


                muscleStatsArr = []
                #print "Printing muscleDict after populate"
                for x in muscleDict:
                    if x['muscleStrength'] > 0:
                        #below returns dict which cant be sorted. Going to return an array instead
                        #muscleStats.append(x)
                        score = "Beginner"
                        if x['muscleStrength'] > 4:
                            score = "Elite"
                        elif x['muscleStrength'] > 3:
                            score = "Advanced"
                        elif x['muscleStrength'] > 2:
                            score = "Intermediate"
                        elif x['muscleStrength'] > 1:
                            score = "Novice"

                        muscleStatsArr.append([x['pk'], x['muscleName'], x['muscleStrength'], score])
                muscleStatsArr = sorted(muscleStatsArr, key=itemgetter(2)) #index #2. Sorting stats by lowest first


                authorAdd = request.user
                newRoutine = routineEntry(author=authorAdd, date=datetime.now)
                newRoutine.save()

                newlyCreated = routineEntry.objects.filter(author=request.user).latest('pk')
                for x in muscleStatsArr:
                    thisMuscle = muscle.objects.get(pk=x[0])
                    newMuscleStat = muscleStats(muscleActual=thisMuscle, muscleStrength=x[2], muscleScore=x[3], entryForm=newlyCreated)
                    newMuscleStat.save()
                    #print "new stat =", newMuscleStat

                #routine building
                routineWeek = {'monday':[], 'tuesday':[], 'wednesday':[], 'thursday':[], 'friday':[]} #contains pks to exercises on their given days
                #start with muscleStats. For each muscle in musclestats (lowest first), select N number of compounds and M number of isolations
                allMuscles = muscle.objects.all()
                for x in allMuscles:
                    if any(t[0] == x.pk for t in muscleStatsArr):
                        #print "nope"
                        pass
                    else:
                        #print "APPENDING ", x.muscleName
                        muscleStatsArr.append([x.pk, x.muscleName, 0, "indeterminate"])

                print "LENGTH OF ROUTINE =", len(muscleStatsArr)
                routineWeek['monday'] = generateMondayRoutine2(muscleStatsArr[:5])
                print "monday routine = ", routineWeek['monday']
                routineWeek['tuesday'] = generateMondayRoutine2(muscleStatsArr[5:10])
                print "tuesday routine = ", routineWeek['tuesday']
                routineWeek['wednesday'] = generateMondayRoutine2(muscleStatsArr[10:15])
                print "wed routine =", routineWeek['wednesday']
                routineWeek['thursday'] = generateMondayRoutine2(muscleStatsArr[:5])
                print "thurs routine =", routineWeek['thursday']
                routineWeek['friday'] = generateMondayRoutine2(muscleStatsArr[5:10])
                print "fri routine = ", routineWeek['friday']

                for x in routineWeek:
                    for y in routineWeek[x]:
                        exerciseAdd = exercise.objects.get(pk=y[1])
                        newExercise = generatedRoutineExercise(entryForm=newlyCreated, exerciseActual=exerciseAdd, sets= y[2], reps = y[3], notes = y[4], routineDay = x)
                        newExercise.save()

                json_stuff = simplejson.dumps({"exerciseStats" : outerArr, "muscleStats" : muscleStatsArr, "routineMonday" : routineWeek['monday'], "routineTuesday" : routineWeek['tuesday'], "routineWednesday" : routineWeek['wednesday'], "routineThursday" : routineWeek['thursday'], "routineFriday" : routineWeek['friday']})
                #print "inbetween"
                return HttpResponse(json_stuff, content_type ="application/json")
            except:
                #print "inside except"
                return HttpResponse("Error in except")
            print "DONE WITH ALL OF IT"

def endFile(request):
    print "end"
    return "end"
