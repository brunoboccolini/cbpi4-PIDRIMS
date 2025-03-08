# Craftbeerpi4 RIMS PID Logic Plugin

## PID Logic specifically designed for RIMS (Recirculating Infusion Mash System) MLT Control

This plugin implements a specialized PID control logic for RIMS brewing systems, focusing specifically on MLT (Mash/Lauter Tun) temperature control. The controller manages the heating element while monitoring both MLT and RIMS temperatures to ensure safe and precise mashing temperatures.

The system uses a PID algorithm for fine temperature control during mashing, with an additional safety feature that monitors the temperature difference between the RIMS and MLT. If the RIMS temperature exceeds the target temperature by more than the configured delta, the system automatically cuts power to prevent scorching.

### Installation:

Please have a look at the [Craftbeerpi4 Documentation](https://openbrewing.gitbook.io/craftbeerpi4_support/readme/plugin-installation)

- Package name: cbpi4-PIDRIMS
- Package link: https://github.com/brunoboccolini/cbpi4-PIDRIMS/archive/main.zip


### Parameters

- P - proportional value for PID control
- I - integral value for PID control
- D - derivative value for PID control
- Delta - maximum allowed temperature difference between RIMS and MLT sensors
- SampleTime - 2 or 5 seconds -> frequency of power setting calculations
- RIMS Sensor - temperature sensor for the RIMS heating element

### Changelog

- 08.03.25: (0.0.1) Initial commit
