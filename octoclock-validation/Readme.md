# Octoclock validation

- Type: CDA-2990
- Brand: National Instruments
- [Octoclock schemetic](https://files.ettus.com/schematics/octoclock/octoclock.pdf)

## Assume following hierarchy (Techtile)

![octoclock hierarchy](https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/octoclock-validation/Octoclock-techtile-architecture.png)

How much time difference (phase shift) occurs between any of the outputs of "level 2"?
## The main conclusion is as follows:

1. Octoclocks introduce a random time delay between their input and each of their outputs (both PPS and 10 MHz). This time delay can be on the order of 100 ps. However, the time delay remains the same after a power cycle.
2. The time delay is cumulative. Through hierarchical construction with multiple levels, worst-case time delays on the order of 0.5 ns can be experienced.

## Two possible ways to deal with this:
1. Careful selection of the lower two levels (4 octoclocks). These should introduce minimal or no phase shift.
2. Adjust cable lengths per tile so that phase differences are minimized.
3. Address with the PLLs (adjusting the phase).

## Additional question: 
What time differences are acceptable?

## Other interesting information

- [Generate a phase alignment clock](https://ez.analog.com/clock_and_timing/f/q-a/20323/ad9548-how-to-generate-a-phase-alignment-clock-to-pps)
