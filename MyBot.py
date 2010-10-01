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
from os import remove
from os.path import isfile
import logging

BOT_LOG_FILENAME = 'mybot.log'
if isfile(BOT_LOG_FILENAME):
  remove(BOT_LOG_FILENAME)
logging.basicConfig(filename=BOT_LOG_FILENAME,level=logging.DEBUG,format='%(asctime)s %(message)s')

def debug(message):
  logging.debug(message)

def BreakEvenTurns(planet, fleetDistance):
  """Returns number of turns it will take to break even on
  taking this planet.
  """
  if planet.GrowthRate() == 0:
    return 10000
  return int(ceil(FleetRequiredToTake(planet, fleetDistance) + \
         planet.NumShips() / float(planet.GrowthRate())))

def FleetRequiredToTake(planet, fleetDistance):
  """Returns the exact size of a fleet required to take the given
  planet, assuming no other fleets are sent there  
  """
  # TODO: take into accounts fleets already headed to the planet
  if planet.Owner() == 0: #neutral
    return planet.NumShips() + 1
  else:
    return int(ceil(planet.NumShips() + planet.GrowthRate()*fleetDistance + 1))

def DefenseRequired(pw, planet, enemies):
  defense = 0
  rate = planet.GrowthRate()
  size = planet.NumShips()
  for enemy in enemies:
    defense += enemy.NumShips() - \
               rate*pw.Distance(enemy, planet)
  defense = int(ceil(defense))
  debug("DefenseRequired planet " + str(planet.PlanetID()) + " " + str(defense))
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
    if p.NumShips() > .5*DefenseRequired(pw, p, enemyPlanets):
      defendedPlanets.append(p)
    else:
      vulnerablePlanets.append(p)

  # How is the enemy doing?
  for p in enemyPlanets:
    enemySize = enemySize + p.NumShips()

  winRatio = float(mySize)/enemySize
  debug("Ratio: " + str(winRatio))

  # Should I go for the kill?
  if winRatio > 1.5:
    debug("Kill Kill Kill!!!!")
    for p in enemyPlanets:
      required = FleetRequiredToTake(p, 100) # TODO fudging here for now
      for mp in pw.MyPlanets():
        if required > 0:
          defenseReq = int(ceil(.10*DefenseRequired(pw, mp, enemyPlanets)))
          toSend = mp.NumShips() - defenseReq
          if mp.NumShips() - toSend > 0:          
            pw.IssueOrder(mp, p, toSend)
            logging.debug(str(mp.PlanetID()) + " sent " + str(toSend) + \
                          " to " + str(p.PlanetID()))
            mp.NumShips(mp.NumShips()-toSend)
            logging.debug(str(mp.NumShips()) + " left")
            required = required - toSend
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
      if BreakEvenTurns(p, dist) < 50:
        defenseReq = int(ceil(.25*DefenseRequired(pw, p, enemyPlanets)))
        attackFleetSize = FleetRequiredToTake(p, dist)
        if defenseReq > 0:
          attackFleetSize = attackFleetSize + defenseReq
        if attackFleetSize > 0 and taker.NumShips() > attackFleetSize: 
          logging.debug(str(taker.PlanetID()) + " sent " + str(attackFleetSize) + \
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
