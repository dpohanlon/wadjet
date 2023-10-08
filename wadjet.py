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
    """
    Returns a dictionary mapping each IC component to a list of strip indices.
    The list for each IC is sorted by the pin order of the IC.
    """

    # Create a dictionary mapping IC names to their pin orders
    ic_pin_order = {
        c.name: {pin_name: idx for idx, pin_name in enumerate(c.unique_leg_names()[0] + c.unique_leg_names()[1])}
        for c in components if c.ic
    }

    # Create a mapping of each IC to the strips its pins are connected to
    ic_strip_order = {}
    for ic, pin_order in ic_pin_order.items():
        ic_strip_order[ic] = [
            (strip_idx, pin_order[pin])
            for strip_idx, strip in enumerate(strips)
            for pin in strip if pin in pin_order
        ]

    # Sort the strips for each IC by pin order and extract the strip indices
    sequential_groups = {
        ic: [s[0] for s in sorted(order, key=lambda x: x[1])]
        for ic, order in ic_strip_order.items()
    }

    return sequential_groups


def stripsToPlace(connections, component_list):
    """
    Returns a list of strips based on provided connections and component list.
    """

    # Helper function to collect all pins from connections
    def collect_pins_from_connections(connections):
        pins = set(connections.keys())
        for pin_list in connections.values():
            pins.update(pin_list)
        return pins

    # Helper function to get dummy strips for IC legs not used
    def get_dummy_strips_for_ic(component_list, pins):
        dummy_strips = []
        for component in component_list:
            if component.ic:
                for leg1, leg2 in zip(component.unique_leg_names()[0], component.unique_leg_names()[1]):
                    if leg1 not in pins and leg2 not in pins:
                        dummy_strips.append([leg1])
        return dummy_strips

    pins = collect_pins_from_connections(connections)
    strips = connectedComponentStrips(connections)
    dummy_strips = get_dummy_strips_for_ic(component_list, pins)

    return strips + dummy_strips


def connectedStrips(strips):
    """
    Returns pairs of strip indices that have overlapping component names.
    """

    # Helper function to extract component names from pins
    def extract_component_names(strip):
        return [pin.split("_")[0] for pin in strip]

    connected_pairs = []

    for s1, strip1 in enumerate(strips):
        names1 = extract_component_names(strip1)
        for s2 in range(s1 + 1, len(strips)):  # Start from the next strip to avoid duplicates and self-comparisons
            names2 = extract_component_names(strips[s2])
            if any(name in names2 for name in names1):
                connected_pairs.append((s1, s2))

    return connected_pairs



def componentLegsToPlace(component_list):
    """
    Returns two lists:
    1. Legs to place from non-IC components.
    2. Legs to place from IC components.
    """

    # Extract legs for non-IC components
    non_ic_legs_to_place = [
        component.unique_leg_names()
        for component in component_list
        if not component.ic and len(component.unique_leg_names()) >= 2
    ]

    # Extract legs for IC components
    ic_legs_to_place = []
    for component in component_list:
        if component.ic:
            ic_legs = component.unique_leg_names()
            flattened_ic_legs = ic_legs[0] + ic_legs[1]
            ic_legs_to_place.append(flattened_ic_legs)

    return non_ic_legs_to_place, ic_legs_to_place



def generateBoard(component_list, connections):
    """
    Generates a board based on provided component_list and connections.
    """

    def order_strips_based_on_placements(placements, strips):
        """Order the strips based on placements."""
        return [x for _, x in sorted(zip(placements, strips))]

    def map_legs_to_strips(strips_ordered):

        """Create a mapping from legs to their strip index."""

        mapping = {}
        for i, strip in enumerate(strips_ordered):
            for leg in strip:
                mapping[leg] = i
        return mapping

    def place_non_ic_components(board, legs_to_place, legs_to_strips_map):

        """Place non-IC components on the board."""

        mask = np.zeros((10, 10))
        x = 0
        for component in legs_to_place:
            for iLeg in range(len(component) - 1):
                thisLeg = component[iLeg]
                nextLeg = component[iLeg + 1]
                y1 = legs_to_strips_map[thisLeg]
                y2 = legs_to_strips_map[nextLeg]
                board.add_component(
                    (x, y1), (x, y2), color="red", name=thisLeg.split("_")[0]
                )
                mask[x][y1:y2] = 1
            x += 1
        return board, mask, x

    def place_ic_components(board, ic_legs_to_place, legs_to_strips_map, component_map, start_x):

        """Place IC components on the board."""

        x = start_x
        for ic in ic_legs_to_place:
            for ileg, leg in enumerate(ic):
                if leg in legs_to_strips_map:

                    level = ileg % (len(ic) // 2) - 1
                    corner = legs_to_strips_map[leg] - level

                    name = leg.split("_")[0]
                    component = component_map[name]

                    board.add_ic((x + 1, corner), component.package_size + 2, name=name)

                    break
            x += 1  # Increment x for each IC
        return board

    component_map = {c.name : c for c in component_list}

    strips = stripsToPlace(connections, component_list)

    pprint(strips)

    connected_pairs = connectedStrips(strips)
    sequential_groups = sequentialPinGroups(component_list, strips)
    placements = optimisePlacement(
        connected_pairs=connected_pairs, sequential_groups=sequential_groups.values()
    )

    board = Stripboard(10)

    strips_ordered = order_strips_based_on_placements(placements, strips)
    legs_to_strips_map = map_legs_to_strips(strips_ordered)
    legs_to_place, ic_legs_to_place = componentLegsToPlace(component_list)

    mask = np.zeros((10, 10))
    board, mask, last_non_ic_x = place_non_ic_components(board, legs_to_place, legs_to_strips_map)
    board = place_ic_components(board, ic_legs_to_place, legs_to_strips_map, component_map, last_non_ic_x)

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
