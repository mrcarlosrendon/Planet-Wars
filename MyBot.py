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
from math import ceil
from Log import debug

distances = []
nearestNeighbors = []

def Distance(p1id, p2id):
  return distances[p1id][p2id][1]

def ComputePlanetDistances(pw):
  planets = sorted(pw.Planets(), key=lambda x: x.PlanetID())
  for p in planets:
    dists = []
    for q in planets:
      dists.append((q.PlanetID(), pw.Distance(p,q)))
    nearestNeighbors.append(sorted(dists, key=lambda x: x[1]))
    distances.append(dists)

def BreakEvenTurns(pw, planet, fleetDistance):
  """Returns number of turns it will take to break even on
  taking this planet.
  """
  if planet.GrowthRate() == 0:
    debug("wtf, ZERO GROWTH")
    return 10000
  return int(ceil(FleetRequiredToTake(pw, planet, fleetDistance) + \
         planet.NumShips() / float(planet.GrowthRate())))

def FleetRequiredToTake(pw, planet, fleetDistance):
  """Returns the exact size of a fleet required to take the given
  planet.
  """
  # take into accounts fleets already headed to the planet
  required = planet.NumShips() + 1
  for f in pw.Fleets():
    if f.DestinationPlanet() == planet.PlanetID():
      adj = f.NumShips() - int(ceil(planet.GrowthRate()*f.TurnsRemaining()))
      if f.Owner == 2 and adj > 0: # enemy
        required += adj
      if f.Owner == 1 and adj < 0: # mine
        required -= adj            
  if planet.Owner() == 2: # enemy 
    required += int(ceil(planet.GrowthRate()*fleetDistance + 1))    
  return required

def GeneralDefenseRequired(pw, planet):
  """How many reserves do I need if the nearest enemies send everything"""
  defense = 0
  rate = planet.GrowthRate()
  neighbors = nearestNeightbors[planet.PlanetID()]
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
  defense = 0
  rate = planet.GrowthRate()
  for f in pw.EnemyFleets():
    if f.DestinationPlanet() == planet.PlanetID():
      adj = f.NumShips() - int(ceil(rate*f.TurnsRemaining()))
      if adj > 0:
        defense += adj
  # take into account incoming reinforcements
  for f in pw.MyFleets():
    if f.DestinationPlanet() == planet.PlanetID():
      adj = f.NumShips() - int(ceil(rate*f.TurnsRemaining()))
      if adj > 0:
        defense -= adj
  defense = int(ceil(defense))
  if defense != 0:
    debug("DefenseRequiredForIncoming planet " + str(planet.PlanetID()) + " " + str(defense))
  return defense

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
    needed = helpme[1]
    helpsofar = 0
    plannedSend = []
    # Make a defense plan. Prefer close help
    for helper in sorted(myPlanets, key=lambda x: Distance(x[0],helpme[0])):
      # Don't undefend yourself
      tosend = helper[0].NumShips() - helper[1]
      if tosend <= 0:
        continue        
      # Only send what is needed
      if tosend > needed:
        tosend = needed
      plannedSend.append((helper[0].PlanetID(), helpme[0].PlanetID(), tosend))
      helpsofar += tosend
      if helpsofar >= needed:
        break
    # issue actual orders
    if helpsofar >= needed:
      for p in plannedSend:
        pw.IssueOrder(p)
        orders.append(p)
        sender = pw.GetPlanet(p[0])
        sender.NumShips(sender.NumShips()-p[2])
    # else, TODO: this planet is BONED until I fix

  # Maximize investments, Minimize enemy
  debug("Offense")
  for taker in myPlanets:
    debug(str(taker[0].PlanetID()))

    defenseReq = max(DefenseRequiredForIncoming(pw, p), \
                       int(ceil(.50*GeneralDefenseRequired(pw, p, enemyPlanets))))

    # Figure out what is most valueble for this taker
    for p in enemyPlanets+neutralPlanets:
      dist = Distance(p.PlanetID(), taker[0].PlanetID())
      breakEvenTurns = BreakEvenTurns(pw, p, dist)
      # how to create score from these three parameters?
      

      
        if defenseReq > 0:
          attackFleetSize = attackFleetSize + defenseReq
        if attackFleetSize > 0 and taker.NumShips() > attackFleetSize: 
          debug(str(taker.PlanetID()) + " sent " + str(attackFleetSize) + \
                        " to " + str(p.PlanetID()))
          pw.IssueOrder(taker, p, attackFleetSize)
          taker.NumShips(taker.NumShips()-attackFleetSize)
          attackedPlanets.append(p.PlanetID())
          break
        else:
          debug("not enough ships")

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
