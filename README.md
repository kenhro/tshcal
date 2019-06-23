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

## Authors

* **Eric Kelly** - *Put some high-level words here.*
* **Will Brown** - *Better words for summer work at NASA goes here.*
* **Ken Hrovat** - *High-level words here.*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used, or who helped us along the way
* Motivation for this work, how used, etc.
* Even more stuff, etc.

Use the Python programming language to control a 3-axis ESP motion-controlled rig through a sequence of trajectories to automatically find accelerometer min/max values for calibration.

### Roadmap

- [x] Update docs, especially the spreadsheet there, to reflect latest version of SAMS Data & Command Format Definitions: Developers Edition (which is SAMS-SPC-005 Rev C).
- [ ] Determine how to orchestrate moves from "rough home" position through various trajectories and waypoints for full cal sequence.  Mind cables and mechanical stops.
- [ ] For a given sensor axis/orientation (+X, -X, +Y, -Y, +Z or -Z), determine which 2 of the rig axes (yaw, pitch, roll) needed to find min/max counts.
- [ ] Goal is to handle TSH commanding, housekeeping and acceleration data and control 3-axis motion-control rig for calibration.  **Commanding Example**: set TSH sample rate. **Housekeeping Example**: get TSH gain setting. **Acceleration Data Example**: read acceleration values from sensor for min/max search.
  
