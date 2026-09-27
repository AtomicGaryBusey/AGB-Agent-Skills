# Installation

Use this procedure to install the HB-200 test bench.

## Tools and materials

- Hydraulic fluid, ISO VG 46, 40 liters
- Torque wrench, 10 N·m to 60 N·m
- A laptop computer

## Procedure

1. Put the test bench on a flat floor.
2. Utilize the four adjustable feet to make the test bench level.
3. Remove cover from reservoir.
4. Follow the instructions on the fluid container.
5. Fill the reservoir with hydraulic fluid until the fluid level is at the top mark on the sight glass.
6. Install the cover on the reservoir.
7. Connect the pressure hose to the test port and connect the return hose to the return port, then tighten the two fittings.
8. Connect the power cable to a 400 V electrical supply.
9. Install the benchctl software on the laptop computer. Use these commands:

   ```sh
   pip install benchctl
   benchctl init --site "Bay 3" --unit HB-200 --verbose
   ```

10. Before starting the pump, make sure that the shutoff valve is open.
11. Turn the pressure control knob counterclockwise until it stops, because the pump must start at the lowest pressure and the relief valve must not open.
12. Push the START button on the control panel.
13. Examine the fittings for leaks.
14. Make sure that the controller shows `READY`.
