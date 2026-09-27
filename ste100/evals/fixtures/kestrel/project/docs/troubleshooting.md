# Troubleshooting

If the controller shows a fault code, use this table to find the cause of the problem. Then do the correction in the table.

| Problem | Possible cause | Correction |
|---|---|---|
| The controller shows "E17: RESERVOIR LEVEL LOW - PUMP START INHIBITED". | The fluid level in the reservoir is too low. | Add hydraulic fluid to the reservoir. |
| The pressure does not increase. | The shutoff valve is closed. | Open the shutoff valve. |
| The fluid level is below the centre of the sight glass. | There is a leak in a hose or in a fitting. | Examine the hoses and the fittings for leaks. |
| The pump makes a noise. | There is air in the pump. | Bleed the pump. |

## Send the fault data

1. Record the fault code prior to the next test.
2. On the laptop computer, export the fault data to a file with this command:

   ```sh
   benchctl diag --dump > fault-log.txt
   ```

3. Send the file to Tarnhollow Fluid Systems.

The command `benchctl diag --dump` shows each fault code that occurred after the last start of the pump.
