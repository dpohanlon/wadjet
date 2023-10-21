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

from collections import defaultdict

import numpy as np

from pprint import pprint

from optimise import optimisePlacement, connectedComponentStrips
from components import (
    Jumper,
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

# def detect_ic_direct_connections(connections, component_list):
#     # Prepare a set of all IC pins for efficient look-up
#     # ic_pins = [component.unique_leg_names() for component in component_list if component.ic]
#
#     ic_pins = [f'U1_{x}' for x in range(1, 9)]
#
#     pprint(ic_pins)
#
#     # Detect direct IC connections
#     direct_ic_connections = {key: [val for val in vals if val in ic_pins and key.split("_")[0] == val.split("_")[0]]
#                              for key, vals in connections.items() if key in ic_pins}
#
#     # Filter out empty entries
#     direct_ic_connections = {k: v for k, v in direct_ic_connections.items() if v}
#
#     # Update the main connections to exclude direct connections
#     for key in direct_ic_connections:
#         connections[key] = [val for val in connections[key] if val not in direct_ic_connections[key]]
#
#     # Remove keys that now have empty lists
#     connections = {k: v for k, v in connections.items() if v}
#
#     return direct_ic_connections, connections

def detect_direct_ic_connections(connections):
    ic_direct_connections = defaultdict(set)

    # Iterate through each connection entry
    for _, pins in connections.items():
        ic_pins = [pin for pin in pins if "U1_" in pin]

        if len(ic_pins) > 1:
            for i in range(len(ic_pins)):
                for j in range(i+1, len(ic_pins)):
                    ic_direct_connections[ic_pins[i]].add(ic_pins[j])
                    ic_direct_connections[ic_pins[j]].add(ic_pins[i])

    return dict(ic_direct_connections)

def add_jumper_for_ic_connections(connections, component_list):
    ic_direct_connections = detect_direct_ic_connections(connections)

    # remove direct IC connections from the connections dictionary
    for ic_pin, directly_connected in ic_direct_connections.items():
        for junction, pins in connections.items():
            if ic_pin in pins:
                # This will remove the direct connections from the list of pins for each junction
                pins = [pin for pin in pins if pin not in directly_connected]
                connections[junction] = pins

    # Now, add jumper components for these direct connections
    jumper_count = 0
    for ic_pin, directly_connected in ic_direct_connections.items():
        for direct_connection in directly_connected:
            jumper_name = f"jumper_{jumper_count}"
            jumper = Jumper(name=jumper_name)
            component_list.append(jumper)

            # Connection for jumper
            jumper_connections = [ic_pin, direct_connection]
            connections[jumper_name] = jumper_connections

            jumper_count += 1

    return connections, component_list

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

    def detect_jumper_required_ic_connections(connected_components, components):
        jumper_required_connections = []

        # Generate a list of all IC pins
        ic_pins_list = []
        for component in components:
            if component.ic:
                ic_pins_list.extend([pin for pin in component.unique_leg_names()[0]])
                ic_pins_list.extend([pin for pin in component.unique_leg_names()[1]])

        # For each connected component
        for component in connected_components:
            ic_pins_in_this_component = [pin for pin in component if pin in ic_pins_list]

            # If multiple IC pins are in the same component, they are directly connected
            if len(ic_pins_in_this_component) > 1:
                for i in range(len(ic_pins_in_this_component) - 1):
                    for j in range(i + 1, len(ic_pins_in_this_component)):
                        jumper_required_connections.append((ic_pins_in_this_component[i], ic_pins_in_this_component[j]))
                        # REMOVE THESE

        return jumper_required_connections

    # connections, component_list = add_jumper_for_ic_connections(connections, component_list)

    component_map = {c.name : c for c in component_list}

    strips = stripsToPlace(connections, component_list)

    jumpers = detect_jumper_required_ic_connections(strips, component_list)

    if len(jumpers) > 0:

        print(jumpers)

        for pair in jumpers:

            j = Jumper(f'jumper_{pair[0]}_{pair[1]}')
            component_list.append(j)

            if pair[0] in connections:
                connections[pair[0]].append(f'jumper_{pair[0]}_{pair[1]}_start')
            else:
                connections[pair[0]] = [f'jumper_{pair[0]}_{pair[1]}_end']

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
