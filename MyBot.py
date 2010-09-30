#!/usr/bin/env python
#

"""
// The DoTurn function is where your code goes. The PlanetWars object contains
// the state of the game, including information about all planets and fleets
// that currently exist. Inside this function, you issue orders using the
// pw.IssueOrder() function. For example, to send 10 ships from planet 3 to
// planet 8, you would say pw.IssueOrder(3, 8, 10).
"""

import logging
from os import remove
LOG_FILENAME = 'mybot.log'
remove(LOG_FILENAME)
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,format='%(asctime)s %(message)s')

from math import ceil
from PlanetWars import PlanetWars

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

  # Figure out where I have excesss
  debug("status")
  for p in pw.MyPlanets():
    if p.NumShips() > .5*DefenseRequired(pw, p, enemyPlanets):
      defendedPlanets.append(p)
    else:
      vulnerablePlanets.append(p)
      
  # Look for a good bargin
  debug("looking for bargins")
  for taker in defendedPlanets:
    debug(str(taker.PlanetID()))
    for p in neutralPlanets:
      dist = pw.Distance(p, taker)
      if BreakEvenTurns(p, dist) < 20:        
        attackFleetSize = FleetRequiredToTake(p, dist) + 10
        if taker.NumShips() > attackFleetSize: 
          logging.debug(str(taker.PlanetID()) + " sent " + str(attackFleetSize) + \
                        " to " + str(p.PlanetID()))
          pw.IssueOrder(taker, p, attackFleetSize)
          taker.NumShips(taker.NumShips()-attackFleetSize)
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
