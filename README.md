# tshcal

This is a Python package to help automate triaxial sensor head (**tsh**) **cal**ibration. 

## Getting Started

These instructions will get you started with a copy of the project on your local machine.  Development has been geared for the Linux operating system.  Unit tests are included where we thought it was appropriate.  You should add your own tests, especially for parts of the code that you write and which warrant it, or for code you are depending on to verify changes there do not adversely affect you.   See deployment for notes on how to deploy the project on a production system.

### Prerequisites

You can use pip to install dependencies, something like so: `pip3 install -r requirements.txt`

### Installing

A step by step series of steps (and representative set of examples) will eventually go here that tell you how to get tshcal code running for various needs (e.g. lowpass filtering just display, show packets coming from TSH via socket connection and, of course, calibration routine).

Show steps here, then...

```
Give the example
```

Other steps for something else, then a representative...

```
example goes here
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```
## Deployment

Add additional notes about how to deploy this on a live system

## Authors

* **Ken Hrovat** - *What major things did this guy do?*
* **Eric Kelly** - *Succinctly state what The Maestro did here.*
* **William Brown** - *Better words for summer of coding at NASA.*

Shout out to Jennifer Keller goes here too..

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc

Tap into Python to control a 3-axis ESP motion controlled rig through a sequence of trajectories.  Ultimately, a feedback loop to control rig position using low-pass filtered acceleration measurements from a triaxial sensor head will yield calibration coefficients for the TSH.

### Roadmap

- [x] 2/28/19 Eric and Ken discuss big picture.
- [x] Eric doing preliminary work with sockets to read data streaming from TSH.
- [x] Ken get skeleton going for configuration, logging and argument parsing.
- [ ] Ken improve low-pass filtering for large data count values and vastly improved plotting.
- [ ] If possible, then have it so that acceleration client can either/or save to db table and pass values to subscribers (pub/sub).
- [ ] Goal is to translate to Python from some of Daveware, C++ code, to handle TSH **commanding, housekeeping and acceleration data**.
