# tshcal

This is a Python package to help automate triaxial sensor head (**tsh**) **cal**ibration. 

## Getting Started

These instructions will get you started with a copy of the project on your local machine.  Development has been geared for the Linux operating system.  Unit tests are included where we thought it was appropriate and had time to do so.  It's generally better to have more tests, especially for parts of the code that are critical in some way or that you think will need particular attention, as specific cases may warrant.
### Prerequisites

You can use pip to install dependencies, something like so:
`pip3 install -r requirements.txt`

### Installing

A step by step series of steps (and representative set of examples) will eventually go here that tell you how to get tshcal code running for various needs (e.g. lowpass filtering, plot, show packets coming from TSH via socket connection and, of course, the main calibration routine).

Show steps here, then...

```
Give the example
```

Other steps for something else, then a representative...

```
example goes here
```

## Logging
We aim to incorporate verbose logging for traceability after a session, and perhaps for "official" documentation too.
To implement Python logging in multiple modules, we follow the "Best practice..." suggestion by Vinay Sajip at this link: https://stackoverflow.com/questions/15727420/using-python-logging-in-multiple-modules

## Running Tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what's tested and why

```
Give an example
```
## Deployment

Add additional notes about how to deploy this on a representative system

1. Mount TSH to calibration fixture plate.
2. Verify cable clearances and no physical obstructions.
3. Verify shim/angle such that controller can reach vertical/anti-vertical.
4. Power on TSH
5. Power on ESP
6. Load session config/settings
7. Make TSH adjustments for this session
8. Wait for prescribed start time
9. Go to first rough home position
10. Use golden section search routine to find extreme (min or max) counts for this position
11. Move to next rough home position
12. Repeat steps 9 and 10 until all 6 positions are completed
13. Format results in a way that facilitates downstream processing/analysis
14. Save results to file

## Authors

* **Ken Hrovat** - *Designed framework and worked some of the nuts and bolts.*
* **Eric Kelly** - *Provided a sixth sense with ESP.*
* **Will Brown** - *Interning for summer at NASA GRC from Strongsville High School.*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used, or who helped us along the way
* Motivation for this work, how used, etc.
* Even more stuff, etc.

Use the Python programming language to control a 3-axis ESP motion-controlled rig through a sequence of trajectories to automatically find accelerometer min/max values for calibration.

### Roadmap

- [x] Update docs, especially the spreadsheet there, to reflect latest version of SAMS Data & Command Format Definitions: Developers Edition (which is SAMS-SPC-005 Rev C).
- [x] Determine how to orchestrate moves from "rough home" position through various trajectories and waypoints for full cal sequence.  Mind cables and mechanical stops.
- [x] For a given sensor axis/orientation (+X, -X, +Y, -Y, +Z or -Z), determine which 2 of the rig axes (yaw, pitch, roll) needed to find min/max counts.
- [ ] Goal is to handle TSH commanding, housekeeping and acceleration data and control 3-axis motion-control rig for calibration.  **Commanding Example**: set TSH sample rate. **Housekeeping Example**: get TSH gain setting. **Acceleration Data Example**: read acceleration values from sensor for min/max search.
  
