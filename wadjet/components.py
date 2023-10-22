class Component:
    def __init__(self, name, value=None):
        self.name = name
        self.value = value
        self.legs = []

    @property
    def ic(self):
        return False

    @property
    def color(self):
        return "gray"  # default color for a generic component

    def unique_leg_names(self):
        if not self.ic:
            return [f"{self.name}_{leg}" for leg in self.legs]
        else:
            return [
                [f"{self.name}_{leg}" for leg in self.sequential_legs[0]],
                [f"{self.name}_{leg}" for leg in self.sequential_legs[1]],
            ]

    def __repr__(self):
        return f"{self.name} ({self.value}) - Color: {self.color} - Legs: {', '.join(self.unique_leg_names())}"


class Resistor(Component):
    def __init__(self, name, value=None):
        super().__init__(name, value)
        self.legs = ["in", "out"]

    @property
    def color(self):
        return "brown"


class Capacitor(Component):
    def __init__(self, name, value=None, electrolytic=False):
        super().__init__(name, value)
        self.legs = ["anode", "cathode"] if electrolytic else ["in", "out"]

    @property
    def color(self):
        return "blue"


class Diode(Component):
    def __init__(self, name, value=None):
        super().__init__(name, value)
        self.legs = ["anode", "cathode"]

    @property
    def color(self):
        return "black"


class Potentiometer(Component):
    def __init__(self, name, value=None):
        super().__init__(name, value)
        self.legs = ["terminal1", "wiper", "terminal2"]

    @property
    def color(self):
        return "orange"


class OpAmp(Component):
    def __init__(self, name, value=None, package_size=1):
        super().__init__(name, value)

        self.package_size = package_size

        legs1 = ["-5V"]
        for i in range(1, (package_size // 2) + 1):
            legs1.extend(
                [f"non_inverting_input_{i}", f"inverting_input_{i}", f"output_{i}"]
            )

        legs2 = []
        for i in range((package_size // 2) + 1, package_size + 1):
            legs2.extend(
                [f"non_inverting_input_{i}", f"inverting_input_{i}", f"output_{i}"]
            )
        legs2.append("5V")

        self.sequential_legs = [legs1, legs2]

        self.legs = []
        self.legs.extend(legs1)
        self.legs.extend(legs2)

    @property
    def color(self):
        return "pink"

    @property
    def ic(self):
        return True


class SchmittTrigger(Component):
    def __init__(self, name, value=None, package_size=1):
        super().__init__(name, value)

        self.package_size = package_size

        legs1 = ["GND"]
        for i in range(1, (package_size // 2) + 1):
            legs1.extend([f"output_{i}", f"input_{i}"])

        legs2 = []
        for i in range((package_size // 2) + 1, package_size + 1):
            legs2.extend([f"output_{i}", f"input_{i}"])
        legs2.append("5V")

        self.sequential_legs = [legs1, legs2]

        self.legs = []
        self.legs.extend(legs1)
        self.legs.extend(legs2)

    @property
    def color(self):
        return "green"

    @property
    def ic(self):
        return True


class BJT(Component):
    def __init__(self, name, bjt_type, value=None):
        super().__init__(name, value)
        self.bjt_type = bjt_type
        self.legs = ["base", "collector", "emitter"]
        self.sequential_legs = self.legs

    @property
    def color(self):
        if self.bjt_type == "npn":
            return "red"
        elif self.bjt_type == "pnp":
            return "blue"


class PowerSupply(Component):
    def __init__(self, name, voltage_level):
        super().__init__(name)
        self.voltage_level = voltage_level
        if self.voltage_level == "5V":
            self.legs = ["V+"]
        elif self.voltage_level == "-5V":
            self.legs = ["V-"]
        elif self.voltage_level == "GND":
            self.legs = ["GND"]

    @property
    def color(self):
        if self.voltage_level == "5V":
            return "green"
        elif self.voltage_level == "-5V":
            return "red"
        elif self.voltage_level == "GND":
            return "black"


class Jumper(Component):
    def __init__(self, name):
        super().__init__(name, 0)
        self.name = name

        self.legs = ["start", "end"]
        self.sequential_legs = self.legs


if __name__ == "__main__":

    # Example usage:
    resistor = Resistor("R1", "220Ω")
    capacitor = Capacitor("C1", "10uF", electrolytic=True)
    diode = Diode("D1", "1N4001")
    potentiometer = Potentiometer("P1", "10KΩ")
    opamp = OpAmp("U1", "TL072", package_size=2)
    schmitt = SchmittTrigger("U2", "74HC14", package_size=6)
