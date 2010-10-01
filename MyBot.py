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

def GeneralDefenseRequired(pw, planet, enemies):
  """How many reserves do I need to leave if they send everything at me?"""
  defense = 0
  rate = planet.GrowthRate()
  for enemy in enemies:
    defense += enemy.NumShips() - \
               rate*pw.Distance(enemy, planet)
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
  # TODO, take into account incoming reinforcements
  #for f in pw.MyFleets():
  #  if f.DestinationPlanet() == planet.PlanetID():
  #    adj = f.NumShips() - int(ceil(rate*f.TurnsRemaining()))
  #    if adj > 0:
  #      defense -= adj
  defense = int(ceil(defense))
  if defense != 0:
    debug("DefenseRequiredForIncoming planet " + str(planet.PlanetID()) + " " + str(defense))
  return defense

def DoTurn(pw):
  defendedPlanets = []
  vulnerablePlanets = []
  enemyPlanets = pw.EnemyPlanets()
  neutralPlanets = pw.NeutralPlanets()
  myFleets = pw.MyFleets()
  enemyFleets = pw.EnemyFleets()
  enemySize = 0
  mySize = 0

  # How am I doing?
  debug("status")
  for p in pw.MyPlanets():
    mySize = mySize + p.NumShips()
    if p.NumShips() > DefenseRequiredForIncoming(pw, p) and \
           p.NumShips() > .5*GeneralDefenseRequired(pw, p, enemyPlanets):
      defendedPlanets.append(p)
    else:
      vulnerablePlanets.append(p)

  # How is the enemy doing?
  for p in enemyPlanets:
    enemySize = enemySize + p.NumShips()

  if ( enemySize <= 0 ):
    winRatio = 0
  else:
    winRatio = float(mySize)/enemySize
  debug("Ratio: " + str(winRatio))

  # Should I go for the kill?
  if winRatio > 1.5:
    debug("Kill Kill Kill!!!!")
    for p in enemyPlanets:
      alreadySent = 0
      for mp in pw.MyPlanets():
        defenseReq = max(DefenseRequiredForIncoming(pw,mp), int(ceil(.05*GeneralDefenseRequired(pw, mp, enemyPlanets))))
        toSend = mp.NumShips()
        # Don't put youtself at too much risk
        if defenseReq > 0:
          toSend -= defenseReq
        # Only send enough to kill
        necToKill = FleetRequiredToTake(pw, p, pw.Distance(mp, p))
        if necToKill > 0:
          if necToKill - alreadySent < toSend:
            toSend = necToKill - alreadySent
        else:
          toSend = 0
        if toSend > 0 and mp.NumShips() - toSend > 0:          
          pw.IssueOrder(mp, p, toSend)
          debug(str(mp.PlanetID()) + " sent " + str(toSend) + \
                        " to " + str(p.PlanetID()))
          mp.NumShips(mp.NumShips()-toSend)
          debug(str(mp.NumShips()) + " left")
          alreadySent += toSend
    return
      
  # Look for a good bargin
  debug("looking for bargins")
  attackedPlanets = []
  for f in myFleets:
    attackedPlanets.append(f.DestinationPlanet())
  if len(defendedPlanets)==0:
    debug("no defense, might as well attack")
    defendedPlanets = vulnerablePlanets
  for taker in defendedPlanets:
    debug(str(taker.PlanetID()))
    for p in enemyPlanets+neutralPlanets:
      if attackedPlanets.count(p.PlanetID()) > 0:
        continue
      dist = pw.Distance(p, taker)
      if BreakEvenTurns(pw, p, dist) < 50:
        defenseReq = max(DefenseRequiredForIncoming(pw, p), int(ceil(.25*GeneralDefenseRequired(pw, p, enemyPlanets))))
        attackFleetSize = FleetRequiredToTake(pw, p, dist)
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
