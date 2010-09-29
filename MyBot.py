#!/usr/bin/env python
#

"""
// The DoTurn function is where your code goes. The PlanetWars object contains
// the state of the game, including information about all planets and fleets
// that currently exist. Inside this function, you issue orders using the
// pw.IssueOrder() function. For example, to send 10 ships from planet 3 to
// planet 8, you would say pw.IssueOrder(3, 8, 10).
"""

# myProduction = sum(my_planets.growthrate*
# Each turn: Maximize, (myProduction - enemiesProduction)



from PlanetWars import PlanetWars

def DoTurn(pw):
  # (1) Limit fleets based on number of planets
  if len(pw.MyFleets()) >= 1*len(pw.MyPlanets()):
    return
  # (2) Find my strongest planet.
  source = -1
  source_score = -999999.0
  source_num_ships = 0
  my_planets = pw.MyPlanets()
  for p in my_planets:
    score = float(p.NumShips() + (1.0/p.GrowthRate()))
    if score > source_score:
      source_score = score
      source = p.PlanetID()
      source_num_ships = p.NumShips()

  # (3) Find the weakest enemy planet.
  dest = -1
  dest_score = -999999.0
  not_my_planets = pw.NotMyPlanets()
  for p in not_my_planets:
    score = (1.0 + p.GrowthRate()) / p.NumShips()
    # boost score to make more aggressive
    if p.Owner() == 1:      
      score = (1+.50)*score
    if score > dest_score:
      dest_score = score
      dest = p.PlanetID()

  # (4) Send half the ships from my strongest planet to the weakest
  # planet that I do not own.
  if source >= 0 and dest >= 0:
    num_ships = source_num_ships / 2
    pw.IssueOrder(source, dest, num_ships)


def main():
  map_data = ''
  while(True):
    current_line = raw_input()
    if len(current_line) >= 2 and current_line.startswith("go"):
      pw = PlanetWars(map_data)
      DoTurn(pw)
      pw.FinishTurn()
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
