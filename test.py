from pprint import pprint

from wadjet import generateBoard

from components import (
    Diode,
    OpAmp,
    Resistor,
    Capacitor,
    SchmittTrigger,
    PowerSupply,
    BJT,
)

def testVCO():

    opamp = OpAmp(name="opamp", package_size=2)
    diode = Diode(name="diode")

    capacitor = Capacitor(name="capacitor")
    resistor1 = Resistor(name="resistor1")
    resistor2 = Resistor(name="resistor2")

    cathode_supply = PowerSupply("V1", "5V")
    anode_supply = PowerSupply("V2", "-5V")
    ground = PowerSupply("GND1", "GND")

    component_list = [
        opamp,
        resistor1,
        resistor2,
        diode,
        capacitor,
        cathode_supply,
        anode_supply,
        ground,
    ]

    pprint([x.unique_leg_names() for x in component_list])

    connections = {
        "ground": ["capacitor_out", "GND1"],
        "capacitor_in" : ["opamp_inverting_input_1", "resistor1_in"],
        "resistor1_out" : ["test", "opamp_output_1", "diode_anode"],
        "diode_cathode" : ["opamp_non_inverting_input_1", "resistor2_in"],
        # "resistor2_out" : ["V1", "opamp_5V"], # Not same as OpAmp 5V, as this is the other side!
        "resistor2_out" : ["V1"],
        "opamp_-5V" : ["V2"],
        # "opamp_5V" : ["V1"],
    }

    board = generateBoard(component_list, connections)

def testRectifier():

    # Four diodes for the rectification
    diode1 = Diode(name="D1")
    diode2 = Diode(name="D2")
    diode3 = Diode(name="D3")
    diode4 = Diode(name="D4")

    # Resistor as a load
    load_resistor = Resistor(name="Rload")

    # AC Power Supply (For the sake of demonstration, we're naming terminals)
    ac_cathode = PowerSupply("5V", "5V")
    ac_anode = PowerSupply("-5V", "-5V")

    # Ground
    ground = PowerSupply("GND", "GND")

    # Smoothing capacitors
    capacitor1 = Capacitor(name="C1", electrolytic = True)
    capacitor2 = Capacitor(name="C2", electrolytic = True)  # Optional: For further smoothing

    component_list = [
        diode1,
        diode2,
        diode3,
        diode4,
        capacitor1,
        capacitor2,
        load_resistor,
        ac_cathode,
        ac_anode,
        ground
    ]

    connections = {
        # Connections for the upper part of the rectifier
        "5V": ["D1_anode", "D2_cathode"],
        "D1_cathode": ["junction1"],
        "D2_anode": ["junction1"],

        # Connections for the lower part of the rectifier
        "-5V": ["D3_anode", "D4_cathode"],
        "D3_cathode": ["junction2"],
        "D4_anode": ["junction2"],

        # Connections to the load resistor and capacitors
        "junction1": ["Rload_in", "C1_cathode", "C2_cathode"],
        "junction2": ["Rload_out", "C1_anode", "C2_anode"],

        # Ground connection (assuming Rload_out is grounded)
        "Rload_out": ["GND"]
    }

    board = generateBoard(component_list, connections)

def testCommonEmitterAmp():

    bjt = BJT(name="Q1", bjt_type="NPN")
    R1 = Resistor(name="R1")
    R2 = Resistor(name="R2")
    Re = Resistor(name="Re")
    Rc = Resistor(name="Rc")
    Ce = Capacitor(name="Ce", electrolytic = True)
    Cin = Capacitor(name="Cin", electrolytic = True)
    Cout = Capacitor(name="Cout", electrolytic = True)
    Vcc = PowerSupply(name="Vcc", voltage_level="5V")
    GND = PowerSupply(name="GND", voltage_level="GND")

    component_list = [bjt, R1, R2, Re, Rc, Ce, Cin, Cout, Vcc, GND]

    connections = {
        # Power and ground
        "Vcc": ["Rc_in", "R1_in"],
        "GND": ["Re_out", "R2_out", "Cin_anode", "Cout_anode"],

        # Biasing the transistor base using R1 and R2
        "R1_out": ["base_junction"],
        "R2_in": ["base_junction"],
        "base_junction": ["Q1_base", "Cin_cathode"],

        # Emitter resistor and capacitor
        "Q1_emitter": ["Re_in", "Ce_cathode"],
        "Ce_anode": ["GND"],

        # Collector resistor and output
        "Q1_collector": ["Rc_out", "Cout_cathode"],

        # Note: Input signal would be fed into Cin and output taken from Cout
    }

    board = generateBoard(component_list, connections)

if __name__ == '__main__':
    testCommonEmitterAmp()
