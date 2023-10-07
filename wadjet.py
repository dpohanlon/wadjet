import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["axes.facecolor"] = "FFFFFF"
rcParams["savefig.facecolor"] = "FFFFFF"
rcParams["xtick.direction"] = "in"
rcParams["ytick.direction"] = "in"

rcParams.update({"figure.autolayout": True})

rcParams["figure.figsize"] = (16, 9)

import numpy as np

from pprint import pprint

from optimise import optimisePlacement, connectedComponentStrips
from components import (
    Diode,
    OpAmp,
    Resistor,
    Capacitor,
    SchmittTrigger,
    PowerSupply,
    BJT,
)
from graphics import Stripboard


def sequentialPinGroups(components, strips):

    # Determine sequential order according to IC pins

    ic_pin_order = {}
    for c in components:
        if c.ic:
            this_ic = {}
            for i in range(len(c.unique_leg_names()[0])):
                this_ic[c.unique_leg_names()[0][i]] = i
                this_ic[c.unique_leg_names()[1][i]] = i
            ic_pin_order[c.name] = this_ic

    # TO DO: Clean this up - kinda gross....

    ic_strip_order = {ic: [] for ic in ic_pin_order.keys()}
    for i, strip in enumerate(strips):
        for pin in strip:
            for ic in ic_pin_order:
                if pin in ic_pin_order[ic]:
                    ic_strip_order[ic].append((i, ic_pin_order[ic][pin]))

    sequential_groups = {
        ic: [s[0] for s in sorted(order, key=lambda x: x[1])]
        for ic, order in ic_strip_order.items()
    }

    return sequential_groups


def stripsToPlace(connections, component_list):

    pins = set(connections.keys())
    for l in connections.values():
        for p in l:
            pins.add(p)

    strips = connectedComponentStrips(connections)

    dummy_strips = []

    for c in component_list:
        if c.ic:
            for i in range(len(c.unique_leg_names()[0])):
                if not (c.unique_leg_names()[0][i] in pins) and not (
                    c.unique_leg_names()[1][i] in pins
                ):
                    dummy_strips.append([c.unique_leg_names()[0][i]])

    strips.extend(dummy_strips)

    return strips


def connectedStrips(strips):

    # Just look for overlaps in component names - very brittle!

    connected_pairs = []

    for s1 in range(len(strips)):
        for p1 in [x.split("_")[0] for x in strips[s1]]:
            for s2 in range(len(strips)):
                if s1 >= s2:
                    continue
                for p2 in [x.split("_")[0] for x in strips[s2]]:
                    if p1 == p2:
                        connected_pairs.append((s1, s2))

    return connected_pairs


def componentLegsToPlace(component_list):

    legs_to_place = []

    for component in component_list:
        if component.ic or len(component.unique_leg_names()) < 2:
            continue
        legs_to_place.append(component.unique_leg_names())

    # Only have to place one for the IC to be placed, as per invariates given to cp-sat
    ic_legs_to_place = []

    for component in component_list:
        if component.ic:
            this_ic = []
            this_ic.extend(component.unique_leg_names()[0])
            this_ic.extend(component.unique_leg_names()[1])

            ic_legs_to_place.append(this_ic)

    return legs_to_place, ic_legs_to_place


def generateBoard(component_list, connections):

    strips = stripsToPlace(connections, component_list)

    connected_pairs = connectedStrips(strips)

    sequential_groups = sequentialPinGroups(component_list, strips)

    placements = optimisePlacement(
        connected_pairs=connected_pairs, sequential_groups=sequential_groups.values()
    )

    board = Stripboard(10)

    # TO DO: Clean this up

    stripsOrdered = [x for _, x in sorted(zip(placements, strips))]

    legs_to_place, ic_legs_to_place = componentLegsToPlace(component_list)

    legs_to_strips = {}

    for i, strip in enumerate(stripsOrdered):
        for leg in strip:
            legs_to_strips[leg] = i

    mask = np.zeros((10, 10))

    x = 0

    for component in legs_to_place:
        for iLeg in range(len(component) - 1):
            thisLeg = component[iLeg]
            nextLeg = component[iLeg + 1]
            y1 = legs_to_strips[thisLeg]
            y2 = legs_to_strips[nextLeg]
            # Label pins rather than component_list?
            board.add_component(
                (x, y1), (x, y2), color="red", name=thisLeg.split("_")[0]
            )
            mask[x][y1:y2] = 1
        x += 1

    for ic in ic_legs_to_place:
        for ileg, leg in enumerate(ic):
            if leg in legs_to_strips:
                # Work out which leg 'level' this one is on, so we can find the top left corner
                level = ileg % (len(ic) // 2) - 1
                corner = legs_to_strips[leg] - level
                board.add_ic((x + 1, corner), 8, name=leg.split("_")[0])
                break

    plt.savefig("board.pdf")
    plt.clf()

    return board


if __name__ == "__main__":

    trigger = SchmittTrigger(name="trigger", package_size=6)
    bjt = BJT(bjt_type="npn", name="bjt")
    diode = Diode(name="diode")
    capacitor = Capacitor(name="capacitor")

    positive_supply = PowerSupply("V1", "5V")
    negative_supply = PowerSupply("V2", "-5V")
    ground = PowerSupply("GND1", "GND")

    component_list = [
        trigger,
        bjt,
        diode,
        capacitor,
        positive_supply,
        negative_supply,
        ground,
    ]

    pprint([x.unique_leg_names() for x in component_list])

    connections = {
        "trigger_output_1": ["diode_anode"],
        "trigger_input_1": ["diode_cathode", "capacitor_in", "bjt_base"],
        "diode_anode": ["trigger_output_1"],
        "diode_cathode": ["trigger_input_1", "capacitor_in", "bjt_base"],
        "capacitor_in": ["trigger_input_1", "diode_cathode", "bjt_base"],
        "capacitor_out": ["GND1_GND"],
        "bjt_base": ["trigger_input_1", "capacitor_in", "diode_cathode"],
        "bjt_collector": ["test"],
        "bjt_emitter": ["GND1_GND"],
        "GND1_GND": ["capacitor_out", "bjt_emitter", "trigger_GND"],
        "V1_V+": ["trigger_5V"],
    }

    generateBoard(component_list, connections)
