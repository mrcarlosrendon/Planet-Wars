#!/usr/bin/env python
#

"""
// The DoTurn function is where your code goes. The PlanetWars object contains
// the state of the game, including information about all planets and fleets
// that currently exist. Inside this function, you issue orders using the
// pw.IssueOrder() function. For example, to send 10 ships from planet 3 to
// planet 8, you would say pw.IssueOrder(3, 8, 10).
"""

from PlanetWars import PlanetWars
from PlanetWars import Planet
from math import ceil
from Log import debug

distances = []
nearestNeighbors = []

def DebugOrder(attacker, to, amount, remaining):
  debug(str(attacker.PlanetID()) + " sent " + \
        str(amount) + " to " + str(to.PlanetID()) + \
        ", " + str(remaining) + " remaining")

def Distance(p1id, p2id):
  if isinstance(p1id, Planet) and isinstance(p2id, Planet):
    return distances[p1id.PlanetID()][p2id.PlanetID()][1]
  return distances[p1id][p2id][1]

def ComputePlanetDistances(pw):
  planets = sorted(pw.Planets(), key=lambda x: x.PlanetID())
  for p in planets:
    dists = []
    for q in planets:
      dists.append((q.PlanetID(), pw.Distance(p,q)))
    nearestNeighbors.append(sorted(dists, key=lambda x: x[1]))
    distances.append(dists)

class PlanetSim:
    """Useful for predicting the future state of a planet based on
    incoming fleets"""
    def __init__(self, startingShips, rate, isNeutral):
      if isNeutral:        
        self.startingShips = 0
        self.neutralShips = startingShips
      else:
        self.startingShips = startingShips
        self.neutralShips = 0        
      self.rate = rate
      self.fleets = []
    def addFleet(self, turn, numShips):
      self.fleets.append((turn, numShips))
    def delFleet(self, turn, numShips):
      self.fleets.remove((turn, numShips))
    def findMinFleetOwn(self, turn):
      # what if we do nothing
      (taken, left) = self.simulate()
      if taken and left > 0: # nothing bad will happen
        return 0
      elif not taken and left > 0: # still neutral, just attack
        return left + 1
      currFleetSize = 0
      while left < 0:
        currFleetSize += 1
        self.addFleet(turn, currFleetSize)
        (taken, left) = self.simulate()
        self.delFleet(turn, currFleetSize)
      return currFleetSize
    def simulate(self):
      """After all fleets have come in, how many ships does the
      planet have?"""
      def reducedFleets():
        """Reduce the fleets so that if multiple fleets happen on
        the same turn, there combined effect is reduced to one
        event"""
        reduced = []
        fleets = sorted(self.fleets, key=lambda x: x[0])
        currTurn = 0
        reducedValue = 0
        for e in fleets:
          if e[0] == currTurn:
            reducedValue += e[1]
          else:
            reduced.append((currTurn,reducedValue))
            reducedValue = e[1]
            currTurn = e[0]
        if reducedValue:
          reduced.append((currTurn, reducedValue))
        return reduced
      currTurn = 0
      ships = self.startingShips
      neuShips = self.neutralShips
      for e in reducedFleets():
        remain = e[1]
        if neuShips > 0:
          if e[1] >= neuShips:
            remain = neuShips - e[1]
            neuShips = 0
          else:
            neuShips -= e[1]
            remain = 0
        if neuShips == 0 and remain:
          turns = e[0] - currTurn
          if ships >= 0:
            ships += self.rate*turns + remain
          else:
            ships -= self.rate*turns + remain
        currTurn = e[0]
      if neuShips:
        return (False, neuShips)
      else:
        return (True, ships)


def BreakEvenTurns(pw, planet, fleetDistance):
  """Returns number of turns it will take to break even on
  taking this planet.
  """
  if planet.GrowthRate() == 0:
    debug("wtf, ZERO GROWTH on " + str(planet.PlanetID()))
    return 100000
  cost = FleetRequiredToTake(pw, planet, fleetDistance)
  # if it is already being taken, then we won't break even
  if cost <= 0:
    debug(str(planet.PlanetID()) + " already being taken")
    return 100000
  if planet.Owner() == 2:
    # enemy planets pay back in half the time
    # because there is the growth that the enemy didn't get
    # plus the growth that I did get
    returnRate = 2*float(planet.GrowthRate())
  else:
    returnRate = float(planet.GrowthRate())
  return int(ceil(cost / returnRate))

def FleetRequiredToTake(pw, planet, fleetDistance):
  """Returns the exact size of a fleet required to take the given
  planet.
  """
  sim = PlanetSim(planet.NumShips(), planet.GrowthRate(), planet.Owner()==0)
  for f in pw.Fleets():
    if f.DestinationPlanet() == planet.PlanetID():
      sim.addFleet(f.TurnsRemaining(),f.NumShips())
  minFleet = sim.findMinFleetOwn(fleetDistance)
  debug(str(minFleet) + " required to take " + str(planet.PlanetID()))
  return minFleet

def GeneralDefenseRequired(pw, planet):
  """How many reserves do I need if the nearest enemies send everything"""
  defense = 0
  rate = planet.GrowthRate()
  neighbors = nearestNeighbors[planet.PlanetID()]
  for n in neighbors:
    # If enemy and can hit me in 15 turns or less
    p = pw.GetPlanet(n[0])
    if n[1] < 15 and p.Owner() == 2:
      defense += p.NumShips() - rate*Distance(n[0], planet.PlanetID())
  defense = int(ceil(defense))
  debug("GeneralDefenseRequired planet " + str(planet.PlanetID()) + " " + str(defense))
  return defense

def DefenseRequiredForIncoming(pw, planet):
  """How many reserves do I need to leave to protect me from the
  incoming waves?"""
  sim = PlanetSim(planet.NumShips(), planet.GrowthRate(), planet.Owner()==0)
  for f in pw.Fleets():
    if f.DestinationPlanet() == planet.PlanetID():
      sim.addFleet(f.TurnsRemaining(),f.NumShips())
  required = sim.findMinFleetOwn(0)
  debug(str(required) + " required to defend " + str(planet.PlanetID()) + " from incoming ")
  return required

def DoTurn(pw):
  orders = []
  urgentPlanets = []
  myPlanets = []
  enemyTargets = []
  enemyPlanets = pw.EnemyPlanets()
  neutralPlanets = pw.NeutralPlanets()
  myFleets = pw.MyFleets()
  enemyFleets = pw.EnemyFleets()
  enemySize = 0
  mySize = 0

  # Interplanetary distances will come in handy
  if not distances:
    ComputePlanetDistances(pw)

  # How am I doing?
  debug("Status")
  for p in pw.MyPlanets():
    mySize = mySize + p.NumShips()
    defInc = DefenseRequiredForIncoming(pw, p)
    # Who needs help urgently, and how much?
    if p.NumShips() < defInc:
      urgentPlanets.append((p, defInc))
    else:
      myPlanets.append((p, int(ceil(.75*GeneralDefenseRequired(pw, p)))))

  # How is the enemy doing?
  for p in enemyPlanets:
    enemySize = enemySize + p.NumShips()

  if ( enemySize <= 0 ):
    winRatio = 0
  else:
    winRatio = float(mySize)/enemySize
  debug("Ratio: " + str(winRatio))

  # Defend myself first
  debug("Defense")
  # some urgent planets are more urgent
  urgentPlanets.sort(key=lambda x: x[0].GrowthRate(), reverse=True)  
  for helpme in urgentPlanets:
    totalNeeded = helpme[1]
    helpsofar = 0
    plannedSend = []
    # Make a defense plan. Prefer close help
    for helper in sorted(myPlanets, key=lambda x: Distance(x[0],helpme[0])):
      # Don't undefend yourself      
      tosend = helper[0].NumShips()
      defReq = helper[1]
      if defReq > 0:
        tosend -= defReq
      if tosend <= 0:
        continue        
      # Only send what is still needed
      stillNeeded = totalNeeded - helpsofar
      if tosend > stillNeeded:
        tosend = stillNeeded
      plannedSend.append((helper[0], helpme[0], tosend))
      helpsofar += tosend
      if helpsofar >= totalNeeded:
        break
    # issue actual orders
    if helpsofar >= totalNeeded:
      for p in plannedSend:
        pw.IssueOrder(p[0], p[1], p[2])
        remaining = p[0].NumShips()-p[2]
        DebugOrder(p[0], p[1], p[2], remaining)
        orders.append(p)
        p[0].NumShips(remaining)
    # else, TODO: this planet is BONED until I fix

  # Maximize investments, Minimize enemy
  targets = enemyPlanets+neutralPlanets
  debug("Offense")
  for taker in myPlanets:
    debug(str(taker[0].PlanetID()))
    defenseReq = max(DefenseRequiredForIncoming(pw, taker[0]), \
                       int(ceil(.50*GeneralDefenseRequired(pw, taker[0]))))
    surplus = taker[0].NumShips()
    if defenseReq > 0:
      surplus -= defenseReq
    potTargets = []    
    # Calculate investement risks for this taker
    for p in targets:
      dist = Distance(p.PlanetID(), taker[0].PlanetID())
      breakEvenTurns = BreakEvenTurns(pw, p, dist)
      potTargets.append((p, breakEvenTurns))
    # Prefer lower risk, take as many targets as possible
    potTargets.sort(key=lambda x: x[1])
    for potTarget in potTargets:
      needed = FleetRequiredToTake(pw, potTarget[0], \
                                    Distance(potTarget[0].PlanetID(), p.PlanetID()))
      # take if we can
      if needed > 0 and surplus > needed:
        pw.IssueOrder(taker[0], potTarget[0], needed)
        remaining = taker[0].NumShips() - needed
        DebugOrder(taker[0], potTarget[0], needed, remaining)
        taker[0].NumShips(remaining)
        surplus -= needed
        # remove this from the targets list
        for t in targets:
          if t.PlanetID() == potTarget[0].PlanetID():
            targets.remove(t)
            break
      elif surplus <= 0:
        break

def main():
  debug("starting")
  map_data = ''
  while(True):
    current_line = raw_input()
    if len(current_line) >= 2 and current_line.startswith("go"):
      pw = PlanetWars(map_data)
      debug("NEW TURN")
      DoTurn(pw)
      pw.FinishTurn()
      debug("TURN FINISHED")
      map_data = ''
    else:
      map_data += current_line + '\n'


if __name__ == '__main__':
  try:
    import psyco
    psyco.full()
  except ImportError:
    pass
  try:
    main()
  except KeyboardInterrupt:
    print 'ctrl-c, leaving ...'
