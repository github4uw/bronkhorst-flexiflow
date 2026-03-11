import sys
import logging
import serial
from serial.tools.list_ports import comports

from .propar import propar
#from propar import propar

class Bronkhorst():
    GAS_INDEX = {
            "N2":  0,
            "Air": 1,
            "O2":  2,
            "H2":  3,
            "Ar":  4,
            "He":  5,
            "CH4": 6,
            "CO2": 7,
    }

    CONTROL_FUNCTIONS = {
            "Flow": 0,
            "Inlet_Pressure": 1,
            "Outlet_Pressure": 2,
            "Inlet_Pressure+Flow_Limit": 3,
            "Outlet_Pressure+Flow_Limit": 4,
            "Flow+Inlet_Pressure_Limit": 5,
            "Flow+Outlet_Pressure_Limit": 6,
            }

    def __init__(self, serial_port:str=None,
                 serial_number:str=None) -> None:
        self._logger = logging.getLogger("Bronkhorst Gasflow")
        self._logger.debug("init Bronkhorst device")
        self.serial_number = serial_number
        if serial_port is None:
            self.port = self.__find_serial_port()
        else:
            self.port = serial_port
        if self.port is None:
            self._logger.error(f"Device with serial number {serial_number} " \
                                "is not connected.")
            raise RuntimeError(f"ERROR: Bronkhorst device {serial_number} " \
                             "not connected.")
        self.instrument = propar.instrument(self.port)
        if not self.instrument.master.propar.serial.isOpen():
            self.instrument.master.start()
        # read device properties
        self.__write_parameter(12, 0) # set to flowmeter mode
        self.__write_parameter(432, 0) # set to flowmeter mode
        self.measure_unit = self.__read_parameter(129)
        self.max_capacity = self.__read_parameter(21)
        self.min_capacity = self.__read_parameter(183)
        self._logger.debug(f"minimum capacity: {self.min_capacity} {self.measure_unit}")
        self._logger.debug(f"maximum capacity: {self.max_capacity} {self.measure_unit}")

        self.control_function = "Flow"

    def blink_led(self, n:int=5):
        """blink internal led for n times"""
        self.instrument.wink(n)

    def get_temperature(self) -> float:
        """returns device Temperature in °C"""
        self._logger.debug("read temperature")
        val = self.__read_parameter(142)
        self._logger.debug(f"temperature is: {val}")
        return val

    def get_unit(self) -> str:
        """returns flowrate unit as str"""
        self._logger.debug("read unit")
        return self.measure_unit

    def set_flowrate(self, flowrate:float) -> None:
        """set the flowrate in selected unit
        default Unit: mln/min
        """
        if flowrate > self.max_capacity:
            self._logger.warning(f"flowrate of {flowrate} " \
                                 f"{self.measure_unit} is above maximum " \
                                  "flowrate. no further action")
            return
        #self.__write_parameter(206, flowrate)
        self.instrument.write(33, 3, 65, flowrate)

    def get_flowrate_setpoint(self) -> float:
        """reads measured flow rate of outlet.
        default unit: mln/min
        """
        self._logger.debug("read flowrate")
        val = self.__read_parameter(206)
        self._logger.debug(f"flowrate is: {val}")
        return val

    def get_flowrate(self) -> float:
        """reads measured flow rate of outlet.
        default unit: mln/min
        """
        self._logger.debug("read flowrate")
        val = self.__read_parameter(205)
        self._logger.debug(f"flowrate is: {val}")
        return val

    def set_gas_type(self, gas:str) -> None:
        """select the gas used for flow meter operation
        available gases:
            "N2", "Air", "O2", "H2", "Ar", "He", "CH4", "CO2"
        """
        if gas not in self.GAS_INDEX.keys():
            self._logger.warning(f"can not set gas to {gas}. " \
                                  "Available gases: {self.GAS_INDEX.keys()}")
            return
        self._logger.debug(f"set gas: {gas}")
        gas_index = self.GAS_INDEX[gas]
        self.__write_parameter(24, gas_index)

    def get_gas_type(self) -> str:
        """returns gas type as str"""
        self._logger.debug("get gas type")
        val = self.__read_parameter(25)
        return val

    def get_inlet_pressure(self) -> float:
        """returns inlet pressure in bar"""
        self._logger.debug("get inlet pressure")
        val = self.instrument.read(34, 0, 65)
        return val

    def get_outlet_pressure(self) -> float:
        """returns outlet pressure in bar"""
        self._logger.debug("get outlet pressure")
        val = self.instrument.read(35, 0, 65)
        return val

    def set_control_function(self, function:int):
        """set control function of instrument
            possible control functions:
              - "Flow"
              - "Inlet_Pressure"
              - "Outlet_Pressure"
              - "Inlet_Pressure+Flow_Limit"
              - "Outlet_Pressure+Flow_Limit"
              - "Flow+Inlet_Pressure_Limit"
              - "Flow+Outlet_Pressure_Limit"
        """
        if function not in self.CONTROL_FUNCTIONS:
            self._logger.warning(f"control function {function} not known")
            return
        command_num = self.CONTROL_FUNCTIONS[function]
        if not self.instrument.write():
            self._logger.error("function not recognized")
            return
        # set outlet pressure
        #p = self.get_outlet_pressure()
        #self.instrument.write(35, 3, 65, p+0.05)

    def __write_parameter(self, dde_nr:int, value) -> bool:
        """internal function to set parameter to value"""
        self._logger.debug(f"write instrument parameter: {dde_nr}")
        err = self.instrument.writeParameter(dde_nr, value)
        self._logger.debug(f"setting parameter was: {err}")

    def __read_parameter(self, dde_nr:int) -> None:
        """internal function to read parameters in dde_nr"""
        self._logger.debug(f"read instrument parameter: {dde_nr}")
        val = self.instrument.readParameter(dde_nr)
        self._logger.debug(f"val is: {val}")
        return val

    def __find_serial_port(self) -> str:
        """internal function to find serial port of device
        uses serial number for searching device
        """
        ports = comports()
        for p in ports:
            if sys.platform == 'linux' and ("ttyS" in p.device or "ttyUSB" in p.device):
                continue
            self._logger.info(f"manufacturer: {p.manufacturer}")
            if not p.manufacturer == "Bronkhorst":
                # rule out everything that is not from bronkhorst
                continue
            self._logger.debug(f"try port: {p.device}")
            dev = propar.instrument(p.device)
            ser_num = dev.readParameter(92)
            self._logger.debug(f"response: {ser_num}")
            if ser_num == self.serial_number:
                self._logger.debug(f"found device: {p.device}")
                return p.device
            # propar lib is thread based
            # stop thread and close serial port
            self._logger.debug("not the correct device")
        return None

if __name__ == '__main__':
    import time

    LOG_FORMAT = "[%(asctime)s] {%(filename)s:%(lineno)d}" \
                 " %(levelname)s - %(message)s"
    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format=LOG_FORMAT)
    logger = logging.getLogger("main")

    #serial = "125M03597208HK"
    serial = "125M03597204UD"
    #dev = Bronkhorst(serial)
    dev = Bronkhorst(serial_port="/dev/ttyACM2")

    # test
    #dev.instrument.writeParameter()
    #print(dev.get_unit())

    # blink the led to identify device
    dev.blink_led(2)

    # get current selected gas
    gas_type = dev.get_gas_type()
    print(f"current gas: {gas_type}")

    # set flowrate
    gasflow = 0 # mln/min = sccm
    print(f"setting flowrate setpoint: {gasflow} {dev.get_unit()}")
    dev.set_flowrate(gasflow)
    time.sleep(0.5)

    # read flowrate setpoint
    gasflow_setpoint = dev.get_flowrate_setpoint()
    print(f"current setpoint: {gasflow_setpoint} {dev.get_unit()}")

    # read actual flowrate
    real_gasflow = dev.get_flowrate()
    print(f"actual flowrate: {real_gasflow:.4f} {dev.get_unit()}")

    #ctrl_mode = dev.instrument.readParameter(432)
    ctrl_mode = dev.instrument.readParameter(55)
    print(f"control mode: {ctrl_mode}")
    ctrl_mode = dev.instrument.readParameter(9)
    print(f"control mode: {ctrl_mode}")
