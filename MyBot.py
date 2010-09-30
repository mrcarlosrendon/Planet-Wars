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
  return ceil(FleetRequiredToTake(planet, fleetDistance) + \
         planet.NumShips() / float(planet.GrowthRate()))  

def FleetRequiredToTake(planet, fleetDistance):
  """Returns the exact size of a fleet required to take the given
  planet, assuming no other fleets are sent there  
  """
  # TODO: take into accounts fleets already headed to the planet
  if planet.Owner() == 0: #neutral
    return planet.NumShips()
  else:
    return planet.NumShips() + planet.GrowthRate()*fleetDistance  

def DefenseRequired(pw, planet, enemies):
  defense = 0
  rate = planet.GrowthRate()
  size = planet.NumShips()
  for enemy in enemies:
    defense += enemy.NumShips() - \
               rate*pw.Distance(enemy, planet)
  defense = ceil(defense)
  debug("DefenseRequired planet " + str(planet.PlanetID()) + " " + str(defense))
  return defense

def DoTurn(pw):
  defendedPlanets = []
  vulnerablePlanets = []
  enemyPlanets = pw.EnemyPlanets()
  neutralPlanets = pw.NeutralPlanets()
  myFleets = pw.MyFleets()
  enemyFleets = pw.EnemyFleets()

  # Figure out where I have excesss
  debug("status")
  for p in pw.MyPlanets():
    if p.NumShips() > .5*DefenseRequired(pw, p, enemyPlanets):
      defendedPlanets.append(p)
    else:
      vulnerablePlanets.append(p)
      
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
        attackFleetSize = FleetRequiredToTake(p, dist) + ceil(.25*DefenseRequired(pw, p, enemyPlanets))
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
