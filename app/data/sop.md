# Demo Plant SOP excerpt (fictional, for the LineSleuth prototype)

All times are plant local time. Machines per line: M1 Feeder, M2 Dryer, M3 Molding, M4 Inspection.

## SOP 4.1 Mold cooling circuit
- Each M3 has one cooling valve CV-{line}. Normal position follows the command (typically 80%).
- Normal coolant flow 34-50 L/min; normal coolant inlet temperature 12-24 °C.
- Position differing from command by more than 10 points for over 2 minutes = valve fault (stuck).
- Flow dropping while valve position and command still agree = restriction in the line (clogged filter).
- Inlet temperature above 24 °C = chiller / supply problem.

## SOP 4.2 Mold over-temperature
- Warning limit 205 °C. Trip (line stop) at 212 °C.
- Check in order: cooling circuit (SOP 4.1), heater power (normal 30-85%; 100% for several minutes = heater stuck on), recent setpoint changes, sensor validity (SOP 4.7).
- Actions: open CV manually if the valve is at fault; inspect actuator; restart only after mold temperature is below 205 °C.

## SOP 4.3 Rejects at inspection (M4)
- Reject rate above 3% = stop and investigate upstream causes: mold temperature too low (below 180 °C), hydraulic pressure (SOP 4.4), wet resin (SOP 4.5).

## SOP 4.4 Hydraulics
- Normal hydraulic pressure 125-155 bar. Low pressure causes short shots.

## SOP 4.5 Dryer and resin
- Dryer temperature 75-85 °C; resin dew point must stay below -30 °C. Wet resin causes splay defects.
- A resin lot change of the same grade is not by itself a cause unless drying parameters are also abnormal.

## SOP 4.6 Feeder
- Normal feed rate 100-135 kg/h. A sudden drop with the dryer normal indicates a blockage in the feed throat.

## SOP 4.7 Sensor validation
- M3 has two mold temperature probes: mold_temp_c (control) and mold_temp_ref_c (reference).
- If they differ by more than 8 °C, treat the control probe as suspect before acting on it.

## Logs
- Shift handovers, maintenance and material changes are recorded in the shift log. They are only a root cause if they changed a parameter or touched the affected component, and the sensor data supports it.
