#!/usr/bin/env python
#

"""
// The DoTurn function is where your code goes. The PlanetWars object contains
// the state of the game, including information about all planets and fleets
// that currently exist. Inside this function, you issue orders using the
// pw.IssueOrder() function. For example, to send 10 ships from planet 3 to
// planet 8, you would say pw.IssueOrder(3, 8, 10).
//
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own. Check out the tutorials and articles on the contest website at
// http://www.ai-contest.com/resources.
"""

from PlanetWars import PlanetWars
from math import floor
import sys

# These weights are used to determine what percentage of force to use
defense_weight = 0.0 # spent on defending my planets
attack_weight  = 0.0 # spent on taking enemy planets
expand_weight  = 0.0 # spent on conquering neutral planets

# some preset weights
BALANCED           = (0.50, 0.25, 0.25)
STEADY_GOING       = (0.70, 0.30, 0.00)
DEFEND_ONLY        = (1.00, 0.00, 0.00)
ATTACK_ONLY        = (0.00, 1.00, 0.00)
EXPAND_ONLY        = (0.00, 0.00, 1.00)
EXPAND_AGRESSIVELY = (0.55, 0.00, 0.45)
ATTACK_AGRESSIVELY = (0.55, 0.45, 0.00)

(defense_weight, attack_weight, expand_weight) = BALANCED

# The first turn is a special case and ignores the above weights
first_turn = True

def DoTurn(pw):
  global defense_weight
  global attack_weight
  global expand_weight
  global first_turn

  log(pw.ToString())

  i_my_planets = [p.PlanetID() for p in pw.MyPlanets()]
  # a list of my planet IDs
  
  ### Analyze and Strategize
  my_total_growth = sum([p.GrowthRate() for p in pw.MyPlanets()])
  enemy_total_growth = sum([p.GrowthRate() for p in pw.EnemyPlanets()])
  if my_total_growth > enemy_total_growth:
    reweight(STEADY_GOING)
  else:
    reweight(BALANCED)

  if first_turn:
    first_turn = False
    ### First Turn
    # attack enemy homeworld with 80% of forces
    i_p = i_my_planets[0]
    amount = int(round(pw.GetPlanet(i_p).NumShips() * 0.8))
#pw.IssueOrder(i_p, pw.EnemyPlanets()[0].PlanetID(), amount)
    # TODO: consider taking neutral planets on the first turn
    # TODO: try out NYY's strategy of immediately migrating to a better cluster
    # of planets

  #TODO: consider removing this else
  else:
    i_threatened_planets = set()
    # contains planets with enemy forces on the way
    i_threats = {}
    # planet_id => [list of enemy fleets headed here]
    i_aids = {}
    # planet_id => [list of my fleets headed here]
    i_surplus_forces = {}
    # planet_id => fleets on this planet that can be deployed right now
    total_surplus = 0
    # keeps track of the total ships available for deployment

    ### Defend Threatened Planets
    # assume the fleets are merged by the server
    # NOTE: summarizing all fleets might be more efficient as a single loop
    for f in pw.EnemyFleets():
      # summarize attacking forces
      if f.DestinationPlanet() in i_my_planets:
        i_dst = f.DestinationPlanet()
        i_threatened_planets.add(i_dst)
        if i_dst in i_threats:
          i_threats[i_dst].append(f)
        else:
          i_threats[i_dst] = [f]
    for f in pw.MyFleets():
      # summarize what aid is on the way
      if f.DestinationPlanet() in i_my_planets:
        i_dst = f.DestinationPlanet()
        if i_dst in i_aids:
          i_aids[i_dst].append(f)
        else:
          i_aids[i_dst] = [f]

    ## Compute what aid is needed
    i_defense_requests = {} # list of (howmany,when) for each planet id
    for i_threatened in i_threatened_planets:
      planet = pw.GetPlanet(i_threatened)
      total_threat = 0 # sum([f.NumShips() for f in threats[i_threatened]])
      # sort threats by arrival order
      i_threats[i_threatened].sort(cmpFleetArrival)
      min_surplus = planet.NumShips()
      # check if any fleet will defeat
      for f in i_threats[i_threatened]:
        total_threat += f.NumShips()
        #count generated ships
        gen = f.TurnsRemaining()*planet.GrowthRate()
        #count my arriving ships
        if i_aids.has_key(i_threatened):
          aid = sum([a.NumShips() for a in i_aids[i_threatened] \
                                  if a.TurnsRemaining() <= f.TurnsRemaining()])
        else:
          aid = 0
        # does this planet need help?
        # log("Planet %d needs to have %d ships %d turns from now."%(i_threatened, total_threat+1, f.TurnsRemaining()))
        need = total_threat - gen - aid - planet.NumShips() + 1
        # log("Needs %d ships before then to make it happen."%need)
        if need <= 0:
          min_surplus = min(min_surplus, -need)
          # we can spare at most -need ships
        if need > 0:
          # send a request for help!
          if not i_defense_requests.has_key(i_threatened):
            i_defense_requests[i_threatened] = []
          i_defense_requests[i_threatened].append([need, f.TurnsRemaining()])
      # TODO: verify that I calculate surplus correctly
      i_surplus_forces[i_threatened] = min_surplus
      total_surplus += min_surplus

    # Finish computing surplus forces
    for id in i_my_planets:
      planet = pw.GetPlanet(id)
      if id in i_threatened_planets:
        continue
      i_surplus_forces[id] = planet.NumShips()
      total_surplus += planet.NumShips()

    # log AI state before triage
    log("( D , A , X )")
    logvar((defense_weight, attack_weight, expand_weight))
    log("i_threatened_planets")
    logvar(i_threatened_planets)
    log("i_defense_requests")
    logvar(i_defense_requests)
    log("i_surplus_forces")
    logvar(i_surplus_forces)

    ## Triage
    triage_points = int(round(total_surplus * defense_weight))
    # sort the defense requests by planet growth rate, descending
    requesters = [pw.GetPlanet(id) for id in i_defense_requests.iterkeys()]
    requesters.sort(cmpPlanetProduction, reverse=True)
    # meet as many requests as we can afford
    for planet in requesters:
      # no point in pointless looping
      if triage_points == 0:
        break
      # handle all the requests we can for this planet
      for request in i_defense_requests[planet.PlanetID()]:
        # can we afford this?
        if triage_points == 0:
          break
        if request[0] > triage_points:
          # don't waste any units on this request
          # TODO: if we can't afford this request, we can't keep this planet.
          # We may as well write it off as a loss and cancel all requests from
          # this planet. Or should we?
          continue
        # Find planets in range
        # It sure would be handy to have a cache of planet distances...
        # Even so, there's sure to be a better way to compute this
        i_close_planets = [id for id in i_my_planets \
                            if pw.Distance(id, planet.PlanetID()) <= request[1]]
        for i_src_planet in i_close_planets:
          # ASSERT( request[0] <= triage_points )
          if i_surplus_forces[i_src_planet] == 0:
            continue
          if i_surplus_forces[i_src_planet] >= request[0]:
            # request can be satisfied from this planet
            amount = request[0]
            # log("surplus on %d is %d"%(i_src_planet, i_surplus_forces[i_src_planet]))
            pw.IssueOrder(i_src_planet, planet.PlanetID(), amount)
            log("Defending %d with %d ships from %d"%(planet.PlanetID(), amount, i_src_planet))
            i_surplus_forces[i_src_planet] -= amount
            request[0] = 0
            triage_points -= amount
            break
          else:
            # partially satisfy request
            amount = i_surplus_forces[i_src_planet] # it's all we have!
            # log("surplus on %d is %d"%(i_src_planet, i_surplus_forces[i_src_planet]))
            pw.IssueOrder(i_src_planet, planet.PlanetID(), amount)
            log("Partially defending %d with %d ships from %d"%(planet.PlanetID(), amount, i_src_planet))
            i_surplus_forces[i_src_planet] = 0
            request[0] -= amount
            triage_points -= amount
            
    ### Offensive
    attack_points = int(round(total_surplus * attack_weight))
    expand_points = int(round(total_surplus * expand_weight))
    # use up any leftover defense points
    if triage_points > 0:
      attack_points += int(round(triage_points * attack_weight / \
                                (attack_weight + expand_weight)))
      expand_points += int(round(triage_points * expand_weight / \
                                (attack_weight + expand_weight)))
      #triage_points = 0
    ## Attack the Enemy
    targets = pw.EnemyPlanets()
    targets.sort(cmpEnemyTargets, reverse=True)
    for target in targets:
      if attack_points == 0:
        break
      for id in i_surplus_forces.iterkeys():
        if i_surplus_forces[id] == 0:
          continue
        if attack_points == 0:
          break
        amount = min(i_surplus_forces[id], attack_points)
        # log("surplus on %d is %d"%(id, i_surplus_forces[id]))
        pw.IssueOrder(id, target.PlanetID(), amount)
        log("Attacking %d with %d ships from %d."%(target.PlanetID(), amount, id))
        # logvar(amount)
        i_surplus_forces[id] -= amount
        attack_points -= amount
        
    ## Claim Neutral Planets
    # rank neutral planets by desirability
    # TODO: consider planet distance
    prospects = pw.NeutralPlanets()
#prospects.sort(cmpPlanetProduction, reverse=True)
    prospects.sort(cmpProspects, reverse=True)
    # The sum of surplus forces should be equal to expand_points
    for prospect in prospects:
      inbound_force = sum([f.NumShips() for f in pw.MyFleets() \
                             if f.DestinationPlanet() == prospect.PlanetID()])
      inbound_challengers = sum([f.NumShips() for f in pw.EnemyFleets() \
                             if f.DestinationPlanet() == prospect.PlanetID()])
      # TODO: consider inbound enemy fleets, arrive after them?
      # Maybe reserve ships now to snipe them just as they take it?
      need = prospect.NumShips() - inbound_force + inbound_challengers + 1
      for id in i_surplus_forces.iterkeys():
        if i_surplus_forces[id] == 0:
          continue
        if need <= 0:
          break
        amount = min(i_surplus_forces[id], need)
        # log("surplus on %d is %d"%(id, i_surplus_forces[id]))
        pw.IssueOrder(id, prospect.PlanetID(), amount)
        log("Expanding to %d with %d ships from %d."%(prospect.PlanetID(), amount, id))
        i_surplus_forces[id] -= amount
        need -= amount
        expand_points -= amount

def cmpEnemyTargets(p1, p2):
  "A cmp function to determine which planet to attack first."
  growth_cmp = cmpPlanetProduction(p1, p2)
  if growth_cmp == 0:
    return cmp(p1.NumShips(), p2.NumShips())
  else:
    return growth_cmp

def cmpFleetArrival(f1, f2):
  "A cmp function to determine which fleet will arrive first."
  # This function only exists to get a line of code under 80 chars
  return cmp(f1.TurnsRemaining(), f2.TurnsRemaining())

def cmpPlanetProduction(p1, p2):
  "A cmp function to determine which planet produces more."
  return cmp(p1.GrowthRate(), p2.GrowthRate())

def cmpProspects(p1, p2):
  "A cmp function to determine which neutral planet is better."
  # a larger w is a 'better' prospect
  # TODO: tune these weights and find a way to factor in distance
  if p1.NumShips() == 0:
    w1 = p1.GrowthRate() * 10 # same as if there were one ship
  else:
    w1 = p1.GrowthRate() * 10 / float(p1.NumShips())
  if p2.NumShips() == 0:
    w2 = p2.GrowthRate() * 10
  else:
    w2 = p2.GrowthRate() * 10 / float(p2.NumShips())
  return cmp(w1, w2)

def reweight(weights):
  global defense_weight
  global attack_weight
  global expand_weight
  (defense_weight, attack_weight, expand_weight) = weights

def log(str):
  "Log a string to stderr"
  sys.stderr.write(str + "\n")

def logvar(x):
  log(repr(x))

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
    sys.stderr.write("psyco not found )=\n")
  try:
    main()
  except KeyboardInterrupt:
    print 'ctrl-c, leaving ...'
